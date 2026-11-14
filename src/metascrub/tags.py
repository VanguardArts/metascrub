"""Shared constants: default strip lists and provenance signatures.

These defaults target the metadata fingerprints commonly embedded by AI music
services and file converters (Suno, Udio, ffmpeg re-muxes, etc.). Everything
here is configurable through a Policy.
"""
from __future__ import annotations

import os
import re

# ID3v2 frame IDs removed by default (prefix match, so "COMM" removes
# COMM::eng, COMM:iTunNORM:eng, ...; "TXXX" removes every user-defined frame).
DEFAULT_STRIP_ID3_FRAMES = [
    "COMM",   # comments ("made with suno; created=...; id=...")
    "USLT",   # unsynchronised lyrics (AI-generated lyric/prompt dumps)
    "SYLT",   # synchronised lyrics
    "GEOB",   # general encapsulated object (C2PA manifest store lives here)
    "WOAS",   # official audio source webpage (e.g. https://suno.com/song/<id>)
    "WXXX",   # user-defined URL link frames
    "TSSE",   # software/encoder fingerprint (e.g. Lavf60.16.100)
    "TENC",   # encoded-by
    "TXXX",   # user-defined text (major_brand/minor_version/compatible_brands/comment)
    "PRIV",   # private frames (watermark/owner IDs)
]

# RIFF chunk IDs removed entirely by default.
DEFAULT_STRIP_RIFF_CHUNKS = ["C2PA"]

# RIFF LIST INFO sub-codes removed by default (comment + software fingerprint).
DEFAULT_STRIP_RIFF_INFO = ["ICMT", "ISFT"]

# Case-insensitive substrings searched by `metascrub verify`. These are
# signatures of AI generation services, content-provenance manifests and
# converter fingerprints. Add your own via policy `extra_signatures`.
DEFAULT_SIGNATURES = [
    "suno",
    "udio",
    "stable audio",
    "mubert",
    "boomy",
    "aiva",
    "soundraw",
    "made with",
    "c2pa",
    "content credentials",
    "lavf",
]

_BRACKET_RE = re.compile(r"\[([^\]]+)\]")


def derive_genre(relpath: str, mode: str = "brackets", fixed: str | None = None):
    """Derive a per-track genre.

    mode="brackets": first ``[Genre]`` token in the filename, falling back to
                     the immediate parent directory (handles files renamed
                     without a genre bracket).
    mode="fixed":    always return ``fixed``.
    mode="none":     no genre.
    """
    if mode == "none":
        return None
    if mode == "fixed":
        return fixed or None
    m = _BRACKET_RE.search(os.path.basename(relpath))
    if m:
        return m.group(1).strip()
    m = _BRACKET_RE.search(os.path.basename(os.path.dirname(relpath)))
    return m.group(1).strip() if m else None
