from metascrub.titles import TitleRules


def rule(**kw):
    defaults = dict(strip_label_prefix="Example Records - ")
    defaults.update(kw)
    return TitleRules(**defaults)


def test_strips_label_genre_year():
    assert rule().derive("Example Records - [DNB] - Aurora (2026).mp3") == "Aurora"


def test_keeps_edition_and_version():
    assert rule().derive(
        "Example Records - [Metal] - Monochrome [NextGen Edition] (2026) v2.wav"
    ) == "Monochrome [NextGen Edition] v2"


def test_filename_without_genre_bracket():
    assert rule().derive("Example Records - The Machine (2026).mp3") == "The Machine"


def test_bare_genre_prefix_token():
    r = rule(strip_genre_prefixes=["DnB", "2step"])
    assert r.derive("DnB - Neon Skyline.mp3") == "Neon Skyline"
    assert r.derive("2step - Velvet Tone (2026).mp3") == "Velvet Tone"


def test_bare_genre_prefix_not_in_list_is_kept():
    assert rule().derive("DnB - Neon Skyline.mp3") == "DnB - Neon Skyline"


def test_no_label_prefix_configured():
    r = TitleRules()
    assert r.derive("Example Records - [DNB] - Vapor Trail (2026).mp3") == "Example Records - Vapor Trail"


def test_year_preserved_when_disabled():
    r = rule(strip_year_suffix=False)
    assert r.derive("Example Records - [DNB] - Vapor Trail (2026).mp3") == "Vapor Trail (2026)"


def test_unicode_titles():
    assert rule().derive("Example Records - [Russian Rap] - Тестовый трек! [Club Edition] (2026).mp3") \
        == "Тестовый трек! [Club Edition]"


def test_whitespace_collapsed():
    assert rule().derive("Example Records - [Trapcore] - Starfall  [NextGen Edition] (2026) v1.mp3") \
        == "Starfall [NextGen Edition] v1"
