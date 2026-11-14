#!/usr/bin/env bash
# Build a distributable .dmg containing the metascrub GUI .app (macOS only).
set -euo pipefail

DIST_DIR="${DIST_DIR:-dist}"
STAGE="$DIST_DIR/dmg-staging"

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -R "$DIST_DIR/metascrub-gui.app" "$STAGE/"
ln -s /Applications "$STAGE/Applications"

hdiutil create -volname metascrub -srcfolder "$STAGE" -ov -format UDZO \
    "$DIST_DIR/metascrub-gui-macos.dmg"
rm -rf "$STAGE"
echo "built $DIST_DIR/metascrub-gui-macos.dmg"
