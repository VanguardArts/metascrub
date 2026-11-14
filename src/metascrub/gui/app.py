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
    window.auto_tutorial_if_first_launch()
    exit_code = app.exec()
    # Destroy the window while the QApplication is still fully alive.
    # Signal connections on child widgets capture the window, forming
    # reference cycles that CPython's GC cannot see through C++; without
    # this the window can leak into interpreter shutdown, where PySide6's
    # global cleanup would tear it down in a bad state.
    window.deleteLater()
    app.sendPostedEvents(None, 0)
    app.processEvents()
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
