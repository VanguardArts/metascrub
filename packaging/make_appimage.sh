#!/usr/bin/env bash
# Build an AppImage of the metascrub GUI from $DIST_DIR/metascrub-gui.
# Needs: $APPIMAGETOOL (path to appimagetool) and $DIST_DIR/metascrub.png.
# Note: APP_DIR is intentionally not named APPDIR (AppImage runtime uses it).
set -euo pipefail

DIST_DIR="${DIST_DIR:-dist}"
APPIMAGETOOL="${APPIMAGETOOL:-appimagetool}"
OUT="$DIST_DIR/metascrub-gui-linux.AppImage"

APP_DIR="$DIST_DIR/AppDir"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/usr/bin"

install -m 755 "$DIST_DIR/metascrub-gui" "$APP_DIR/usr/bin/metascrub-gui"
install -m 644 packaging/metascrub.desktop "$APP_DIR/metascrub.desktop"
install -m 644 "$DIST_DIR/metascrub.png" "$APP_DIR/metascrub.png"

cat > "$APP_DIR/AppRun" <<'RUN_EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/metascrub-gui" "$@"
RUN_EOF
chmod +x "$APP_DIR/AppRun"

ARCH=x86_64 "$APPIMAGETOOL" --appimage-extract-and-run "$APP_DIR" "$OUT"
rm -rf "$APP_DIR"
echo "built $OUT"
