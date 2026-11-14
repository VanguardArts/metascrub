"""Directory walking + adapter dispatch."""
from __future__ import annotations

import os
from typing import Iterator, List, Tuple

from .formats import ADAPTERS, Derived, adapter_for
from .policy import Policy
from .report import FileResult
from .tags import derive_genre


def iter_files(root: str) -> Iterator[Tuple[str, str]]:
    """Yield (abspath, relpath) for every regular file under root, sorted."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            yield full, os.path.relpath(full, root)


def _derive(relpath: str, policy: Policy) -> Derived:
    title = None
    if policy.titles.enabled:
        title = policy.titles.derive(os.path.basename(relpath))
    return Derived(
        title=title,
        genre=derive_genre(relpath, policy.genre_mode, policy.genre_fixed),
        album=policy.credits.album_for(relpath),
    )


def scan(root: str, policy: Policy) -> List[FileResult]:
    results: List[FileResult] = []
    for full, rel in iter_files(root):
        adapter = adapter_for(full)
        if adapter is None:
            continue
        if policy.is_excluded(rel):
            results.append(FileResult(path=rel, format=adapter.name, skipped=True))
            continue
        results.append(adapter.inspect(full, rel, policy))
    return results


def clean(root: str, policy: Policy, dry_run: bool) -> List[FileResult]:
    results: List[FileResult] = []
    for full, rel in iter_files(root):
        adapter = adapter_for(full)
        if adapter is None:
            continue
        if policy.is_excluded(rel):
            results.append(FileResult(path=rel, format=adapter.name, skipped=True))
            continue
        results.append(adapter.clean(full, rel, policy, _derive(rel, policy), dry_run))
    return results


def verify(root: str, policy: Policy) -> List[FileResult]:
    """Re-scan and flag any entry whose key or value matches a signature."""
    results: List[FileResult] = []
    sigs = policy.signatures()
    for full, rel in iter_files(root):
        adapter = adapter_for(full)
        if adapter is None:
            continue
        if policy.is_excluded(rel):
            continue
        found = adapter.inspect(full, rel, policy)
        hits = [
            e for e in found.entries
            if any(s in f"{e.key} {e.value}".lower() for s in sigs)
        ]
        results.append(FileResult(path=rel, format=found.format, entries=hits,
                                  skipped=found.skipped, error=found.error))
    return results
