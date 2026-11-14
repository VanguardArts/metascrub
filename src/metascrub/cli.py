"""metascrub command line interface.

  metascrub scan   <path>                 Show every embedded tag/chunk.
  metascrub clean  <path> [--apply]       Strip provenance + apply credits.
  metascrub verify <path>                 Exit 1 if any provenance signature remains.

`clean` is a dry run unless --apply is passed. Policies (YAML/JSON) set credits
and rules once; CLI flags override them.
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__
from .policy import Policy
from .report import render_json, render_text
from .scanner import clean as scan_clean
from .scanner import scan, verify


def _add_common(p: argparse.ArgumentParser):
    p.add_argument("path", help="File or folder tree to process (recursive).")
    p.add_argument("--policy", help="YAML or JSON policy file.")
    p.add_argument("--exclude", action="append", default=[],
                   help="Regex; matching relative paths are skipped (repeatable).")
    p.add_argument("--json", action="store_true", help="Machine-readable output.")


def _add_credit_flags(p: argparse.ArgumentParser):
    p.add_argument("--artist")
    p.add_argument("--album-artist")
    p.add_argument("--composer", help="Production/composer credit.")
    p.add_argument("--label", help="Label/publisher (MP3 only; RIFF INFO has no field).")
    p.add_argument("--copyright")
    p.add_argument("--year")
    p.add_argument("--album", help="Release/album name.")
    p.add_argument("--release-subdir",
                   help="Apply --album only to files under this sub-directory "
                        "(singles get no album tag).")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="metascrub",
        description="Byte-safe audio metadata hygiene: inspect, strip provenance, "
                    "re-tag credits, clean titles. Never re-encodes audio.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("scan", help="List all embedded tags/chunks with predicted actions.")
    _add_common(sp)

    cp = sub.add_parser("clean", help="Strip provenance metadata and apply credits.")
    _add_common(cp)
    _add_credit_flags(cp)
    cp.add_argument("--apply", action="store_true",
                    help="Actually write changes (default is a dry run).")
    cp.add_argument("--genre-mode", choices=["brackets", "fixed", "none"],
                    help="Genre source: [bracket] in filename (default), fixed value, none.")
    cp.add_argument("--genre-fixed", help="Genre value when --genre-mode=fixed.")
    cp.add_argument("--label-prefix",
                    help='Label prefix stripped from titles, e.g. "My Label - ".')
    cp.add_argument("--no-titles", action="store_true",
                    help="Leave title tags untouched.")
    cp.add_argument("--keep-cover-art", action="store_true",
                    help="Do not strip embedded cover art.")

    vp = sub.add_parser("verify", help="Fail if any provenance signature remains.")
    _add_common(vp)
    vp.add_argument("--signature", action="append", default=[],
                    help="Extra case-insensitive signature to hunt for (repeatable).")
    return p


def _policy_from_args(args) -> Policy:
    policy = Policy.load(args.policy) if args.policy else Policy()
    policy.exclude.extend(args.exclude)
    if getattr(args, "signature", None):
        policy.extra_signatures.extend(args.signature)

    c = policy.credits
    for arg, attr in [
        ("artist", "artist"), ("album_artist", "album_artist"),
        ("composer", "composer"), ("label", "label"),
        ("copyright", "copyright"), ("year", "year"),
        ("album", "album"), ("release_subdir", "release_subdir"),
    ]:
        val = getattr(args, arg, None)
        if val is not None:
            setattr(c, attr, val)

    if getattr(args, "genre_mode", None):
        policy.genre_mode = args.genre_mode
    if getattr(args, "genre_fixed", None) is not None:
        policy.genre_fixed = args.genre_fixed
    if getattr(args, "label_prefix", None) is not None:
        policy.titles.strip_label_prefix = args.label_prefix
    if getattr(args, "no_titles", False):
        policy.titles.enabled = False
    if getattr(args, "keep_cover_art", False):
        policy.remove_cover_art = False
    return policy


def _emit(results, json_mode: bool, dry_run: bool):
    print(render_json(results, dry_run) if json_mode else render_text(results, dry_run))


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        policy = _policy_from_args(args)
    except Exception as exc:
        print(f"error: invalid policy: {exc}", file=sys.stderr)
        return 2

    if args.command == "scan":
        _emit(scan(args.path, policy), args.json, dry_run=True)
        return 0

    if args.command == "clean":
        dry = not args.apply
        results = scan_clean(args.path, policy, dry_run=dry)
        _emit(results, args.json, dry_run=dry)
        return 2 if any(r.error for r in results) else 0

    if args.command == "verify":
        results = verify(args.path, policy)
        hits = sum(len(r.entries) for r in results)
        if args.json:
            _emit(results, True, dry_run=True)
        else:
            for r in results:
                for e in r.entries:
                    print(f"HIT {r.path}: {e.key} = {e.value}")
            print("verify: OK — no provenance signatures found." if hits == 0
                  else f"verify: FAILED — {hits} provenance signature(s) remain.")
        return 1 if hits else 0

    return 2  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
