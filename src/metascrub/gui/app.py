"""GUI entry point:  metascrub-gui  (or:  python -m metascrub.gui)."""
from __future__ import annotations

import sys
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("The metascrub GUI needs PySide6:  pip install metascrub[gui]",
              file=sys.stderr)
        return 2

    from PySide6.QtCore import QSettings

    from .. import __version__
    from .main_window import MainWindow, app_icon
    from .theme import DEFAULT_THEME, apply_theme

    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("metascrub")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("metascrub")
    saved_theme = QSettings("metascrub", "metascrub").value(
        "theme", DEFAULT_THEME)
    apply_theme(app, saved_theme)
    app.setWindowIcon(app_icon())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
