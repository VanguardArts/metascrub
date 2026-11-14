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


@pytest.fixture(autouse=True)
def _widget_cleanup(qapp):
    """Destroy leaked top-level widgets after each test.

    Signal connections on child widgets capture their page, forming
    reference cycles that CPython's GC cannot see through C++. Leaked
    widgets would otherwise survive into interpreter shutdown, where
    PySide6's global cleanup destroys them in a bad state (SIGSEGV in
    QWidget::destroy via Shiboken::BindingManager::visitAllPyObjects).
    """
    yield
    for w in QApplication.topLevelWidgets():
        w.deleteLater()
    qapp.sendPostedEvents(None, 0)
    qapp.processEvents()


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
def test_tutorial_dialog_flow(qapp):
    from metascrub.gui.wizard import PAGES, TutorialDialog
    dlg = TutorialDialog()
    assert dlg._page == 0
    assert not dlg.back_btn.isEnabled()
    assert dlg.next_btn.text() == "Next"
    for i in range(1, len(PAGES)):
        dlg.next()
        assert dlg._page == i
    assert dlg.next_btn.text() == "Finish"
    dlg.back()
    assert dlg._page == len(PAGES) - 2
    dlg.close()


def test_tutorial_first_launch_and_reopen(qapp, monkeypatch):
    from PySide6.QtCore import QSettings
    from PySide6.QtTest import QTest

    from metascrub.gui import main_window as mw_mod
    from metascrub.gui.main_window import MainWindow

    settings = QSettings("metascrub", "metascrub")
    settings.remove("tutorial_seen")

    opened = []
    monkeypatch.setattr(mw_mod.TutorialDialog, "exec",
                        lambda self: opened.append(1) or 0)

    w = MainWindow()
    w.show()
    w.auto_tutorial_if_first_launch()  # what app.py does after window.show()
    QTest.qWait(600)  # let the first-launch timer fire
    assert opened, "tutorial should auto-open on first launch"
    assert settings.value("tutorial_seen", False, type=bool) is True
    w.close()

    opened.clear()
    w2 = MainWindow()
    w2.show()
    w2.auto_tutorial_if_first_launch()
    QTest.qWait(600)
    assert not opened, "tutorial must not auto-open on second launch"
    w2.tutorial_btn.click()  # ...but is summonable anytime
    assert opened, "sidebar button should open the tutorial"
    w2.close()
    settings.remove("tutorial_seen")
def test_scan_uses_clean_form_policy(qapp):
    from metascrub.gui.main_window import MainWindow
    w = MainWindow()
    scan, clean = w.pages[0], w.pages[1]
    clean.artist.setText("Example Artist")
    assert scan._policy().credits.artist == "Example Artist"
    assert not scan.auto_btn.isEnabled()  # nothing scanned yet
    w.close()


def test_auto_clean_end_to_end(qapp, tmp_path, monkeypatch):
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QMessageBox

    from conftest import make_wav
    from metascrub import scanner
    from metascrub.gui.main_window import MainWindow
    from metascrub.policy import Policy

    make_wav(tmp_path / "Example Records - [DNB] - Neon Skyline (2026).wav",
             info={"ICMT": "made with suno; id=x", "ISFT": "Lavf60.16.100"})

    w = MainWindow()  # never shown -> no first-launch tutorial interferes
    w.path_edit.setText(str(tmp_path))
    scan = w.pages[0]

    # auto-accept the confirmation dialog
    monkeypatch.setattr(QMessageBox, "exec", lambda _self: QMessageBox.Yes)

    scan.run_scan()
    scan._worker.wait(10000)
    QTest.qWait(100)
    assert scan.auto_btn.isEnabled()
    assert "1" in scan.auto_btn.text()

    scan.auto_btn.click()
    QTest.qWait(100)
    scan._worker.wait(10000)   # the clean worker
    QTest.qWait(200)
    scan._worker.wait(10000)   # the automatic re-scan worker
    QTest.qWait(100)

    hits = sum(len(r.entries) for r in scanner.verify(str(tmp_path), Policy()))
    assert hits == 0, "file should be provenance-clean after auto-clean"
    assert not any(e.action == "strip"
                   for r in scan.results for e in r.entries),         "re-scan should show nothing left to strip"
    w.close()
def test_chained_worker_starts_retire_previous_safely(qapp, tmp_path):
    """Regression: chained _start() from inside a done handler (what
    auto-clean does) must retire the previous worker safely — a QThread
    dropped for GC while its run() epilogue is still unwinding can crash
    the process."""
    from PySide6.QtTest import QTest

    from conftest import make_wav
    from metascrub import scanner
    from metascrub.gui.pages import ScanPage
    from metascrub.gui.workers import Worker

    make_wav(tmp_path / "Example Records - [DNB] - Neon Skyline (2026).wav",
             info={"ICMT": "made with suno; id=x"})
    page = ScanPage(lambda: str(tmp_path))
    CHAIN = 15
    finished = {"n": 0}

    def on_results(_results):
        finished["n"] += 1
        if finished["n"] < CHAIN:
            # start the next worker straight from the done handler: the
            # previous worker's thread is still unwinding at this point
            w = Worker(scanner.scan, str(tmp_path), page._policy())
            w.done.connect(on_results)
            page._start(w, [page.scan_btn], page.progress)

    page._on_results = on_results  # run_scan() connects this attribute
    page.run_scan()
    while finished["n"] < CHAIN:
        QTest.qWait(50)
    page._worker.wait(10000)
    QTest.qWait(50)
    assert finished["n"] == CHAIN


def test_progress_caption_lives_on_label(qapp):
    from metascrub.gui.pages import ScanPage
    page = ScanPage(lambda: "/tmp")
    assert not page.progress.isTextVisible()  # bar shows fill only
    assert page.progress_label.objectName() == "progress"
    page._update_progress(page.progress, 3, 10, "sub/dir/some-track.wav")
    assert page.progress.value() == 3
    assert page.progress.maximum() == 10
    assert "3/10" in page.progress_label.text()
    assert "some-track.wav" in page.progress_label.text()
def test_long_paths_do_not_expand_window(qapp):
    from PySide6.QtWidgets import QSizePolicy

    from metascrub.gui.main_window import MainWindow
    w = MainWindow()
    w.resize(1180, 780)
    w.show()
    scan = w.pages[0]
    assert (scan.progress_label.sizePolicy().horizontalPolicy()
            == QSizePolicy.Policy.Ignored)
    scan.progress.setVisible(True)
    scan.progress_label.setVisible(True)
    scan._update_progress(scan.progress, 2, 9,
                          "deep/" + "nested-" * 100 + "/track.wav")
    qapp.processEvents()
    assert w.width() <= 1180, "window must not grow to fit long captions"
    w.close()
def test_clean_page_evict_and_signatures(qapp):
    from metascrub.gui.pages import CleanPage
    page = CleanPage(lambda: "/tmp")
    assert page.evict_cb.isChecked() is False  # non-destructive default
    page.evict_cb.setChecked(True)
    page.signatures.setText("oldusername, secretproject")
    p = page.build_policy()
    assert p.remove_unset_credits is True
    assert p.extra_signatures == ["oldusername", "secretproject"]
    page2 = CleanPage(lambda: "/tmp")
    page2.load_policy(p)
    assert page2.evict_cb.isChecked() is True
    assert page2.signatures.text() == "oldusername, secretproject"
