"""Main window: header (folder picker), sidebar nav, stacked pages, status bar."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from .pages import CleanPage, ScanPage, VerifyPage

_ICON = Path(__file__).parent / "assets" / "icon.svg"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"metascrub {__version__}")
        if _ICON.exists():
            self.setWindowIcon(QIcon(str(_ICON)))
        self.resize(1180, 780)

        self._settings = QSettings("metascrub", "metascrub")

        central = QWidget()
        self.setCentralWidget(central)
        root_lay = QVBoxLayout(central)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ---- header ---------------------------------------------------
        header = QFrame()
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 12, 16, 12)
        h.setSpacing(10)

        icon_lbl = QLabel("◈")
        icon_lbl.setObjectName("appIcon")
        title = QLabel("metascrub")
        title.setObjectName("appTitle")
        subtitle = QLabel("byte-safe audio metadata hygiene")
        subtitle.setStyleSheet("color: #54647a;")

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Audio folder to work on…")
        self.path_edit.setText(self._settings.value("last_folder", ""))
        self.path_edit.textChanged.connect(
            lambda t: self._settings.setValue("last_folder", t))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)

        h.addWidget(icon_lbl)
        h.addWidget(title)
        h.addWidget(subtitle)
        h.addSpacing(24)
        h.addWidget(QLabel("Folder:"))
        h.addWidget(self.path_edit, 1)
        h.addWidget(browse)
        root_lay.addWidget(header)

        # ---- body -----------------------------------------------------
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root_lay.addLayout(body, 1)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(170)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(8, 14, 8, 8)
        side.setSpacing(2)

        self.stack = QStackedWidget()
        self.pages = [
            ScanPage(self.root_path),
            CleanPage(self.root_path),
            VerifyPage(self.root_path),
        ]
        self.nav_buttons = []
        names = [("🔍", "Scan"), ("✨", "Clean"), ("✔", "Verify")]
        for i, (glyph, name) in enumerate(names):
            btn = QToolButton()
            btn.setObjectName("nav")
            btn.setText(f"{glyph}  {name}")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            btn.clicked.connect(lambda _c, idx=i: self.stack.setCurrentIndex(idx))
            side.addWidget(btn)
            self.nav_buttons.append(btn)
            self.stack.addWidget(self.pages[i])
        self.nav_buttons[0].setChecked(True)

        side.addStretch(1)
        ver = QLabel(f"v{__version__}")
        ver.setObjectName("version")
        side.addWidget(ver)

        body.addWidget(sidebar)
        body.addWidget(self.stack, 1)

        self.statusBar().showMessage("Ready")

        for page in self.pages:
            if isinstance(page, ScanPage):
                page.scan_btn.clicked.connect(
                    lambda: self.statusBar().showMessage("Scanning…"))
            if isinstance(page, VerifyPage):
                page.verify_btn.clicked.connect(
                    lambda: self.statusBar().showMessage("Verifying…"))

    def root_path(self) -> str:
        return self.path_edit.text()

    def _browse(self):
        start = self.path_edit.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Choose audio folder", start)
        if folder:
            self.path_edit.setText(folder)
