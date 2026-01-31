#!/bin/bash
# Link Phoenix state directory for HUD file seam
# HUD now lives inside Phoenix repo at surfaces/hud/
# Usage: ./scripts/link-phoenix-state.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Since HUD is at phoenix/surfaces/hud/, state is at ../../state/
STATE_SOURCE="$PROJECT_ROOT/../../state"
STATE_LINK="$PROJECT_ROOT/state"

echo "🐗 Linking Phoenix state directory..."
echo ""

# Resolve and verify source exists
STATE_SOURCE_RESOLVED="$(cd "$PROJECT_ROOT/../.." && pwd)/state"
if [[ ! -d "$STATE_SOURCE_RESOLVED" ]]; then
    echo "❌ Error: Phoenix state directory not found: $STATE_SOURCE_RESOLVED"
    echo "   Expected HUD at: phoenix/surfaces/hud/"
    echo "   Expected state at: phoenix/state/"
    exit 1
fi

if [[ -L "$STATE_LINK" ]]; then
    echo "   Removing existing symlink..."
    rm "$STATE_LINK"
elif [[ -e "$STATE_LINK" ]]; then
    echo "❌ Error: $STATE_LINK exists and is not a symlink"
    exit 1
fi

# Use relative symlink for portability
ln -s "../../state" "$STATE_LINK"

echo "✅ Symlink created:"
echo "   $STATE_LINK → ../../state"
echo ""
echo "   HUD will read: $STATE_LINK/manifest.json"
