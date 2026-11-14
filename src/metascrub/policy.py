"""Policy: what metascrub strips, what it sets, and how it derives values.

A Policy can be loaded from a YAML or JSON file (``--policy``) and then
overridden by CLI flags. Every field has a sane default so a bare
``metascrub clean <path> --apply`` does something sensible.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .tags import (
    DEFAULT_SIGNATURES,
    DEFAULT_STRIP_ID3_FRAMES,
    DEFAULT_STRIP_RIFF_CHUNKS,
    DEFAULT_STRIP_RIFF_INFO,
)
from .titles import TitleRules


@dataclass
class Credits:
    """Uniform credits applied to every processed track."""
    artist: Optional[str] = None
    album_artist: Optional[str] = None   # defaults to artist when None
    composer: Optional[str] = None       # production credit
    label: Optional[str] = None          # publisher (MP3 only; RIFF INFO has no field)
    copyright: Optional[str] = None
    year: Optional[str] = None
    album: Optional[str] = None          # release/album name
    # Album is applied only to files whose path (relative to the scan root)
    # sits under this sub-directory. Singles get no album tag.
    release_subdir: Optional[str] = None

    def album_for(self, relpath: str) -> Optional[str]:
        if not self.album:
            return None
        if not self.release_subdir:
            return self.album
        return self.album if relpath.startswith(self.release_subdir + os.sep) else None


@dataclass
class Policy:
    credits: Credits = field(default_factory=Credits)
    titles: TitleRules = field(default_factory=TitleRules)
    genre_mode: str = "brackets"          # brackets | fixed | none
    genre_fixed: Optional[str] = None
    remove_cover_art: bool = True
    # Evict credit frames (artist, album, composer, label, copyright, year)
    # even when the policy has no replacement value for them, so stale or
    # revealing credits can never survive a clean.
    remove_unset_credits: bool = False
    strip_id3_frames: List[str] = field(default_factory=lambda: list(DEFAULT_STRIP_ID3_FRAMES))
    strip_riff_chunks: List[str] = field(default_factory=lambda: list(DEFAULT_STRIP_RIFF_CHUNKS))
    strip_riff_info: List[str] = field(default_factory=lambda: list(DEFAULT_STRIP_RIFF_INFO))
    exclude: List[str] = field(default_factory=list)   # regexes matched against relpath
    extra_signatures: List[str] = field(default_factory=list)

    # -- helpers ---------------------------------------------------------
    def is_excluded(self, relpath: str) -> bool:
        return any(re.search(rx, relpath) for rx in self.exclude)

    def signatures(self) -> List[str]:
        return [s.lower() for s in DEFAULT_SIGNATURES + self.extra_signatures]

    def matches_signature(self, text: str) -> bool:
        t = text.lower()
        return any(sig in t for sig in self.signatures())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict (JSON/YAML-safe), for policy files."""
        return {
            "credits": asdict(self.credits),
            "titles": asdict(self.titles),
            "genre_mode": self.genre_mode,
            "genre_fixed": self.genre_fixed,
            "remove_cover_art": self.remove_cover_art,
            "remove_unset_credits": self.remove_unset_credits,
            "strip_id3_frames": list(self.strip_id3_frames),
            "strip_riff_chunks": list(self.strip_riff_chunks),
            "strip_riff_info": list(self.strip_riff_info),
            "exclude": list(self.exclude),
            "extra_signatures": list(self.extra_signatures),
        }

    # -- (de)serialisation ------------------------------------------------
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Policy":
        d = dict(d or {})
        credits = Credits(**_filter(d.pop("credits", {}), Credits))
        titles = TitleRules(**_filter(d.pop("titles", {}), TitleRules))
        p = cls(credits=credits, titles=titles)
        for k, v in d.items():
            if hasattr(p, k):
                setattr(p, k, v)
        return p

    @classmethod
    def load(cls, path: str) -> "Policy":
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        if path.lower().endswith((".yaml", ".yml")):
            try:
                import yaml  # soft dependency
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "YAML policies need PyYAML: pip install metascrub[yaml]"
                ) from exc
            return cls.from_dict(yaml.safe_load(text))
        return cls.from_dict(json.loads(text))


def _filter(d: Dict[str, Any], cls) -> Dict[str, Any]:
    """Drop unknown keys so a typo in a policy file fails visibly (KeyError)."""
    known = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
    unknown = set(d) - known
    if unknown:
        raise KeyError(f"Unknown {cls.__name__} keys: {sorted(unknown)}")
    return d
