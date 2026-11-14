"""Headless GUI smoke tests (Qt offscreen platform)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from metascrub.report import FileResult, TagEntry


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication(["metascrub-test"])
    yield app
    # Teardown hygiene: close windows + flush deferred deletes so Qt has
    # less work (and less to trip over) at interpreter exit.
    app.closeAllWindows()
    app.sendPostedEvents(None, 0)
    app.processEvents()


def test_main_window_builds_and_navigates(qapp):
    from metascrub.gui.main_window import MainWindow
    w = MainWindow()
    assert w.stack.count() == 3
    for i, btn in enumerate(w.nav_buttons):
        btn.click()
        assert w.stack.currentIndex() == i
    w.close()


def test_clean_page_policy_roundtrip(qapp):
    from metascrub.gui.pages import CleanPage
    page = CleanPage(lambda: "/tmp")
    page.artist.setText("Example Artist")
    page.composer.setText("Jane Doe")
    page.label.setText("Example Records")
    page.copyright.setText("© 2026 Example Records. All rights reserved.")
    page.year.setText("2026")
    page.album.setText("[001] Midnight Drive")
    page.release_subdir.setText("RELEASES")
    page.label_prefix.setText("Example Records - ")
    page.excludes.setText("Samples/, OtherArtist")
    page.genre_mode.setCurrentIndex(0)

    p = page.build_policy()
    assert p.credits.artist == "Example Artist"
    assert p.credits.composer == "Jane Doe"
    assert p.credits.release_subdir == "RELEASES"
    assert p.genre_mode == "brackets"
    assert p.titles.strip_label_prefix == "Example Records - "
    assert p.remove_cover_art is True
    assert p.exclude == ["Samples/", "OtherArtist"]

    # and the form can be re-populated from that policy
    page2 = CleanPage(lambda: "/tmp")
    page2.load_policy(p)
    assert page2.artist.text() == "Example Artist"
    assert page2.excludes.text() == "Samples/, OtherArtist"


def test_clean_page_empty_fields_become_none(qapp):
    from metascrub.gui.pages import CleanPage
    p = CleanPage(lambda: "/tmp").build_policy()
    assert p.credits.artist is None
    assert p.credits.album is None
    assert p.exclude == []


def test_results_table_populates_and_filters(qapp):
    from metascrub.gui.pages import ScanPage
    page = ScanPage(lambda: "/tmp")
    results = [
        FileResult(path="a.mp3", format="mp3", entries=[
            TagEntry("COMM::eng", "made with x", "strip", "tag"),
            TagEntry("TIT2", "Song", "keep", "tag"),
        ]),
        FileResult(path="b.wav", format="wav", entries=[
            TagEntry("chunk:C2PA", "33 bytes", "strip", "provenance"),
        ]),
        FileResult(path="skip/loop.wav", format="wav", skipped=True),
    ]
    page.populate(results)
    # 2 + 1 entries + 1 skipped row
    assert page.table.rowCount() == 4
    actions = {page.table.item(r, 3).text() for r in range(page.table.rowCount())}
    assert "strip" in actions and "keep" in actions and "skip" in actions

    page.filter_edit.setText("c2pa")
    page.populate(results)
    assert page.table.rowCount() == 1
    assert page.table.item(0, 2).text() == "chunk:C2PA"


def test_verify_badge_states(qapp):
    from metascrub.gui.pages import VerifyPage
    page = VerifyPage(lambda: "/tmp")
    page._on_results([FileResult(path="a.mp3", format="mp3", entries=[])])
    assert page.badge.objectName() == "badgeOk"
    page._on_results([FileResult(path="a.mp3", format="mp3", entries=[
        TagEntry("COMM::eng", "made with x", "strip", "tag")])])
    assert page.badge.objectName() == "badgeBad"
    assert page.table.rowCount() == 1


def test_gui_entrypoint_imports(qapp):
    from metascrub.gui import app
    assert callable(app.main)
def test_places_discovery(qapp):
    import os
    from pathlib import Path

    from metascrub.gui.places import mounted_places
    places = mounted_places()
    assert places, "expected at least Home"
    assert places[0].path == str(Path.home())
    assert all(os.path.exists(p.path) for p in places)


def test_places_menu_populates_and_selects(qapp):
    from metascrub.gui.main_window import MainWindow
    w = MainWindow()
    w._fill_places()
    actions = w.places_menu.actions()
    assert len(actions) >= 2
    assert actions[0].text().startswith("Home")
    # selecting a place fills the path field
    actions[0].trigger()
    from pathlib import Path
    assert w.path_edit.text() == str(Path.home())
    w.close()
def test_eight_themes_render(qapp):
    from metascrub.gui import theme
    names = theme.theme_names()
    assert len(names) == 8  # 7 accent colors + slate/anthracite
    assert "slate" in names and "tidal" in names
    for n in names:
        assert "$" not in theme.qss(n), n
        assert theme.icon_svg(n).startswith("<svg"), n
    # slate/anthracite has a neutral gray background, unlike the others
    assert theme.palette("slate")["bg"] == "#17191c"
    assert theme.palette("tidal")["bg"] == "#0e1116"


def test_theme_picker_switches_and_persists(qapp):
    from PySide6.QtWidgets import QApplication

    from metascrub.gui import theme
    from metascrub.gui.main_window import MainWindow
    w = MainWindow()
    assert w.theme_combo.count() == 8
    idx = w.theme_combo.findData("slate")
    w.theme_combo.setCurrentIndex(idx)
    assert theme.current_theme() == "slate"
    assert w._settings.value("theme") == "slate"
    assert "#17191c" in QApplication.instance().styleSheet()
    # back to default, and forget the setting so user prefs stay untouched
    w.theme_combo.setCurrentIndex(w.theme_combo.findData(theme.DEFAULT_THEME))
    assert theme.current_theme() == theme.DEFAULT_THEME
    w._settings.remove("theme")
    w.close()
