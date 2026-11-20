#!/usr/bin/env bash
# Uninstall metascrub (portable install only).
set -euo pipefail

PREFIX="${PREFIX:-$HOME/.local}"
LIBDIR="$PREFIX/lib/metascrub"

rm -rf "$LIBDIR"
rm -f "$PREFIX/bin/metascrub" "$PREFIX/bin/metascrub-gui"
rm -f "$PREFIX/share/applications/metascrub.desktop"
rm -f "$PREFIX/share/icons/hicolor/scalable/apps/metascrub.svg"
for sz in 16 24 32 48 64 96 128 256 512; do
    rm -f "$PREFIX/share/icons/hicolor/${sz}x${sz}/apps/metascrub.png"
done

echo "✔ metascrub uninstalled from $PREFIX"
