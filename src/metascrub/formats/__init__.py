"""Adapter registry. Add new format adapters here."""
from .base import Derived, FormatAdapter
from .mp3 import MP3Adapter
from .wav import WAVAdapter

ADAPTERS = [MP3Adapter(), WAVAdapter()]


def adapter_for(path: str):
    low = path.lower()
    for adapter in ADAPTERS:
        if low.endswith(adapter.extensions):
            return adapter
    return None


__all__ = ["Derived", "FormatAdapter", "ADAPTERS", "adapter_for"]
