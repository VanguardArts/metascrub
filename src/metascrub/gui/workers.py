"""Background workers: run the (blocking) core pipeline off the UI thread."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """Run a scanner function (scan/clean/verify) in a thread.

    Signals:
        progressed(current, total, relpath)
        done(list[FileResult])
        failed(str)
    """

    progressed = Signal(int, int, str)
    done = Signal(list)
    failed = Signal(str)

    def __init__(self, fn: Callable, root: str, policy, parent=None, **kwargs):
        super().__init__(parent)
        self._fn = fn
        self._root = root
        self._policy = policy
        self._kwargs = kwargs

    def run(self):  # noqa: D401 - thread entry point
        try:
            results = self._fn(
                self._root,
                self._policy,
                progress=lambda i, n, rel: self.progressed.emit(i, n, rel),
                **self._kwargs,
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.failed.emit(str(exc))
            return
        self.done.emit(results)
