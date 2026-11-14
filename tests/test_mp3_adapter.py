from mutagen.id3 import ID3

from metascrub.formats import Derived
from metascrub.formats.mp3 import MP3Adapter
from metascrub.policy import Credits, Policy


def policy():
    p = Policy()
    p.credits = Credits(artist="Example Artist", composer="Jane Doe",
                        label="Example Records",
                        copyright="© 2026 Example. All rights reserved.",
                        year="2026", album="[001] Midnight Drive",
                        release_subdir="RELEASES")
    return p


def test_clean_strips_provenance_and_sets_credits(mp3_dirty):
    adapter = MP3Adapter()
    derived = Derived(title="Neon Skyline", genre="DNB", album="[001] Midnight Drive")
    result = adapter.clean(str(mp3_dirty), "RELEASES/x/Neon Skyline.mp3",
                           policy(), derived, dry_run=False)
    assert result.error is None

    tags = ID3(str(mp3_dirty))
    keys = list(tags.keys())
    assert not any(k.startswith(("COMM", "USLT", "WOAS", "GEOB", "TSSE", "TXXX", "APIC"))
                   for k in keys)
    assert tags["TPE1"].text[0] == "Example Artist"
    assert tags["TPE2"].text[0] == "Example Artist"
    assert tags["TCOM"].text[0] == "Jane Doe"
    assert str(tags["TDRC"].text[0]) == "2026"
    assert tags["TCON"].text[0] == "DNB"
    assert tags["TPUB"].text[0] == "Example Records"
    assert "2026 Example" in tags["TCOP"].text[0]
    assert tags["TALB"].text[0] == "[001] Midnight Drive"
    assert tags["TIT2"].text[0] == "Neon Skyline"


def test_dry_run_leaves_file_untouched(mp3_dirty):
    before = mp3_dirty.read_bytes()
    MP3Adapter().clean(str(mp3_dirty), "x.mp3", policy(),
                       Derived(title="Neon Skyline", genre="DNB", album=None), dry_run=True)
    assert mp3_dirty.read_bytes() == before
    assert "made with suno" in repr(ID3(str(mp3_dirty)).items())


def test_keep_cover_art_option(mp3_dirty):
    p = policy()
    p.remove_cover_art = False
    MP3Adapter().clean(str(mp3_dirty), "x.mp3", p,
                       Derived(title="Neon Skyline", genre="DNB", album=None), dry_run=False)
    assert any(k.startswith("APIC") for k in ID3(str(mp3_dirty)).keys())


def test_inspect_predicts_strip_actions(mp3_dirty):
    result = MP3Adapter().inspect(str(mp3_dirty), "x.mp3", policy())
    by_prefix = {}
    for e in result.entries:
        by_prefix.setdefault(e.key.split(":")[0], e.action)
    assert by_prefix["COMM"] == "strip"
    assert by_prefix["USLT"] == "strip"
    assert by_prefix["WOAS"] == "strip"
    assert by_prefix["GEOB"] == "strip"
    assert by_prefix["TSSE"] == "strip"
    assert by_prefix["TXXX"] == "strip"
    assert by_prefix["APIC"] == "strip"
    assert by_prefix["TIT2"] == "keep"
    assert by_prefix["TPE1"] == "keep"


def test_tagless_mp3_gets_a_fresh_tag(tmp_path):
    f = tmp_path / "bare.mp3"
    f.write_bytes(b"")
    result = MP3Adapter().clean(str(f), "bare.mp3", policy(),
                                Derived(title="Bare", genre="DNB", album=None),
                                dry_run=False)
    assert result.error is None
    tags = ID3(str(f))
    assert tags["TPE1"].text[0] == "Example Artist"
    assert "TALB" not in tags  # not under RELEASES
