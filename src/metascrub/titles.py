"""Title derivation: build a clean track title from a filename.

Filenames are treated as authoritative because embedded titles are often
stale (renames) or polluted with service prefixes. Typical source form::

    Label Name - [Genre] - Track Name [Edition] (2026) vN.mp3

Rules strip, in order: the extension, a leading label prefix, a leading
``[Genre] - `` bracket, any ``(YYYY)`` year, and collapse whitespace.
Edition/version markers (``[Original Edition]``, ``v2``, ``[Rework]``...)
are preserved because they distinguish distinct releases.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

_EXT_RE = re.compile(r"\.[A-Za-z0-9]{1,5}$")
# First bracketed "[Genre] - " token, wherever it appears. Edition brackets
# like "[Helios Edition]" are safe: they are followed by " (YYYY)"/end, not " - ".
_GENRE_BRACKET_RE = re.compile(r"\[[^\]]+\]\s*-\s*")
_YEAR_RE = re.compile(r"\s*\(\d{4}\)")
_WS_RE = re.compile(r"\s+")


@dataclass
class TitleRules:
    enabled: bool = True
    # Leading label prefix to strip, e.g. "Example Records - " (exact match).
    strip_label_prefix: Optional[str] = None
    # Strip the first "[Genre] - " bracket token.
    strip_genre_bracket: bool = True
    # Strip bare "Genre - " prefixes for these tokens (case-insensitive),
    # e.g. ["DnB", "Speed Garage"] to catch "DnB - Neon Skyline" style names.
    strip_genre_prefixes: List[str] = field(default_factory=list)
    # Strip any "(YYYY)" year marker.
    strip_year_suffix: bool = True

    def derive(self, filename: str) -> str:
        """Derive the clean title from a filename (extension optional)."""
        stem = _EXT_RE.sub("", filename)
        if self.strip_label_prefix and stem.startswith(self.strip_label_prefix):
            stem = stem[len(self.strip_label_prefix):]
        if self.strip_genre_bracket:
            stem = _GENRE_BRACKET_RE.sub("", stem, count=1)
        for token in self.strip_genre_prefixes:
            stem = re.sub(
                r"^" + re.escape(token) + r"\s*-\s*", "", stem,
                count=1, flags=re.IGNORECASE,
            )
        if self.strip_year_suffix:
            stem = _YEAR_RE.sub(" ", stem)
        return _WS_RE.sub(" ", stem).strip()
