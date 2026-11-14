"""MP3 adapter — ID3v2.4 via mutagen."""
from __future__ import annotations

from mutagen.id3 import (
    APIC,
    ID3,
    ID3NoHeaderError,
    TALB,
    TCOM,
    TCON,
    TCOP,
    TDRC,
    TIT2,
    TPE1,
    TPE2,
    TPUB,
)

from ..policy import Policy
from ..report import FileResult, TagEntry, preview
from .base import Derived, FormatAdapter


def _preview_frame(frame) -> str:
    if isinstance(frame, APIC):
        return f"{frame.mime} ({len(frame.data)} bytes)"
    url = getattr(frame, "url", None)
    if url:
        return preview(url)
    text = getattr(frame, "text", None)
    if isinstance(text, list):
        return preview("; ".join(str(t) for t in text))
    if text is not None:
        return preview(str(text))
    data = getattr(frame, "data", None)  # GEOB / PRIV payloads
    if data is not None:
        return f"{getattr(frame, 'mime', '?')} ({len(data)} bytes)"
    return preview(str(frame))


class MP3Adapter(FormatAdapter):
    name = "mp3"
    extensions = (".mp3",)

    def _load(self, path: str):
        try:
            return ID3(path)
        except ID3NoHeaderError:
            return ID3()

    def _is_strip(self, key: str, policy: Policy) -> bool:
        if key.startswith("APIC"):
            return policy.remove_cover_art
        return any(key.startswith(p) for p in policy.strip_id3_frames)

    def inspect(self, path: str, relpath: str, policy: Policy) -> FileResult:
        result = FileResult(path=relpath, format=self.name)
        try:
            tags = self._load(path)
        except Exception as exc:  # unreadable tag
            result.error = str(exc)
            return result
        for key in sorted(tags.keys()):
            action = "strip" if self._is_strip(key, policy) else "keep"
            result.entries.append(
                TagEntry(key=key, value=_preview_frame(tags[key]), action=action, kind="tag")
            )
        if not tags:
            result.entries.append(TagEntry("(no ID3 tag)", "", "keep", "tag"))
        return result

    def clean(self, path: str, relpath: str, policy: Policy,
              derived: Derived, dry_run: bool) -> FileResult:
        result = FileResult(path=relpath, format=self.name)
        try:
            tags = self._load(path)
        except Exception as exc:
            result.error = str(exc)
            return result

        # Frames we are about to set; existing ones are replaced.
        c = policy.credits
        to_set = [
            ("TPE1", TPE1, c.artist),
            ("TPE2", TPE2, c.album_artist or c.artist),
            ("TCOM", TCOM, c.composer),
            ("TDRC", TDRC, c.year),
            ("TCON", TCON, derived.genre),
            ("TPUB", TPUB, c.label),
            ("TCOP", TCOP, c.copyright),
            ("TALB", TALB, derived.album),
        ]
        if policy.titles.enabled:
            to_set.append(("TIT2", TIT2, derived.title))
        to_set = [(fid, cls, v) for fid, cls, v in to_set if v is not None]
        replace_ids = {fid for fid, _, _ in to_set}

        for key in list(tags.keys()):
            if self._is_strip(key, policy) or key in replace_ids:
                result.entries.append(
                    TagEntry(key, _preview_frame(tags[key]), "strip", "tag")
                )
                del tags[key]
            else:
                result.entries.append(
                    TagEntry(key, _preview_frame(tags[key]), "keep", "tag")
                )

        for frame_id, cls, value in to_set:
            tags.add(cls(encoding=3, text=[value]))
            result.entries.append(TagEntry(frame_id, preview(value), "set", "tag"))

        if not dry_run:
            tags.save(path, v2_version=4)
        return result
