"""Dark theme stylesheet + shared colors."""

ACCENT = "#22d3ee"
ACCENT_HOVER = "#67e8f9"
DANGER = "#f87171"
SUCCESS = "#34d399"
WARN = "#fbbf24"
MUTED = "#8b98a9"

ACTION_COLORS = {
    "strip": DANGER,
    "set": SUCCESS,
    "keep": MUTED,
    "skip": WARN,
    "error": DANGER,
}

QSS = """
QMainWindow, QWidget { background: #0e1116; color: #e6edf3; font-size: 13px; }
QFrame#header { background: #141a24; border-bottom: 1px solid #263248; }
QLabel#appTitle { font-size: 17px; font-weight: 700; }
QLabel#appIcon { color: #22d3ee; font-size: 20px; }
QFrame#sidebar { background: #11161f; border-right: 1px solid #263248; }
QToolButton#nav {
    color: #8b98a9; border: none; padding: 10px 16px; text-align: left;
    border-radius: 8px; font-weight: 600; font-size: 13px;
}
QToolButton#nav:hover { background: #1a2230; color: #e6edf3; }
QToolButton#nav:checked { background: #1f2a3d; color: #22d3ee; }
QLabel#version { color: #54647a; font-size: 11px; padding: 10px 16px; }

QPushButton {
    background: #1f2a3d; color: #e6edf3; border: 1px solid #2a3548;
    border-radius: 8px; padding: 8px 16px; font-weight: 600;
}
QPushButton:hover { background: #263449; border-color: #37506e; }
QPushButton:pressed { background: #182130; }
QPushButton:disabled { color: #5a6675; background: #182030; border-color: #223047; }
QPushButton#accent { background: #22d3ee; color: #062731; border: none; }
QPushButton#accent:hover { background: #67e8f9; }
QPushButton#accent:pressed { background: #0e7490; }
QPushButton#danger { background: #3b1d26; color: #f87171; border: 1px solid #6b2a38; }
QPushButton#danger:hover { background: #4a222d; }

QLineEdit, QComboBox {
    background: #151d2a; border: 1px solid #2a3548; border-radius: 8px;
    padding: 7px 10px; selection-background-color: #22d3ee; selection-color: #062731;
}
QLineEdit:focus, QComboBox:focus { border-color: #22d3ee; }
QComboBox QAbstractItemView {
    background: #151d2a; border: 1px solid #2a3548;
    selection-background-color: #22d3ee; selection-color: #062731;
}
QComboBox::drop-down { border: none; width: 26px; }

QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid #2a3548; background: #151d2a;
}
QCheckBox::indicator:checked { background: #22d3ee; border-color: #22d3ee; }

QTableWidget {
    background: #10151d; alternate-background-color: #141b27;
    gridline-color: #223047; border: 1px solid #263248; border-radius: 10px;
}
QHeaderView::section {
    background: #141a24; color: #8b98a9; border: none;
    border-bottom: 1px solid #263248; padding: 8px; font-weight: 700; font-size: 11px;
}
QTableWidget::item { padding: 6px; border: none; }
QTableWidget::item:selected { background: #1f2a3d; }

QProgressBar {
    background: #151d2a; border: 1px solid #2a3548; border-radius: 7px;
    height: 14px; text-align: center; color: #8b98a9; font-size: 11px;
}
QProgressBar::chunk { background: #22d3ee; border-radius: 6px; }

QGroupBox {
    border: 1px solid #263248; border-radius: 10px; margin-top: 16px;
    padding-top: 14px; font-weight: 700; color: #9fb0c3;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }

QLabel#badgeOk {
    background: #10312a; color: #34d399; border: 1px solid #1c5b4a;
    border-radius: 12px; padding: 18px; font-size: 20px; font-weight: 800;
}
QLabel#badgeBad {
    background: #3b1d26; color: #f87171; border: 1px solid #6b2a38;
    border-radius: 12px; padding: 18px; font-size: 20px; font-weight: 800;
}
QLabel#badgeIdle {
    background: #151d2a; color: #8b98a9; border: 1px solid #2a3548;
    border-radius: 12px; padding: 18px; font-size: 16px; font-weight: 600;
}
QLabel#summary { color: #9fb0c3; font-weight: 600; padding: 4px 2px; }

QStatusBar { background: #11161f; color: #8b98a9; border-top: 1px solid #263248; }
QToolTip { background: #1a2230; color: #e6edf3; border: 1px solid #2a3548; padding: 6px; }
QMessageBox { background: #0e1116; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #2a3548; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #37506e; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: #2a3548; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QToolButton#places {
    background: #1f2a3d; color: #e6edf3; border: 1px solid #2a3548;
    border-radius: 8px; padding: 7px 12px; font-weight: 600;
}
QToolButton#places:hover { background: #263449; border-color: #37506e; }
QToolButton#places::menu-indicator { image: none; width: 0; }
QMenu {
    background: #141a24; color: #e6edf3; border: 1px solid #2a3548;
    border-radius: 8px; padding: 4px;
}
QMenu::item { padding: 7px 22px; border-radius: 5px; }
QMenu::item:selected { background: #1f2a3d; color: #22d3ee; }
"""

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect x="4" y="4" width="120" height="120" rx="26" fill="#141a24"/>
  <rect x="4" y="4" width="120" height="120" rx="26" fill="none" stroke="#263248" stroke-width="2"/>
  <rect x="26" y="54" width="10" height="20" rx="5" fill="#22d3ee"/>
  <rect x="42" y="40" width="10" height="48" rx="5" fill="#2dd4bf"/>
  <rect x="58" y="26" width="10" height="76" rx="5" fill="#22d3ee"/>
  <rect x="74" y="46" width="10" height="36" rx="5" fill="#2dd4bf"/>
  <rect x="90" y="58" width="10" height="12" rx="5" fill="#22d3ee"/>
</svg>"""


def apply_theme(app) -> None:
    app.setStyleSheet(QSS)
