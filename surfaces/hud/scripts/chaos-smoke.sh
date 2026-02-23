#!/bin/bash
# Chaos Smoke Tests for HUD Integration
# Usage: ./scripts/chaos-smoke.sh [test_number]
#
# Tests:
#   1 - Corrupt manifest (HUD should show CORRUPT badge)
#   2 - Delete manifest (HUD should show NO_STATE)
#   3 - Stale test (wait 70s, HUD should show STALE overlay)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="$SCRIPT_DIR/../state"
MANIFEST="$STATE_DIR/manifest.json"
BACKUP="$STATE_DIR/manifest.json.backup"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

restore_manifest() {
    if [[ -f "$BACKUP" ]]; then
        echo -e "${GREEN}Restoring manifest from backup...${NC}"
        cp "$BACKUP" "$MANIFEST"
        echo "✅ Manifest restored"
    else
        echo -e "${YELLOW}No backup found, regenerating manifest...${NC}"
        cd "$SCRIPT_DIR/../.." && python -m state.manifest_writer
    fi
}

test_corrupt() {
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}TEST 1: CORRUPT MANIFEST${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo ""

    # Backup current manifest
    cp "$MANIFEST" "$BACKUP"

    echo "Writing corrupt JSON to manifest..."
    echo '{"meta": {"broken": true, invalid json here' > "$MANIFEST"

    echo ""
    echo -e "${RED}EXPECTED: HUD shows CORRUPT badge, keeps last good state${NC}"
    echo ""
    read -p "Press ENTER when verified, then we'll restore... "

    restore_manifest
    echo ""
    echo "Test 1 complete."
}

test_delete() {
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}TEST 2: DELETE MANIFEST${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo ""

    # Backup current manifest
    cp "$MANIFEST" "$BACKUP"

    echo "Deleting manifest.json..."
    rm "$MANIFEST"

    echo ""
    echo -e "${RED}EXPECTED: HUD shows NO_STATE indicator${NC}"
    echo ""
    read -p "Press ENTER when verified, then we'll restore... "

    restore_manifest
    echo ""
    echo "Test 2 complete."
}

test_stale() {
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}TEST 3: STALE MANIFEST (70s wait)${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════${NC}"
    echo ""

    echo "Current manifest timestamp:"
    grep generated_at "$MANIFEST" || echo "(no timestamp found)"
    echo ""
    echo "Waiting 70 seconds for manifest to become stale..."
    echo -e "${RED}EXPECTED: After ~60s, HUD shows STALE overlay${NC}"
    echo ""

    for i in {70..1}; do
        printf "\r  Seconds remaining: %02d " "$i"
        sleep 1
    done
    echo ""
    echo ""

    echo -e "${RED}CHECK: Does HUD show 'STALE STATE — CHECK PHOENIX' overlay?${NC}"
    echo ""
    read -p "Press ENTER to refresh manifest and complete test... "

    cd "$SCRIPT_DIR/../.." && python -m state.manifest_writer
    echo ""
    echo "Test 3 complete. Manifest refreshed."
}

run_all() {
    echo -e "${GREEN}Running all chaos smoke tests...${NC}"
    echo ""
    test_corrupt
    echo ""
    test_delete
    echo ""
    test_stale
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}ALL CHAOS SMOKE TESTS COMPLETE${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
}

# Main
case "${1:-all}" in
    1|corrupt)
        test_corrupt
        ;;
    2|delete)
        test_delete
        ;;
    3|stale)
        test_stale
        ;;
    all)
        run_all
        ;;
    *)
        echo "Usage: $0 [1|2|3|all]"
        echo ""
        echo "Tests:"
        echo "  1 (corrupt) - Write invalid JSON, expect CORRUPT badge"
        echo "  2 (delete)  - Remove manifest, expect NO_STATE"
        echo "  3 (stale)   - Wait 70s, expect STALE overlay"
        echo "  all         - Run all tests in sequence"
        exit 1
        ;;
esac
