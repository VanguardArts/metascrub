#!/usr/bin/env bash
# Build a .deb package from the PyInstaller binaries in $DIST_DIR.
# Needs: dpkg-deb, and $DIST_DIR/{metascrub-cli,metascrub-gui,metascrub.png}.
set -euo pipefail

VERSION="${VERSION:?set VERSION (e.g. 0.2.1)}"
DIST_DIR="${DIST_DIR:-dist}"
OUT="$DIST_DIR/metascrub_${VERSION}_amd64.deb"

PKG="$DIST_DIR/deb-root"
rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" "$PKG/usr/bin" \
         "$PKG/usr/share/applications" \
         "$PKG/usr/share/icons/hicolor/256x256/apps"

install -m 755 "$DIST_DIR/metascrub-cli" "$PKG/usr/bin/metascrub"
install -m 755 "$DIST_DIR/metascrub-gui" "$PKG/usr/bin/metascrub-gui"
install -m 644 packaging/metascrub.desktop \
    "$PKG/usr/share/applications/metascrub.desktop"
install -m 644 "$DIST_DIR/metascrub.png" \
    "$PKG/usr/share/icons/hicolor/256x256/apps/metascrub.png"

SIZE=$(du -sk "$PKG" | cut -f1)
cat > "$PKG/DEBIAN/control" <<CTRL_EOF
Package: metascrub
Version: $VERSION
Section: sound
Priority: optional
Architecture: amd64
Installed-Size: $SIZE
Maintainer: metascrub contributors <https://github.com/VanguardArts/metascrub>
Homepage: https://github.com/VanguardArts/metascrub
Description: Byte-safe audio metadata hygiene (CLI + GUI)
 Inspect, strip and normalize audio metadata (comments, lyrics, C2PA
 provenance, origin URLs, cover art) without re-encoding audio.
 Ships the metascrub command line tool and the metascrub-gui desktop app.
CTRL_EOF

dpkg-deb --build --root-owner-group "$PKG" "$OUT"
rm -rf "$PKG"
echo "built $OUT"
