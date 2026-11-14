"""Palette-driven dark themes + shared colors.

Eight variants: seven accent colors (Tidal, Azure, Violet, Orchid, Amber,
Emerald, Coral) plus a neutral Slate/Anthracite. apply_theme() swaps the
stylesheet; icon_svg() follows the active palette so the icon always matches.
"""
from __future__ import annotations

from string import Template

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

# Structural palette shared by all accent themes (deep blue-tinted dark).
_BASE = {
    "bg": "#0e1116",
    "text": "#e6edf3",
    "surface": "#141a24",
    "surface2": "#11161f",
    "border": "#263248",
    "border_soft": "#2a3548",
    "border_strong": "#37506e",
    "hover": "#1a2230",
    "active": "#1f2a3d",
    "button_hover": "#263449",
    "pressed": "#182130",
    "disabled_bg": "#182030",
    "disabled_bd": "#223047",
    "disabled_fg": "#5a6675",
    "input_bg": "#151d2a",
    "table_bg": "#10151d",
    "table_alt": "#141b27",
    "dim": "#54647a",
    "muted": "#8b98a9",
    "subtle": "#9fb0c3",
    "danger": DANGER,
    "success": SUCCESS,
    "warn": WARN,
    "danger_bg": "#3b1d26",
    "danger_bd": "#6b2a38",
    "danger_hover": "#4a222d",
    "ok_bg": "#10312a",
    "ok_bd": "#1c5b4a",
}

_THEMES = {
    "tidal": {
        "label": "Tidal (Cyan)",
        "colors": {
            "accent": "#22d3ee", "accent_hover": "#67e8f9",
            "accent_pressed": "#0e7490", "accent_text": "#062731",
            "icon_alt": "#2dd4bf",
        },
    },
    "azure": {
        "label": "Azure (Blue)",
        "colors": {
            "accent": "#60a5fa", "accent_hover": "#93c5fd",
            "accent_pressed": "#1d4ed8", "accent_text": "#0b1c3d",
            "icon_alt": "#38bdf8",
        },
    },
    "violet": {
        "label": "Violet",
        "colors": {
            "accent": "#a78bfa", "accent_hover": "#c4b5fd",
            "accent_pressed": "#6d28d9", "accent_text": "#1e1340",
            "icon_alt": "#8b5cf6",
        },
    },
    "orchid": {
        "label": "Orchid (Pink)",
        "colors": {
            "accent": "#f472b6", "accent_hover": "#f9a8d4",
            "accent_pressed": "#be185d", "accent_text": "#3d0a24",
            "icon_alt": "#e879f9",
        },
    },
    "amber": {
        "label": "Amber",
        "colors": {
            "accent": "#fbbf24", "accent_hover": "#fcd34d",
            "accent_pressed": "#b45309", "accent_text": "#3a2703",
            "icon_alt": "#f59e0b",
        },
    },
    "emerald": {
        "label": "Emerald",
        "colors": {
            "accent": "#34d399", "accent_hover": "#6ee7b7",
            "accent_pressed": "#047857", "accent_text": "#03291d",
            "icon_alt": "#10b981",
        },
    },
    "coral": {
        "label": "Coral (Red)",
        "colors": {
            "accent": "#f87171", "accent_hover": "#fca5a5",
            "accent_pressed": "#b91c1c", "accent_text": "#3b0f0f",
            "icon_alt": "#fb923c",
        },
    },
    "slate": {
        "label": "Slate / Anthracite",
        "colors": {
            "accent": "#94a3b8", "accent_hover": "#cbd5e1",
            "accent_pressed": "#475569", "accent_text": "#10141a",
            "icon_alt": "#64748b",
            # anthracite structure: neutral grays, no blue tint
            "bg": "#17191c", "text": "#e8eaed",
            "surface": "#1f2226", "surface2": "#1b1e22",
            "border": "#33373e", "border_soft": "#363b43",
            "border_strong": "#4a5058",
            "hover": "#25292f", "active": "#2a2f36",
            "button_hover": "#2e343c", "pressed": "#16181b",
            "disabled_bg": "#1d2024", "disabled_bd": "#2b2f36",
            "disabled_fg": "#646b74",
            "input_bg": "#21252b", "table_bg": "#15171a",
            "table_alt": "#1b1e22",
            "dim": "#6f767f", "muted": "#9aa3ad", "subtle": "#b6bec7",
        },
    },
}

DEFAULT_THEME = "tidal"
_CURRENT = DEFAULT_THEME

_QSS_TEMPLATE = Template("""
QMainWindow, QWidget { background: $bg; color: $text; font-size: 13px; }
QFrame#header { background: $surface; border-bottom: 1px solid $border; }
QLabel#appTitle { font-size: 17px; font-weight: 700; }
QLabel#appIcon { color: $accent; font-size: 20px; }
QFrame#sidebar { background: $surface2; border-right: 1px solid $border; }
QToolButton#nav {
    color: $muted; border: none; padding: 10px 16px; text-align: left;
    border-radius: 8px; font-weight: 600; font-size: 13px;
}
QToolButton#nav:hover { background: $hover; color: $text; }
QToolButton#nav:checked { background: $active; color: $accent; }
QLabel#version { color: $dim; font-size: 11px; padding: 10px 16px; }

QPushButton {
    background: $active; color: $text; border: 1px solid $border_soft;
    border-radius: 8px; padding: 8px 16px; font-weight: 600;
}
QPushButton:hover { background: $button_hover; border-color: $border_strong; }
QPushButton:pressed { background: $pressed; }
QPushButton:disabled { color: $disabled_fg; background: $disabled_bg; border-color: $disabled_bd; }
QPushButton#accent { background: $accent; color: $accent_text; border: none; }
QPushButton#accent:hover { background: $accent_hover; }
QPushButton#accent:pressed { background: $accent_pressed; }
QPushButton#danger { background: $danger_bg; color: $danger; border: 1px solid $danger_bd; }
QPushButton#danger:hover { background: $danger_hover; }

QLineEdit, QComboBox {
    background: $input_bg; border: 1px solid $border_soft; border-radius: 8px;
    padding: 7px 10px; selection-background-color: $accent; selection-color: $accent_text;
}
QLineEdit:focus, QComboBox:focus { border-color: $accent; }
QComboBox QAbstractItemView {
    background: $input_bg; border: 1px solid $border_soft;
    selection-background-color: $accent; selection-color: $accent_text;
}
QComboBox::drop-down { border: none; width: 26px; }

QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid $border_soft; background: $input_bg;
}
QCheckBox::indicator:checked { background: $accent; border-color: $accent; }

QTableWidget {
    background: $table_bg; alternate-background-color: $table_alt;
    gridline-color: $disabled_bd; border: 1px solid $border; border-radius: 10px;
}
QHeaderView::section {
    background: $surface; color: $muted; border: none;
    border-bottom: 1px solid $border; padding: 8px; font-weight: 700; font-size: 11px;
}
QTableWidget::item { padding: 6px; border: none; }
QTableWidget::item:selected { background: $active; }

QProgressBar {
    background: $input_bg; border: 1px solid $border_soft; border-radius: 7px;
    height: 14px; text-align: center; color: $muted; font-size: 11px;
}
QProgressBar::chunk { background: $accent; border-radius: 6px; }

QGroupBox {
    border: 1px solid $border; border-radius: 10px; margin-top: 16px;
    padding-top: 14px; font-weight: 700; color: $subtle;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }

QLabel#badgeOk {
    background: $ok_bg; color: $success; border: 1px solid $ok_bd;
    border-radius: 12px; padding: 18px; font-size: 20px; font-weight: 800;
}
QLabel#badgeBad {
    background: $danger_bg; color: $danger; border: 1px solid $danger_bd;
    border-radius: 12px; padding: 18px; font-size: 20px; font-weight: 800;
}
QLabel#badgeIdle {
    background: $input_bg; color: $muted; border: 1px solid $border_soft;
    border-radius: 12px; padding: 18px; font-size: 16px; font-weight: 600;
}
QLabel#summary { color: $subtle; font-weight: 600; padding: 4px 2px; }
QLabel#progress { color: $muted; font-size: 11px; padding: 0 2px; }

QStatusBar { background: $surface2; color: $muted; border-top: 1px solid $border; }
QToolTip { background: $hover; color: $text; border: 1px solid $border_soft; padding: 6px; }
QMessageBox { background: $bg; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $border_soft; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: $border_strong; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: $border_soft; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QToolButton#places {
    background: $active; color: $text; border: 1px solid $border_soft;
    border-radius: 8px; padding: 7px 12px; font-weight: 600;
}
QToolButton#places:hover { background: $button_hover; border-color: $border_strong; }
QToolButton#places::menu-indicator { image: none; width: 0; }
QMenu {
    background: $surface; color: $text; border: 1px solid $border_soft;
    border-radius: 8px; padding: 4px;
}
QMenu::item { padding: 7px 22px; border-radius: 5px; }
QMenu::item:selected { background: $active; color: $accent; }

QLabel#tutTitle { font-size: 21px; font-weight: 800; color: $text; }
QLabel#tutBody { color: $subtle; font-size: 14px; }
QLabel#tutBody b { color: $text; }
QLabel#tutDots { font-size: 13px; }
""")

_ICON_TEMPLATE = Template("""<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect x="4" y="4" width="120" height="120" rx="26" fill="$surface"/>
  <rect x="4" y="4" width="120" height="120" rx="26" fill="none" stroke="$border" stroke-width="2"/>
  <rect x="26" y="54" width="10" height="20" rx="5" fill="$accent"/>
  <rect x="42" y="40" width="10" height="48" rx="5" fill="$icon_alt"/>
  <rect x="58" y="26" width="10" height="76" rx="5" fill="$accent"/>
  <rect x="74" y="46" width="10" height="36" rx="5" fill="$icon_alt"/>
  <rect x="90" y="58" width="10" height="12" rx="5" fill="$accent"/>
</svg>""")


def theme_names():
    return list(_THEMES)


def theme_label(key: str) -> str:
    return _THEMES[key]["label"]


def palette(key: str = None) -> dict:
    p = dict(_BASE)
    p.update(_THEMES[key or _CURRENT]["colors"])
    return p


def qss(key: str = None) -> str:
    return _QSS_TEMPLATE.substitute(palette(key))


def icon_svg(key: str = None) -> str:
    return _ICON_TEMPLATE.substitute(palette(key))


def current_theme() -> str:
    return _CURRENT


def apply_theme(app, key: str = None) -> None:
    global _CURRENT
    if key in _THEMES:
        _CURRENT = key
    app.setStyleSheet(qss(_CURRENT))


# Backwards-compatible constants (default theme).
ACCENT = _THEMES[DEFAULT_THEME]["colors"]["accent"]
ACCENT_HOVER = _THEMES[DEFAULT_THEME]["colors"]["accent_hover"]
QSS = qss(DEFAULT_THEME)
ICON_SVG = icon_svg(DEFAULT_THEME)
