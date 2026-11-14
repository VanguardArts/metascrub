"""Format adapter interface.

An adapter knows how to inspect one container family (list every embedded
tag/chunk with a predicted action) and how to clean it (strip + set) without
ever re-encoding audio.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..policy import Policy
from ..report import FileResult


@dataclass
class Derived:
    """Per-file values computed by the scanner from policy + path."""
    title: Optional[str] = None
    genre: Optional[str] = None
    album: Optional[str] = None


class FormatAdapter:
    name: str = "?"
    extensions: tuple = ()

    def inspect(self, path: str, relpath: str, policy: Policy) -> FileResult:
        raise NotImplementedError

    def clean(self, path: str, relpath: str, policy: Policy,
              derived: Derived, dry_run: bool) -> FileResult:
        raise NotImplementedError
