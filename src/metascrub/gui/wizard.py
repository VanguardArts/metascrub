"""First-launch tutorial dialog - also summonable anytime from the sidebar.

A small custom paged dialog (not QWizard) so it follows the active theme
exactly: accent page dots, palette-driven colors, Back/Next/Finish.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .theme import palette

PAGES = [
    ("Welcome to metascrub",
     "<b>metascrub</b> scrubs audio metadata - generator comments, lyric "
     "dumps, C2PA manifests, origin URLs, encoder fingerprints, cover art - "
     "and applies your own clean credits.<br><br>"
     "It <b>never re-encodes audio</b>: writes are atomic and the audio "
     "payload is hash-verified byte-for-byte after every change.<br><br>"
     "The workflow is a simple loop:<br><b>Scan &rarr; Clean &rarr; "
     "Verify</b>"),
    ("1 · Pick a folder",
     "Use the <b>Folder</b> field in the header:<br><br>"
     "&bull; <b>Places &#9662;</b> jumps to Home, Computer, or any mounted "
     "drive (USB, HDD, VeraCrypt&hellip;)<br>"
     "&bull; <b>Browse&hellip;</b> opens a folder picker<br>"
     "&bull; or just paste a path<br><br>"
     "Your last folder is remembered between launches."),
    ("2 · Scan",
     "<b>Scan</b> lists every embedded tag and chunk found in the folder "
     "tree.<br><br>"
     "Rows marked <b>strip</b> (red) are what a clean would remove; "
     "<b>set</b> (green) are credits that would be written; <b>keep</b> "
     "stays untouched.<br><br>"
     "Use the filter box to search files, tags or values.<br><br>"
     "One-click option: after a scan, <b>&#10024; Auto-clean</b> strips "
     "everything flagged, applies the Clean page credits and re-scans - "
     "with a single confirmation."),
    ("3 · Clean",
     "Fill in your credits on the <b>Clean</b> page - artist, composer, "
     "label, copyright, year, album.<br><br>"
     "Always run a <b>Dry run</b> first: nothing is written and you review "
     "the full diff. Then <b>Apply changes</b>.<br><br>"
     "<b>Save policy&hellip;</b> stores the whole form as YAML/JSON so you "
     "can reload it later or reuse it with the CLI.<br><br>"
     "Two safety extras: <b>Extra signatures</b> makes Verify hunt your own "
     "strings (old usernames, project names), and <b>Remove credit tags with "
     "no replacement</b> deletes stale credits even when a field is left "
     "empty."),
    ("4 · Verify",
     "<b>Verify</b> proves nothing revealing remains - a green badge means "
     "the folder is clean.<br><br>"
     "Automation tip: <i>metascrub verify &lt;folder&gt;</i> exits 1 if any "
     "provenance signature is left, which makes it a handy CI gate."),
    ("You're all set",
     "Reopen this tutorial anytime via the <b>Tutorial</b> button at the "
     "bottom of the sidebar.<br><br>"
     "CLI quick reference:<br>"
     "<i>metascrub scan &lt;folder&gt;</i><br>"
     "<i>metascrub clean &lt;folder&gt; --policy policy.yaml --apply</i><br>"
     "<i>metascrub verify &lt;folder&gt;</i><br><br>"
     "Happy scrubbing!"),
]


class TutorialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("metascrub tutorial")
        self.setModal(True)
        self.resize(640, 440)
        self._page = 0

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(14)

        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("tutTitle")
        lay.addWidget(self.title_lbl)

        self.body_lbl = QLabel()
        self.body_lbl.setObjectName("tutBody")
        self.body_lbl.setWordWrap(True)
        self.body_lbl.setTextFormat(Qt.TextFormat.RichText)
        self.body_lbl.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(self.body_lbl, 1)

        footer = QHBoxLayout()
        self.dots_lbl = QLabel()
        self.dots_lbl.setObjectName("tutDots")
        footer.addWidget(self.dots_lbl)
        footer.addStretch(1)

        self.skip_btn = QPushButton("Skip")
        self.skip_btn.clicked.connect(self.reject)
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.back)
        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("accent")
        self.next_btn.setDefault(True)
        self.next_btn.clicked.connect(self.next)
        footer.addWidget(self.skip_btn)
        footer.addWidget(self.back_btn)
        footer.addWidget(self.next_btn)
        lay.addLayout(footer)

        self._show(0)

    def _show(self, index: int):
        self._page = index
        title, body = PAGES[index]
        self.title_lbl.setText(title)
        self.body_lbl.setText(body)

        pal = palette()
        dots = []
        for i in range(len(PAGES)):
            color = pal["accent"] if i == index else pal["dim"]
            glyph = "&#9679;" if i == index else "&#9675;"
            dots.append(f'<span style="color:{color}">{glyph}</span>')
        self.dots_lbl.setText(" ".join(dots))

        self.back_btn.setEnabled(index > 0)
        self.next_btn.setText("Finish" if index == len(PAGES) - 1 else "Next")

    def next(self):
        if self._page == len(PAGES) - 1:
            self.accept()
        else:
            self._show(self._page + 1)

    def back(self):
        if self._page > 0:
            self._show(self._page - 1)
