"""Directory walking + adapter dispatch."""
from __future__ import annotations

import os
from typing import Callable, List, Optional, Tuple

from .formats import Derived, adapter_for
from .policy import Policy
from .report import FileResult
from .tags import derive_genre

ProgressCb = Optional[Callable[[int, int, str], None]]


def iter_files(root: str):
    """Yield (abspath, relpath) for every regular file under root, sorted."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            yield full, os.path.relpath(full, root)


def _collect(root: str, policy: Policy) -> List[Tuple[str, str, object, bool]]:
    """Collect (abspath, relpath, adapter, skipped) for all supported files."""
    items = []
    for full, rel in iter_files(root):
        adapter = adapter_for(full)
        if adapter is None:
            continue
        items.append((full, rel, adapter, policy.is_excluded(rel)))
    return items


def _derive(relpath: str, policy: Policy) -> Derived:
    title = None
    if policy.titles.enabled:
        title = policy.titles.derive(os.path.basename(relpath))
    return Derived(
        title=title,
        genre=derive_genre(relpath, policy.genre_mode, policy.genre_fixed),
        album=policy.credits.album_for(relpath),
    )


def scan(root: str, policy: Policy, progress: ProgressCb = None) -> List[FileResult]:
    results: List[FileResult] = []
    items = _collect(root, policy)
    total = len(items)
    for i, (full, rel, adapter, skipped) in enumerate(items, 1):
        if progress:
            progress(i, total, rel)
        if skipped:
            results.append(FileResult(path=rel, format=adapter.name, skipped=True))
            continue
        results.append(adapter.inspect(full, rel, policy))
    return results


def clean(root: str, policy: Policy, dry_run: bool,
          progress: ProgressCb = None) -> List[FileResult]:
    results: List[FileResult] = []
    items = _collect(root, policy)
    total = len(items)
    for i, (full, rel, adapter, skipped) in enumerate(items, 1):
        if progress:
            progress(i, total, rel)
        if skipped:
            results.append(FileResult(path=rel, format=adapter.name, skipped=True))
            continue
        results.append(adapter.clean(full, rel, policy, _derive(rel, policy), dry_run))
    return results


def verify(root: str, policy: Policy, progress: ProgressCb = None) -> List[FileResult]:
    """Re-scan and flag any entry whose key or value matches a signature."""
    results: List[FileResult] = []
    sigs = policy.signatures()
    items = _collect(root, policy)
    total = len(items)
    for i, (full, rel, adapter, skipped) in enumerate(items, 1):
        if progress:
            progress(i, total, rel)
        if skipped:
            continue
        found = adapter.inspect(full, rel, policy)
        hits = [
            e for e in found.entries
            if any(s in f"{e.key} {e.value}".lower() for s in sigs)
        ]
        results.append(FileResult(path=rel, format=found.format, entries=hits,
                                  skipped=False, error=found.error))
    return results
