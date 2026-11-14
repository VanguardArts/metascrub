"""Discover user-meaningful storage places: home, filesystem root, and
mounted external drives (USB disks, VeraCrypt volumes, secondary HDDs...).

The file dialog (native portal or Qt's own) does not reliably list mounted
volumes on every platform — especially from packaged Linux builds — so the
GUI offers these as quick-jump targets instead.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from PySide6.QtCore import QStorageInfo


@dataclass
class Place:
    label: str
    path: str
    detail: str = ""  # e.g. "232 GB free"


# pseudo/system filesystems we never want to show
_IGNORED_FS = {
    "tmpfs", "devtmpfs", "devpts", "proc", "sysfs", "cgroup", "cgroup2",
    "pstore", "bpf", "tracefs", "debugfs", "configfs", "fusectl",
    "securityfs", "hugetlbfs", "mqueue", "ramfs", "autofs", "overlay",
    "squashfs", "nsfs", "efivarfs", "binfmt_misc", "fuse.portal",
    "fuse.gvfsd-fuse", "fuse.snapfuse", "shm", "fdescfs", "devfs",
}
_IGNORED_MOUNT_PREFIXES = ("/snap", "/run/user", "/sys", "/proc",
                           "/boot", "/var/lib", "/run/lock")
_IGNORED_MOUNTS = {"/", "/home"}
_IGNORED_DEVICES = ("/dev/loop", "/dev/zram")


def _bs(value) -> str:
    """QStorageInfo returns QByteArray on some platforms, str on others."""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", "replace")
    return str(value or "")


def _free(vol: QStorageInfo) -> str:
    free = vol.bytesAvailable()
    return f"{free / 1e9:.0f} GB free" if free >= 0 else ""


def _volume_places() -> List[Place]:
    places: List[Place] = []
    seen = set()
    for vol in QStorageInfo.mountedVolumes():
        if not vol.isValid() or not vol.isReady():
            continue
        mp = vol.rootPath()
        if not mp or mp in seen:
            continue
        fs = _bs(vol.fileSystemType())
        dev = _bs(vol.device())

        if sys.platform.startswith("win"):
            # every mounted volume root is a drive ("C:/", "D:/", ...)
            if len(mp) < 2 or mp[1] != ":":
                continue
        elif sys.platform == "darwin":
            if mp != "/" and not mp.startswith("/Volumes/"):
                continue
        else:  # linux / other unix
            if fs in _IGNORED_FS or mp in _IGNORED_MOUNTS:
                continue
            if any(mp.startswith(p) for p in _IGNORED_MOUNT_PREFIXES):
                continue
            if dev.startswith(_IGNORED_DEVICES):
                continue
            under_mountpoint = mp.startswith(("/media/", "/run/media/",
                                              "/mnt/"))
            dev_backed = dev.startswith("/dev/")
            if not (under_mountpoint or dev_backed):
                continue

        seen.add(mp)
        label = (_bs(vol.displayName())
                 or os.path.basename(mp.rstrip("/")) or "Drive")
        if mp == "/" and sys.platform == "darwin":
            label = "Macintosh HD"
        places.append(Place(label=label, path=mp, detail=_free(vol)))
    places.sort(key=lambda p: p.label.lower())
    return places


def mounted_places() -> List[Place]:
    """Home, then filesystem root (non-Windows), then mounted drives."""
    places = [Place(label="Home", path=str(Path.home()))]
    if not sys.platform.startswith("win"):
        places.append(Place(label="Computer", path="/"))
    places.extend(_volume_places())
    return places
