"""GUI pages: Scan, Clean, Verify.

Each page is self-contained: it owns its background Worker, renders results
into a color-coded table, and reads the target folder from the MainWindow via
a ``root_provider`` callable.
"""
from __future__ import annotations

import json
from typing import Callable, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .. import scanner
from ..policy import Policy
from ..report import FileResult, render_json, render_text
from .theme import ACTION_COLORS
from .workers import Worker


# --------------------------------------------------------------------------
# shared helpers
# --------------------------------------------------------------------------

def _make_table() -> QTableWidget:
    t = QTableWidget(0, 5)
    t.setHorizontalHeaderLabels(["File", "Format", "Tag / Chunk", "Action", "Value"])
    header = t.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.Interactive)
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(2, QHeaderView.Interactive)
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(4, QHeaderView.Stretch)
    t.setColumnWidth(0, 340)
    t.setColumnWidth(2, 200)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setAlternatingRowColors(True)
    t.verticalHeader().setVisible(False)
    t.setShowGrid(False)
    t.setWordWrap(False)
    return t


def results_to_rows(results: List[FileResult]) -> List[tuple]:
    rows = []
    for r in results:
        if r.skipped:
            rows.append((r.path, r.format, "(excluded by policy)", "skip", ""))
            continue
        if r.error:
            rows.append((r.path, r.format, r.error, "error", ""))
            continue
        for e in r.entries:
            rows.append((r.path, r.format, e.key, e.action, e.value))
    return rows


def _populate_table(table: QTableWidget, results: List[FileResult],
                    text_filter: str = "") -> None:
    rows = results_to_rows(results)
    if text_filter:
        f = text_filter.lower()
        rows = [r for r in rows if f in r[0].lower() or f in r[2].lower()
                or f in r[4].lower() or f in r[3].lower()]
    table.setSortingEnabled(False)
    table.setRowCount(len(rows))
    for i, (path, fmt, key, action, value) in enumerate(rows):
        items = [
            QTableWidgetItem(path),
            QTableWidgetItem(fmt),
            QTableWidgetItem(key),
            QTableWidgetItem(action),
            QTableWidgetItem(value),
        ]
        items[3].setForeground(QColor(ACTION_COLORS.get(action, "#e6edf3")))
        items[3].setTextAlignment(Qt.AlignCenter)
        items[0].setToolTip(path)
        items[4].setToolTip(value)
        for col, item in enumerate(items):
            table.setItem(i, col, item)
    table.setSortingEnabled(True)


def _summarize(results: List[FileResult]) -> str:
    files = len(results)
    strips = sets = errors = skipped = 0
    for r in results:
        if r.skipped:
            skipped += 1
        if r.error:
            errors += 1
        for e in r.entries:
            if e.action == "strip":
                strips += 1
            elif e.action == "set":
                sets += 1
    return (f"{files} file(s) · {strips} tag(s) to strip · {sets} tag(s) to set"
            f" · {skipped} excluded · {errors} error(s)")


class _BusyPage(QWidget):
    """Common bits: progress bar, run-state handling, worker lifecycle."""

    def __init__(self, root_provider: Callable[[], str]):
        super().__init__()
        self._root_provider = root_provider
        self._worker: Optional[Worker] = None

    def root(self) -> str:
        return self._root_provider().strip()

    def _start(self, worker: Worker, run_buttons: List[QPushButton],
               progress: QProgressBar):
        self._worker = worker
        for b in run_buttons:
            b.setEnabled(False)
        progress.setVisible(True)
        progress.setRange(0, 0)  # indeterminate until first progress signal
        worker.progressed.connect(
            lambda i, n, rel: (progress.setRange(0, n), progress.setValue(i),
                               progress.setFormat(f"{i}/{n}  {rel}")))
        worker.done.connect(lambda results: self._finish(run_buttons, progress))
        worker.failed.connect(lambda msg: self._fail(msg, run_buttons, progress))
        worker.start()

    def _finish(self, buttons, progress):
        for b in buttons:
            b.setEnabled(True)
        progress.setVisible(False)

    def _fail(self, msg, buttons, progress):
        self._finish(buttons, progress)
        QMessageBox.critical(self, "metascrub", f"Operation failed:\n{msg}")


# --------------------------------------------------------------------------
# Scan page
# --------------------------------------------------------------------------

class ScanPage(_BusyPage):
    def __init__(self, root_provider):
        super().__init__(root_provider)
        self.results: List[FileResult] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        bar = QHBoxLayout()
        self.scan_btn = QPushButton("Scan folder")
        self.scan_btn.setObjectName("accent")
        self.scan_btn.clicked.connect(self.run_scan)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter results…")
        self.filter_edit.textChanged.connect(lambda _t: self.populate(self.results))
        bar.addWidget(self.scan_btn)
        bar.addWidget(self.filter_edit, 1)
        lay.addLayout(bar)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        lay.addWidget(self.progress)

        self.summary = QLabel("Pick a folder above, then scan to see every embedded tag.")
        self.summary.setObjectName("summary")
        lay.addWidget(self.summary)

        self.table = _make_table()
        lay.addWidget(self.table, 1)

    def run_scan(self):
        root = self.root()
        if not root:
            QMessageBox.warning(self, "metascrub", "Choose a folder first.")
            return
        worker = Worker(scanner.scan, root, Policy())
        worker.done.connect(self._on_results)
        self._start(worker, [self.scan_btn], self.progress)

    def _on_results(self, results):
        self.results = results
        self.populate(results)
        n = sum(len(r.entries) for r in results)
        self.summary.setText(
            f"{len(results)} file(s) · {n} embedded tag(s)/chunk(s) found — "
            f"red entries are what a clean would strip.")

    def populate(self, results):
        _populate_table(self.table, results, self.filter_edit.text())


# --------------------------------------------------------------------------
# Clean page
# --------------------------------------------------------------------------

class CleanPage(_BusyPage):
    GENRE_MODES = ["brackets", "fixed", "none"]

    def __init__(self, root_provider):
        super().__init__(root_provider)
        self.results: List[FileResult] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        # ---- form -----------------------------------------------------
        form_box = QGroupBox("Credits & rules")
        form = QFormLayout(form_box)
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(16)

        self.artist = QLineEdit(); self.artist.setPlaceholderText("e.g. Example Artist")
        self.album_artist = QLineEdit(); self.album_artist.setPlaceholderText("defaults to Artist")
        self.composer = QLineEdit(); self.composer.setPlaceholderText("production credit, e.g. Jane Doe")
        self.label = QLineEdit(); self.label.setPlaceholderText("e.g. Example Records (MP3 only)")
        self.copyright = QLineEdit(); self.copyright.setPlaceholderText("© 2026 Example Records. All rights reserved.")
        self.year = QLineEdit(); self.year.setPlaceholderText("e.g. 2026")
        self.album = QLineEdit(); self.album.setPlaceholderText("release name, e.g. [001] Midnight Drive")
        self.release_subdir = QLineEdit(); self.release_subdir.setPlaceholderText("e.g. RELEASES — only files under it get the album tag")

        form.addRow("Artist", self.artist)
        form.addRow("Album artist", self.album_artist)
        form.addRow("Composer / production", self.composer)
        form.addRow("Label", self.label)
        form.addRow("Copyright", self.copyright)
        form.addRow("Year", self.year)
        form.addRow("Album / release", self.album)
        form.addRow("Release subdir", self.release_subdir)

        rules_box = QGroupBox("Options")
        rules = QFormLayout(rules_box)
        rules.setLabelAlignment(Qt.AlignRight)

        self.genre_mode = QComboBox()
        self.genre_mode.addItems(["From filename [brackets]", "Fixed value", "None"])
        self.genre_fixed = QLineEdit()
        self.genre_fixed.setPlaceholderText("genre when 'Fixed value'")
        self.genre_fixed.setEnabled(False)
        self.genre_mode.currentIndexChanged.connect(
            lambda i: self.genre_fixed.setEnabled(i == 1))
        self.label_prefix = QLineEdit()
        self.label_prefix.setPlaceholderText('e.g. "Example Records - " stripped from titles')
        self.excludes = QLineEdit()
        self.excludes.setPlaceholderText("comma-separated regexes, e.g. Samples/, OldArchive")
        self.titles_cb = QCheckBox("Normalize titles from filenames")
        self.titles_cb.setChecked(True)
        self.cover_cb = QCheckBox("Strip embedded cover art")
        self.cover_cb.setChecked(True)

        rules.addRow("Genre", self.genre_mode)
        rules.addRow("", self.genre_fixed)
        rules.addRow("Label prefix", self.label_prefix)
        rules.addRow("Exclude paths", self.excludes)
        rules.addRow("", self.titles_cb)
        rules.addRow("", self.cover_cb)

        top = QHBoxLayout()
        top.addWidget(form_box, 3)
        top.addWidget(rules_box, 2)
        lay.addLayout(top)

        # ---- actions ---------------------------------------------------
        actions = QHBoxLayout()
        self.load_btn = QPushButton("Load policy…")
        self.save_btn = QPushButton("Save policy…")
        self.dry_btn = QPushButton("Dry run")
        self.apply_btn = QPushButton("Apply changes")
        self.apply_btn.setObjectName("accent")
        self.load_btn.clicked.connect(self.load_policy_dialog)
        self.save_btn.clicked.connect(self.save_policy_dialog)
        self.dry_btn.clicked.connect(lambda: self.run_clean(dry_run=True))
        self.apply_btn.clicked.connect(self._confirm_apply)
        actions.addWidget(self.load_btn)
        actions.addWidget(self.save_btn)
        actions.addStretch(1)
        actions.addWidget(self.dry_btn)
        actions.addWidget(self.apply_btn)
        lay.addLayout(actions)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        lay.addWidget(self.progress)

        self.summary = QLabel("Fill in the credits, run a dry run, review the diff, then apply.")
        self.summary.setObjectName("summary")
        lay.addWidget(self.summary)

        self.table = _make_table()
        lay.addWidget(self.table, 1)

    # -- form <-> policy ------------------------------------------------
    def build_policy(self) -> Policy:
        p = Policy()
        c = p.credits
        c.artist = self.artist.text().strip() or None
        c.album_artist = self.album_artist.text().strip() or None
        c.composer = self.composer.text().strip() or None
        c.label = self.label.text().strip() or None
        c.copyright = self.copyright.text().strip() or None
        c.year = self.year.text().strip() or None
        c.album = self.album.text().strip() or None
        c.release_subdir = self.release_subdir.text().strip() or None
        p.genre_mode = self.GENRE_MODES[self.genre_mode.currentIndex()]
        p.genre_fixed = self.genre_fixed.text().strip() or None
        p.titles.enabled = self.titles_cb.isChecked()
        p.titles.strip_label_prefix = self.label_prefix.text() or None
        p.remove_cover_art = self.cover_cb.isChecked()
        p.exclude = [s.strip() for s in self.excludes.text().split(",") if s.strip()]
        return p

    def load_policy(self, policy: Policy) -> None:
        c = policy.credits
        self.artist.setText(c.artist or "")
        self.album_artist.setText(c.album_artist or "")
        self.composer.setText(c.composer or "")
        self.label.setText(c.label or "")
        self.copyright.setText(c.copyright or "")
        self.year.setText(c.year or "")
        self.album.setText(c.album or "")
        self.release_subdir.setText(c.release_subdir or "")
        self.genre_mode.setCurrentIndex(self.GENRE_MODES.index(policy.genre_mode))
        self.genre_fixed.setText(policy.genre_fixed or "")
        self.titles_cb.setChecked(policy.titles.enabled)
        self.label_prefix.setText(policy.titles.strip_label_prefix or "")
        self.cover_cb.setChecked(policy.remove_cover_art)
        self.excludes.setText(", ".join(policy.exclude))

    def load_policy_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load policy", "", "Policies (*.yaml *.yml *.json)")
        if not path:
            return
        try:
            self.load_policy(Policy.load(path))
        except Exception as exc:
            QMessageBox.critical(self, "metascrub", f"Could not load policy:\n{exc}")

    def save_policy_dialog(self):
        path, flt = QFileDialog.getSaveFileName(
            self, "Save policy", "policy.yaml", "YAML (*.yaml);;JSON (*.json)")
        if not path:
            return
        data = self.build_policy().to_dict()
        try:
            if path.lower().endswith(".json"):
                text = json.dumps(data, indent=2, ensure_ascii=False)
            else:
                import yaml
                text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
        except Exception as exc:
            QMessageBox.critical(self, "metascrub", f"Could not save policy:\n{exc}")

    # -- running ---------------------------------------------------------
    def run_clean(self, dry_run: bool):
        root = self.root()
        if not root:
            QMessageBox.warning(self, "metascrub", "Choose a folder first.")
            return
        worker = Worker(scanner.clean, root, self.build_policy(), dry_run=dry_run)
        worker.done.connect(lambda results: self._on_results(results, dry_run))
        self._start(worker, [self.dry_btn, self.apply_btn], self.progress)

    def _confirm_apply(self):
        box = QMessageBox(self)
        box.setWindowTitle("metascrub")
        box.setIcon(QMessageBox.Warning)
        box.setText("Rewrite metadata in place for the selected folder?")
        box.setInformativeText(
            "Audio is never re-encoded and WAV writes are hash-verified, but the "
            "existing tags will be permanently replaced. Run a dry run first and "
            "review the diff if you haven't.")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        box.setDefaultButton(QMessageBox.Cancel)
        if box.exec() == QMessageBox.Yes:
            self.run_clean(dry_run=False)

    def _on_results(self, results, dry_run):
        self.results = results
        _populate_table(self.table, results)
        tail = "" if not dry_run else " — DRY RUN, nothing was written."
        if not dry_run:
            tail = " — applied. Run the Verify page to confirm nothing remains."
        self.summary.setText(_summarize(results) + tail)

    def save_report(self, path: str):
        text = render_text(self.results, dry_run=False)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)


# --------------------------------------------------------------------------
# Verify page
# --------------------------------------------------------------------------

class VerifyPage(_BusyPage):
    def __init__(self, root_provider):
        super().__init__(root_provider)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        bar = QHBoxLayout()
        self.verify_btn = QPushButton("Verify folder")
        self.verify_btn.setObjectName("accent")
        self.verify_btn.clicked.connect(self.run_verify)
        self.sigs = QLineEdit()
        self.sigs.setPlaceholderText("extra signatures, comma-separated (optional)")
        bar.addWidget(self.verify_btn)
        bar.addWidget(self.sigs, 1)
        lay.addLayout(bar)

        self.badge = QLabel("Not verified yet — run a check after cleaning.")
        self.badge.setObjectName("badgeIdle")
        self.badge.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.badge)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        lay.addWidget(self.progress)

        self.table = _make_table()
        lay.addWidget(self.table, 1)

    def run_verify(self):
        root = self.root()
        if not root:
            QMessageBox.warning(self, "metascrub", "Choose a folder first.")
            return
        policy = Policy()
        policy.extra_signatures.extend(
            s.strip().lower() for s in self.sigs.text().split(",") if s.strip())
        worker = Worker(scanner.verify, root, policy)
        worker.done.connect(self._on_results)
        self._start(worker, [self.verify_btn], self.progress)

    def _on_results(self, results):
        hits = [r for r in results if r.entries]
        _populate_table(self.table, [r for r in hits])
        n = sum(len(r.entries) for r in hits)
        if n == 0:
            self.badge.setText("✓  CLEAN — no provenance signatures found")
            self.badge.setObjectName("badgeOk")
        else:
            self.badge.setText(f"✗  {n} provenance signature(s) remain")
            self.badge.setObjectName("badgeBad")
        self.badge.style().unpolish(self.badge)
        self.badge.style().polish(self.badge)
