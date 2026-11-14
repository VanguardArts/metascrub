import json

import pytest

from metascrub.policy import Credits, Policy


def test_album_only_under_release_subdir():
    c = Credits(album="[001] Midnight Drive", release_subdir="RELEASES")
    assert c.album_for("RELEASES/001/track.mp3") == "[001] Midnight Drive"
    assert c.album_for("SINGLES/track.mp3") is None


def test_album_everywhere_without_release_subdir():
    c = Credits(album="X")
    assert c.album_for("anywhere/track.mp3") == "X"


def test_exclude_regex():
    p = Policy(exclude=[r"Samples/", r"OtherArtist"])
    assert p.is_excluded("SINGLES/OtherArtist - Old (2011)/a.wav")
    assert p.is_excluded("Samples/Imported/x.wav")
    assert not p.is_excluded("RELEASES/track.mp3")


def test_from_dict_round_trip(tmp_path):
    d = {
        "credits": {"artist": "Example Artist", "album": "[001] Midnight Drive",
                    "release_subdir": "RELEASES"},
        "titles": {"strip_label_prefix": "Example Records - "},
        "genre_mode": "brackets",
        "remove_cover_art": False,
        "exclude": ["OtherArtist"],
    }
    f = tmp_path / "policy.json"
    f.write_text(json.dumps(d))
    p = Policy.load(str(f))
    assert p.credits.artist == "Example Artist"
    assert p.credits.release_subdir == "RELEASES"
    assert p.titles.strip_label_prefix == "Example Records - "
    assert p.remove_cover_art is False
    assert p.is_excluded("x/OtherArtist/y.mp3")


def test_yaml_policy(tmp_path):
    yaml = pytest.importorskip("yaml")
    f = tmp_path / "policy.yaml"
    f.write_text(
        "credits:\n  artist: Example Artist\n  composer: Jane Doe\n"
        "titles:\n  strip_label_prefix: 'Example Records - '\n"
        "genre_mode: brackets\n"
    )
    p = Policy.load(str(f))
    assert p.credits.composer == "Jane Doe"
    assert p.genre_mode == "brackets"


def test_unknown_key_fails(tmp_path):
    f = tmp_path / "policy.json"
    f.write_text(json.dumps({"credits": {"artst": "typo"}}))
    with pytest.raises(KeyError):
        Policy.load(str(f))


def test_signatures_include_extras():
    p = Policy(extra_signatures=["aiuser42"])
    assert "aiuser42" in p.signatures()
    assert "suno" in p.signatures()
