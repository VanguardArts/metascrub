import struct

from metascrub.formats import Derived
from metascrub.formats.wav import WAVAdapter, _parse_chunks
from metascrub.policy import Credits, Policy

from conftest import make_wav


def policy(**kw):
    p = Policy()
    p.credits = Credits(artist="Example Artist", composer="Jane Doe",
                        label="Example Records",
                        copyright="© 2026 Example. All rights reserved.",
                        year="2026", album="[001] Midnight Drive")
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def info_map(path):
    data = path.read_bytes()
    for cid, body in _parse_chunks(data):
        if cid == b"LIST" and body[:4] == b"INFO":
            out = {}
            pos = 4
            while pos + 8 <= len(body):
                code = body[pos:pos + 4].decode("latin-1")
                size = struct.unpack_from("<I", body, pos + 4)[0]
                out[code] = body[pos + 8:pos + 8 + size].rstrip(b"\x00").decode("utf-8")
                pos += 8 + size + (size & 1)
            return out
    return {}


def chunk_ids(path):
    return [cid for cid, _ in _parse_chunks(path.read_bytes())]


def test_clean_strips_c2pa_and_info_junk(wav_dirty):
    adapter = WAVAdapter()
    derived = Derived(title="Neon Skyline", genre="DNB", album="[001] Midnight Drive")
    result = adapter.clean(str(wav_dirty), "Neon Skyline.wav", policy(), derived, dry_run=False)

    assert result.error is None
    ids = chunk_ids(wav_dirty)
    assert b"C2PA" not in ids
    info = info_map(wav_dirty)
    assert "ICMT" not in info
    assert "ISFT" not in info
    assert info["INAM"] == "Neon Skyline"
    assert info["IART"] == "Example Artist"
    assert info["IPRD"] == "[001] Midnight Drive"
    assert info["IGNR"] == "DNB"
    assert info["ICRD"] == "2026"
    assert info["ICOP"] == "© 2026 Example. All rights reserved."
    assert info["IENG"] == "Jane Doe"


def test_clean_is_byte_safe_for_audio(wav_dirty):
    before = {cid: body for cid, body in _parse_chunks(wav_dirty.read_bytes())}
    adapter = WAVAdapter()
    derived = Derived(title="Neon Skyline", genre="DNB", album=None)
    adapter.clean(str(wav_dirty), "x.wav", policy(), derived, dry_run=False)
    after = {cid: body for cid, body in _parse_chunks(wav_dirty.read_bytes())}
    assert after[b"fmt "] == before[b"fmt "]
    assert after[b"data"] == before[b"data"]


def test_dry_run_leaves_file_untouched(wav_dirty):
    before = wav_dirty.read_bytes()
    adapter = WAVAdapter()
    derived = Derived(title="Neon Skyline", genre="DNB", album=None)
    result = adapter.clean(str(wav_dirty), "x.wav", policy(), derived, dry_run=True)
    assert wav_dirty.read_bytes() == before
    assert any(e.action == "strip" for e in result.entries)


def test_unknown_chunks_are_preserved(tmp_path):
    wav = make_wav(tmp_path / "t.wav",
                   info={"ICMT": "made with suno"},
                   extra_chunks=[(b"smpl", b"\x00" * 36)])
    adapter = WAVAdapter()
    adapter.clean(str(wav), "t.wav", policy(),
                  Derived(title="t", genre="DNB", album=None), dry_run=False)
    ids = chunk_ids(wav)
    assert b"smpl" in ids
    assert b"C2PA" not in ids


def test_no_list_chunk_gets_one_inserted(tmp_path):
    wav = make_wav(tmp_path / "t.wav", info=None, c2pa=False)
    assert b"LIST" not in chunk_ids(wav)
    adapter = WAVAdapter()
    adapter.clean(str(wav), "t.wav", policy(),
                  Derived(title="t", genre="DNB", album=None), dry_run=False)
    assert info_map(wav)["IART"] == "Example Artist"


def test_inspect_marks_c2pa_as_strip(wav_dirty):
    result = WAVAdapter().inspect(str(wav_dirty), "x.wav", policy())
    by_key = {e.key: e.action for e in result.entries}
    assert by_key["chunk:C2PA"] == "strip"
    assert by_key["INFO:ICMT"] == "strip"
    assert by_key["INFO:ISFT"] == "strip"
    assert by_key["chunk:fmt "] == "keep"
    assert by_key["chunk:data"] == "keep"
