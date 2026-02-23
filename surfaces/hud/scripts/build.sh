#!/bin/bash
# WarBoar HUD Build Script
# Usage: ./scripts/build.sh [debug|release]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$PROJECT_ROOT/WarBoarHUD"

CONFIG="${1:-Debug}"
if [[ "$1" == "release" ]]; then
    CONFIG="Release"
fi

echo "🐗 Building WarBoar HUD ($CONFIG)..."
echo ""

cd "$PROJECT_DIR"

xcodebuild \
    -project WarBoarHUD.xcodeproj \
    -scheme WarBoarHUD \
    -configuration "$CONFIG" \
    -derivedDataPath "$PROJECT_ROOT/build" \
    build

echo ""
echo "✅ Build complete!"
echo "   App: $PROJECT_ROOT/build/Build/Products/$CONFIG/WarBoarHUD.app"
