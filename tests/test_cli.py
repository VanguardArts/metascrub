from mutagen.id3 import ID3

from metascrub.cli import main

from conftest import build_wav_bytes, make_mp3, make_wav


def build_tree(tmp_path):
    rel_dir = tmp_path / "RELEASES" / "[ 001 ] Test Release (2026)"
    rel_dir.mkdir(parents=True)
    make_mp3(rel_dir / "Test Label - [DNB] - Neon Skyline (2026).mp3")

    singles = tmp_path / "SINGLES"
    singles.mkdir()
    make_wav(singles / "Test Label - [2step] - Vapor Trail (2026).wav",
             info={"ICMT": "made with suno; id=zzz", "ISFT": "Lavf60.16.100"})

    samples = tmp_path / "Samples" / "Imported"
    samples.mkdir(parents=True)
    make_wav(samples / "loop.wav", info={"ICMT": "made with suno"})
    return tmp_path


CLEAN_ARGS = [
    "--artist", "Example Artist",
    "--composer", "Jane Doe",
    "--label", "Example Records",
    "--copyright", "© 2026 Example. All rights reserved.",
    "--year", "2026",
    "--album", "[001] Midnight Drive",
    "--release-subdir", "RELEASES",
    "--label-prefix", "Test Label - ",
    "--exclude", r"Samples/",
]


def test_clean_dry_run_then_apply(tmp_path):
    root = build_tree(tmp_path)
    mp3 = next(root.rglob("*.mp3"))
    wav = next(root.rglob("*Vapor Trail*.wav"))

    # Dry run: nothing changes.
    assert main(["clean", str(root), *CLEAN_ARGS]) == 0
    assert "made with suno" in repr(ID3(str(mp3)).items())

    # Apply: credits in place, junk gone.
    assert main(["clean", str(root), *CLEAN_ARGS, "--apply"]) == 0
    tags = ID3(str(mp3))
    assert tags["TIT2"].text[0] == "Neon Skyline"
    assert tags["TALB"].text[0] == "[001] Midnight Drive"
    assert tags["TPE1"].text[0] == "Example Artist"
    assert "made with suno" not in repr(tags.items())

    raw = wav.read_bytes()
    assert b"C2PA" not in raw and b"made with suno" not in raw

    # Excluded file untouched.
    loop = next(root.rglob("loop.wav"))
    assert b"made with suno" in loop.read_bytes()

    # And verify now passes.
    assert main(["verify", str(root), "--exclude", r"Samples/"]) == 0


def test_verify_fails_on_dirty_files(tmp_path):
    root = build_tree(tmp_path)
    assert main(["verify", str(root), "--exclude", r"Samples/"]) == 1


def test_scan_lists_predicted_actions(tmp_path, capsys):
    root = build_tree(tmp_path)
    assert main(["scan", str(root)]) == 0
    out = capsys.readouterr().out
    assert "chunk:C2PA" in out
    assert "[strip]" in out


def test_policy_file_plus_cli_override(tmp_path):
    root = build_tree(tmp_path)
    policy = tmp_path / "policy.json"
    policy.write_text(
        '{"credits": {"artist": "Wrong Artist", "year": "2026"}, '
        '"titles": {"strip_label_prefix": "Test Label - "}}'
    )
    assert main(["clean", str(root), "--policy", str(policy),
                 "--artist", "Example Artist", "--apply"]) == 0
    tags = ID3(str(next(root.rglob("*.mp3"))))
    assert tags["TPE1"].text[0] == "Example Artist"          # CLI overrode policy file
    assert str(tags["TDRC"].text[0]) == "2026"    # from policy file
