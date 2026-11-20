#!/usr/bin/env bash
# Build the Flatpak for metascrub (requires flatpak + flatpak-builder).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/packaging/flatpak/com.vanguardarts.Metascrub.yml"
OUT="$ROOT/build/flatpak"

command -v flatpak-builder >/dev/null 2>&1 || { echo "error: flatpak-builder not found" >&2; exit 1; }
flatpak remote-add --if-not-exists --user flathub https://flathub.org/repo/flathub.flatpakrepo

mkdir -p "$OUT"
flatpak-builder --force-clean --user --install-deps-from=flathub "$OUT/build-dir" "$MANIFEST"
flatpak build-export "$OUT/repo" "$OUT/build-dir"
flatpak build-bundle "$OUT/repo" "$OUT/metascrub.flatpak" com.vanguardarts.Metascrub
echo "✔ Flatpak built: $OUT/metascrub.flatpak"
