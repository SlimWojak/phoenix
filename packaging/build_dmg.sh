#!/bin/bash
# =============================================================================
# Phoenix DMG Builder — S41 Track D
# =============================================================================
#
# Creates distributable DMG from Phoenix.app
#
# Usage:
#   ./build_dmg.sh
#
# Prerequisites:
#   - py2app installed: pip install py2app
#   - rumps installed: pip install rumps
#   - create-dmg (optional): brew install create-dmg
#
# Output:
#   dist/Phoenix-0.41.0.dmg
# =============================================================================

set -e  # Exit on error

VERSION="0.41.0"
APP_NAME="Phoenix"
DMG_NAME="${APP_NAME}-${VERSION}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "  Phoenix DMG Builder"
echo "  Version: ${VERSION}"
echo "================================================"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Step 1: Clean previous builds
echo "[1/5] Cleaning previous builds..."
rm -rf build dist "${SCRIPT_DIR}/build" "${SCRIPT_DIR}/dist"

# Step 2: Install build dependencies
echo "[2/5] Checking dependencies..."
if ! pip show py2app > /dev/null 2>&1; then
    echo "Installing py2app..."
    pip install py2app
fi

if ! pip show rumps > /dev/null 2>&1; then
    echo "Installing rumps (menu bar framework)..."
    pip install rumps
fi

# Step 3: Build .app with py2app
echo "[3/5] Building ${APP_NAME}.app..."
cd "$SCRIPT_DIR"
python setup_app.py py2app --dist-dir "${PROJECT_ROOT}/dist"

# Check if build succeeded
if [ ! -d "${PROJECT_ROOT}/dist/${APP_NAME}.app" ]; then
    echo "ERROR: App build failed!"
    exit 1
fi

echo "  ✓ ${APP_NAME}.app created"

# Step 4: Create DMG
echo "[4/5] Creating DMG..."
cd "$PROJECT_ROOT"

if command -v create-dmg > /dev/null 2>&1; then
    # Use create-dmg if available (prettier)
    create-dmg \
        --volname "${APP_NAME}" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "${APP_NAME}.app" 150 190 \
        --app-drop-link 450 190 \
        "dist/${DMG_NAME}.dmg" \
        "dist/${APP_NAME}.app"
else
    # Fallback to hdiutil
    echo "  (Using hdiutil - install create-dmg for prettier DMG)"
    
    # Create temporary directory
    DMG_TEMP="dist/dmg_temp"
    mkdir -p "$DMG_TEMP"
    
    # Copy app
    cp -R "dist/${APP_NAME}.app" "$DMG_TEMP/"
    
    # Create symlink to Applications
    ln -s /Applications "$DMG_TEMP/Applications"
    
    # Create DMG
    hdiutil create \
        -volname "${APP_NAME}" \
        -srcfolder "$DMG_TEMP" \
        -ov \
        -format UDZO \
        "dist/${DMG_NAME}.dmg"
    
    # Cleanup
    rm -rf "$DMG_TEMP"
fi

# Check if DMG created
if [ ! -f "dist/${DMG_NAME}.dmg" ]; then
    echo "ERROR: DMG creation failed!"
    exit 1
fi

echo "  ✓ ${DMG_NAME}.dmg created"

# Step 5: Verify
echo "[5/5] Verifying..."
DMG_SIZE=$(du -h "dist/${DMG_NAME}.dmg" | cut -f1)
echo "  DMG size: ${DMG_SIZE}"

# List contents
echo ""
echo "================================================"
echo "  BUILD COMPLETE"
echo "================================================"
echo "  App:  dist/${APP_NAME}.app"
echo "  DMG:  dist/${DMG_NAME}.dmg"
echo "  Size: ${DMG_SIZE}"
echo ""
echo "  To install: Open DMG, drag to Applications"
echo "================================================"

# Optional: Notarization reminder
echo ""
echo "NOTE: For distribution outside your machine,"
echo "      the app should be signed and notarized."
echo "      See: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution"
