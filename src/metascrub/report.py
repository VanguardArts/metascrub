"""Report models and rendering (text + JSON)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class TagEntry:
    key: str            # e.g. "COMM::eng", "INFO:ICMT", "chunk:C2PA"
    value: str          # preview (truncated)
    action: str         # strip | set | keep
    kind: str = ""      # provenance | audio | tag


@dataclass
class FileResult:
    path: str
    format: str
    entries: List[TagEntry] = field(default_factory=list)
    skipped: bool = False
    error: Optional[str] = None

    def counts(self):
        strip = sum(1 for e in self.entries if e.action == "strip")
        setn = sum(1 for e in self.entries if e.action == "set")
        keep = sum(1 for e in self.entries if e.action == "keep")
        return strip, setn, keep


def render_text(results: List[FileResult], dry_run: bool) -> str:
    lines = []
    n_files = n_strip = n_set = 0
    for r in results:
        n_files += 1
        strip, setn, _ = r.counts()
        n_strip += strip
        n_set += setn
        head = f"{r.path}  [{r.format}]"
        if r.skipped:
            lines.append(f"SKIP {head}")
            continue
        if r.error:
            lines.append(f"ERR  {head}: {r.error}")
            continue
        lines.append(f"FILE {head}")
        for e in r.entries:
            marker = {"strip": "-", "set": "+", "keep": "="}.get(e.action, "?")
            lines.append(f"  {marker} {e.key:<22} [{e.action}]  {e.value}")
    lines.append("")
    lines.append(
        f"Summary: {n_files} files, {n_strip} tags stripped, {n_set} tags set."
    )
    if dry_run:
        lines.append("DRY RUN — no files were modified. Re-run with --apply to write.")
    return "\n".join(lines)


def render_json(results: List[FileResult], dry_run: bool) -> str:
    payload = {
        "dry_run": dry_run,
        "files": [
            {
                "path": r.path,
                "format": r.format,
                "skipped": r.skipped,
                "error": r.error,
                "entries": [asdict(e) for e in r.entries],
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def preview(text: str, limit: int = 90) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"
