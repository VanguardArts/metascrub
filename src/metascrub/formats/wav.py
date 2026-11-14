"""WAV adapter — binary RIFF chunk rewriting.

WAV stores metadata in a ``LIST``/``INFO`` chunk, and newer generators embed a
``C2PA`` provenance-manifest chunk. Neither is touched by generic ID3 tooling,
so this adapter parses and rewrites the chunk list directly.

Safety guarantees:
  * ``fmt `` / ``data`` and any unknown chunks are copied byte-for-byte;
  * audio is never transcoded;
  * writes are atomic (temp file + os.replace);
  * after writing, the audio chunks are re-hashed and compared against the
    original — a mismatch raises and the original file is left in place.
"""
from __future__ import annotations

import hashlib
import os
import struct
from typing import List, Optional, Tuple

from ..policy import Policy
from ..report import FileResult, TagEntry, preview
from .base import Derived, FormatAdapter

# Canonical display order for INFO fields written by clean().
_FIELD_ORDER = ["INAM", "IART", "IPRD", "ICRD", "IGNR", "ICOP", "IENG"]


def _parse_chunks(data: bytes) -> List[Tuple[bytes, bytes]]:
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("not a RIFF/WAVE file")
    chunks = []
    pos, end = 12, len(data)
    while pos + 8 <= end:
        cid = data[pos:pos + 4]
        size = struct.unpack_from("<I", data, pos + 4)[0]
        body = data[pos + 8: pos + 8 + size]
        chunks.append((cid, body))
        pos += 8 + size + (size & 1)
    return chunks


def _parse_info(body: bytes) -> List[Tuple[str, str]]:
    if body[:4] != b"INFO":
        return []
    out = []
    pos = 4
    while pos + 8 <= len(body):
        code = body[pos:pos + 4].decode("latin-1")
        size = struct.unpack_from("<I", body, pos + 4)[0]
        text = body[pos + 8: pos + 8 + size].rstrip(b"\x00").decode("utf-8", "replace")
        out.append((code, text))
        pos += 8 + size + (size & 1)
    return out


def _info_field(code: str, text: str) -> bytes:
    b = text.encode("utf-8") + b"\x00"
    if len(b) % 2:
        b += b"\x00"
    return code.encode("ascii") + struct.pack("<I", len(b)) + b


def _build_info(fields: List[Tuple[str, str]]) -> bytes:
    return b"INFO" + b"".join(_info_field(c, v) for c, v in fields)


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


class WAVAdapter(FormatAdapter):
    name = "wav"
    extensions = (".wav",)

    def inspect(self, path: str, relpath: str, policy: Policy) -> FileResult:
        result = FileResult(path=relpath, format=self.name)
        try:
            with open(path, "rb") as fh:
                chunks = _parse_chunks(fh.read())
        except Exception as exc:
            result.error = str(exc)
            return result
        for cid, body in chunks:
            if cid == b"LIST" and body[:4] == b"INFO":
                for code, text in _parse_info(body):
                    action = "strip" if code in policy.strip_riff_info else "keep"
                    result.entries.append(
                        TagEntry(f"INFO:{code}", preview(text), action, "tag")
                    )
            elif cid in (b"LIST",):
                result.entries.append(
                    TagEntry(f"chunk:{cid.decode('latin-1')}", f"{len(body)} bytes", "keep", "audio")
                )
            else:
                strip = cid.decode("latin-1").strip("\x00 ") in policy.strip_riff_chunks \
                    or cid.decode("latin-1") in policy.strip_riff_chunks
                action = "strip" if strip else "keep"
                kind = "provenance" if strip else "audio"
                result.entries.append(
                    TagEntry(f"chunk:{cid.decode('latin-1')}", f"{len(body)} bytes", action, kind)
                )
        return result

    def clean(self, path: str, relpath: str, policy: Policy,
              derived: Derived, dry_run: bool) -> FileResult:
        result = FileResult(path=relpath, format=self.name)
        try:
            with open(path, "rb") as fh:
                data = fh.read()
            chunks = _parse_chunks(data)
        except Exception as exc:
            result.error = str(exc)
            return result

        strip_chunks = {c.encode("ascii") for c in policy.strip_riff_chunks}
        strip_info = set(policy.strip_riff_info)

        # Credit fields to write (only those with a value).
        c = policy.credits
        credit_fields: List[Tuple[str, str]] = []
        if policy.titles.enabled and derived.title:
            credit_fields.append(("INAM", derived.title))
        if c.artist:
            credit_fields.append(("IART", c.artist))
        if derived.album:
            credit_fields.append(("IPRD", derived.album))
        if c.year:
            credit_fields.append(("ICRD", c.year))
        if derived.genre:
            credit_fields.append(("IGNR", derived.genre))
        if c.copyright:
            credit_fields.append(("ICOP", c.copyright))
        if c.composer:
            credit_fields.append(("IENG", c.composer))
        credit_codes = {code for code, _ in credit_fields}

        new_chunks: List[Tuple[bytes, bytes]] = []
        list_seen = False
        for cid, body in chunks:
            if cid in strip_chunks:
                result.entries.append(
                    TagEntry(f"chunk:{cid.decode('latin-1')}", f"{len(body)} bytes", "strip", "provenance")
                )
                continue
            if cid == b"LIST" and body[:4] == b"INFO":
                list_seen = True
                old = _parse_info(body)
                kept = []
                for code, text in old:
                    if code in strip_info:
                        result.entries.append(
                            TagEntry(f"INFO:{code}", preview(text), "strip", "tag")
                        )
                    elif code in credit_codes:
                        result.entries.append(
                            TagEntry(f"INFO:{code}", preview(text), "strip", "tag")
                        )
                    else:
                        kept.append((code, text))
                merged = self._merge(credit_fields, kept)
                for code, text in credit_fields:
                    result.entries.append(TagEntry(f"INFO:{code}", preview(text), "set", "tag"))
                if merged:
                    new_chunks.append((b"LIST", _build_info(merged)))
                continue
            new_chunks.append((cid, body))

        if not list_seen and credit_fields:
            merged = self._merge(credit_fields, [])
            for code, text in credit_fields:
                result.entries.append(TagEntry(f"INFO:{code}", preview(text), "set", "tag"))
            # Insert the LIST chunk right after fmt (fall back to the front).
            list_chunk = (b"LIST", _build_info(merged))
            inserted = False
            ordered: List[Tuple[bytes, bytes]] = []
            for cid, body in new_chunks:
                ordered.append((cid, body))
                if cid == b"fmt " and not inserted:
                    ordered.append(list_chunk)
                    inserted = True
            if not inserted:
                ordered.insert(0, list_chunk)
            new_chunks = ordered

        if dry_run:
            return result

        audio_before = {
            cid: _sha(body) for cid, body in chunks if cid in (b"fmt ", b"data")
        }
        blob = self._assemble(new_chunks)
        tmp = path + ".metascrub.tmp"
        with open(tmp, "wb") as fh:
            fh.write(blob)
        audio_after = {
            cid: _sha(body) for cid, body in _parse_chunks(blob) if cid in (b"fmt ", b"data")
        }
        if audio_before != audio_after:
            os.unlink(tmp)
            result.error = "audio chunk hash mismatch — rewrite aborted, original untouched"
            return result
        os.replace(tmp, path)
        return result

    @staticmethod
    def _merge(credit_fields: List[Tuple[str, str]],
               kept: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        ordered = sorted(
            credit_fields,
            key=lambda kv: _FIELD_ORDER.index(kv[0]) if kv[0] in _FIELD_ORDER else len(_FIELD_ORDER),
        )
        kept_codes = {code for code, _ in credit_fields}
        return ordered + [(c, v) for c, v in kept if c not in kept_codes]

    @staticmethod
    def _assemble(chunks: List[Tuple[bytes, bytes]]) -> bytes:
        out = bytearray(b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE")
        for cid, body in chunks:
            out += cid + struct.pack("<I", len(body)) + body
            if len(body) % 2:
                out += b"\x00"
        out[4:8] = struct.pack("<I", len(out) - 8)
        return bytes(out)
