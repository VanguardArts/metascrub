import struct

import pytest
from mutagen.id3 import (
    APIC,
    COMM,
    GEOB,
    ID3,
    TIT2,
    TPE1,
    TSSE,
    TXXX,
    USLT,
    WOAS,
)


def _info_field(code, text):
    b = text.encode("utf-8") + b"\x00"
    if len(b) % 2:
        b += b"\x00"
    return code.encode("ascii") + struct.pack("<I", len(b)) + b


def build_wav_bytes(info=None, c2pa=True, audio=b"\x01\x02\x03\x04" * 512,
                    extra_chunks=()):
    """Build a minimal valid PCM WAV with optional INFO + C2PA chunks."""
    fmt_body = struct.pack("<HHIIHH", 1, 2, 44100, 44100 * 4, 4, 16)
    chunks = [(b"fmt ", fmt_body)]
    if info:
        sub = b"".join(_info_field(c, v) for c, v in info.items())
        chunks.append((b"LIST", b"INFO" + sub))
    chunks.append((b"data", audio))
    chunks.extend(extra_chunks)
    if c2pa:
        chunks.append((b"C2PA", b"FAKE-C2PA-MANIFEST made with suno"))
    out = bytearray(b"RIFF\x00\x00\x00\x00WAVE")
    for cid, body in chunks:
        out += cid + struct.pack("<I", len(body)) + body
        if len(body) % 2:
            out += b"\x00"
    out[4:8] = struct.pack("<I", len(out) - 8)
    return bytes(out)


def make_wav(path, **kwargs):
    path.write_bytes(build_wav_bytes(**kwargs))
    return path


def make_mp3(path, title="Example Records - [DNB] - Neon Skyline (2026)"):
    """Write an ID3v2.4 tag full of provenance junk onto a dummy file."""
    path.write_bytes(b"")
    id3 = ID3()
    id3.add(TIT2(encoding=3, text=[title]))
    id3.add(TPE1(encoding=3, text=["aiuser42"]))
    id3.add(COMM(encoding=3, lang="eng", desc="",
                 text=["made with suno; created=2026-03-31T13:07:59Z; id=abc-123"]))
    id3.add(USLT(encoding=3, lang="eng", desc="",
                 text="[Instrumental]\n[distorted kick drum]"))
    id3.add(WOAS(url="https://suno.com/song/abc-123"))
    id3.add(TSSE(encoding=3, text=["Lavf60.16.100"]))
    id3.add(TXXX(encoding=3, desc="major_brand", text=["isom"]))
    id3.add(GEOB(encoding=3, mime="application/c2pa", filename="",
                 desc="c2pa manifest store", data=b"fake-c2pa"))
    id3.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover",
                 data=b"\xff\xd8\xff\xe0fakejpeg"))
    id3.save(path, v2_version=4)
    return path


@pytest.fixture
def wav_dirty(tmp_path):
    return make_wav(tmp_path / "Label - [DNB] - Neon Skyline (2026).wav",
                    info={"ICMT": "made with suno; created=2026-09-21; id=abc",
                          "ISFT": "Lavf60.16.100"})


@pytest.fixture
def mp3_dirty(tmp_path):
    return make_mp3(tmp_path / "Label - [DNB] - Neon Skyline (2026).mp3")
