#!/usr/bin/env bash
# Build a noarch .rpm for metascrub.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VERSION="${VERSION:-0.7.0}"
TOPDIR="build/rpm"

rm -rf "$TOPDIR"
mkdir -p "$TOPDIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

SRC="build/rpm-src/metascrub-$VERSION"
rm -rf "build/rpm-src"
mkdir -p "$SRC"
cp -r src packaging LICENSE README.md pyproject.toml "$SRC/"
tar -czf "$TOPDIR/SOURCES/metascrub-$VERSION.tar.gz" -C "build/rpm-src" "metascrub-$VERSION"

rpmbuild -bb --define "_topdir $(pwd)/$TOPDIR" packaging/rpm/metascrub.spec
echo "built $(find "$TOPDIR/RPMS" -name '*.rpm')"
