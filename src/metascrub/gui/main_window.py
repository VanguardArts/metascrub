"""Main window: header (folder picker), sidebar nav, stacked pages, status bar."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings, Qt, QTimer
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from .pages import CleanPage, ScanPage, VerifyPage
from .places import mounted_places
from .theme import (current_theme, icon_svg, theme_label, theme_names,
                    apply_theme)
from .wizard import TutorialDialog


def app_icon(size: int = 128) -> QIcon:
    """Render the embedded SVG icon in the active theme's palette."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(icon_svg().encode("utf-8")))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"metascrub {__version__}")
        self.setWindowIcon(app_icon())
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

        self.icon_lbl = QLabel()
        self.icon_lbl.setObjectName("appIcon")
        self.icon_lbl.setPixmap(app_icon(30).pixmap(30, 30))
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

        self.places_menu = QMenu(self)
        self.places_menu.aboutToShow.connect(self._fill_places)
        places_btn = QToolButton()
        places_btn.setObjectName("places")
        places_btn.setText("Places ▾")
        places_btn.setToolTip(
            "Jump to Home, Computer, or a mounted drive (USB, HDD, VeraCrypt…)")
        places_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        places_btn.setMenu(self.places_menu)

        h.addWidget(self.icon_lbl)
        h.addWidget(title)
        h.addWidget(subtitle)
        h.addSpacing(24)
        h.addWidget(QLabel("Folder:"))
        h.addWidget(self.path_edit, 1)
        h.addWidget(places_btn)
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
        self.tutorial_btn = QPushButton("💡 Tutorial")
        self.tutorial_btn.clicked.connect(self.show_tutorial)
        side.addWidget(self.tutorial_btn)
        theme_lbl = QLabel("Theme")
        theme_lbl.setObjectName("version")
        side.addWidget(theme_lbl)
        self.theme_combo = QComboBox()
        for key in theme_names():
            self.theme_combo.addItem(theme_label(key), key)
        self.theme_combo.setCurrentIndex(
            self.theme_combo.findData(current_theme()))
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        side.addWidget(self.theme_combo)
        ver = QLabel(f"v{__version__}")
        ver.setObjectName("version")
        side.addWidget(ver)

        body.addWidget(sidebar)
        body.addWidget(self.stack, 1)

        self.statusBar().showMessage("Ready")

        if not self._settings.value("tutorial_seen", False, type=bool):
            QTimer.singleShot(400, self.show_tutorial)

        for page in self.pages:
            if isinstance(page, ScanPage):
                page.scan_btn.clicked.connect(
                    lambda: self.statusBar().showMessage("Scanning…"))
            if isinstance(page, VerifyPage):
                page.verify_btn.clicked.connect(
                    lambda: self.statusBar().showMessage("Verifying…"))

    def root_path(self) -> str:
        return self.path_edit.text()

    def show_tutorial(self):
        dlg = TutorialDialog(self)
        dlg.exec()
        self._settings.setValue("tutorial_seen", True)

    def _on_theme_changed(self, index: int):
        key = self.theme_combo.itemData(index)
        if not key or key == current_theme():
            return
        self._settings.setValue("theme", key)
        app = QApplication.instance()
        apply_theme(app, key)
        self._refresh_icons()

    def _refresh_icons(self):
        icon = app_icon()
        self.setWindowIcon(icon)
        self.icon_lbl.setPixmap(app_icon(30).pixmap(30, 30))
        QApplication.instance().setWindowIcon(icon)

    def _fill_places(self):
        """Rebuild the Places menu live so freshly mounted drives appear."""
        self.places_menu.clear()
        for place in mounted_places():
            act = self.places_menu.addAction(f"{place.label}  —  {place.path}")
            if place.detail:
                act.setToolTip(place.detail)
                act.setStatusTip(place.detail)
            act.triggered.connect(
                lambda _checked=False, p=place.path: self.path_edit.setText(p))

    def _browse(self):
        start = self.path_edit.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Choose audio folder", start)
        if folder:
            self.path_edit.setText(folder)
