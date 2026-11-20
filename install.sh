#!/usr/bin/env bash
# Portable install for metascrub (no root — installs to $PREFIX).
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local}"
BIN="$PREFIX/bin"
APPS="$PREFIX/share/applications"
ICONS="$PREFIX/share/icons/hicolor"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIBDIR="$PREFIX/lib/metascrub"

mkdir -p "$BIN" "$APPS" "$ICONS/scalable/apps" "$LIBDIR"

rm -rf "$LIBDIR/metascrub"
cp -r "$SRC_DIR/src/metascrub" "$LIBDIR/metascrub"
cp "$SRC_DIR/packaging/cli_main.py" "$SRC_DIR/packaging/gui_main.py" "$LIBDIR/"

printf '#!/bin/sh\nexec python3 "%s/cli_main.py" "$@"\n' "$LIBDIR" > "$BIN/metascrub"
printf '#!/bin/sh\nexec python3 "%s/gui_main.py" "$@"\n' "$LIBDIR" > "$BIN/metascrub-gui"
chmod 755 "$BIN/metascrub" "$BIN/metascrub-gui"

install -m 644 "$SRC_DIR/packaging/metascrub.desktop" "$APPS/metascrub.desktop"
install -m 644 "$SRC_DIR/packaging/metascrub.svg" "$ICONS/scalable/apps/metascrub.svg"
for sz in 16 24 32 48 64 96 128 256 512; do
    install -Dm 644 "$SRC_DIR/packaging/icons/hicolor/${sz}x${sz}/apps/metascrub.png" \
        "$ICONS/${sz}x${sz}/apps/metascrub.png"
done

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" 2>/dev/null || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t "$ICONS" 2>/dev/null || true

echo "✔ metascrub installed to $PREFIX"
echo "  CLI:  metascrub"
echo "  GUI:  metascrub-gui"
