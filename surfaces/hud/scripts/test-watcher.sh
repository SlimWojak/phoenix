#!/bin/bash
# Test script for ManifestWatcher
# Modifies MockManifest.json to test file watching and stale detection

MANIFEST="/Users/echopeso/phoenix-hud/WarBoarHUD/Preview Content/MockManifest.json"

echo "🐗 Testing ManifestWatcher..."
echo ""

# Test 1: Update manifest with fresh timestamp
echo "TEST 1: Updating manifest with fresh timestamp..."
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Use a temp file for atomic write (like Phoenix does)
cat > "${MANIFEST}.tmp" << EOF
{
  "meta": {
    "schema_version": "1.1",
    "generated_at": "${TIMESTAMP}",
    "manifest_seq": 99999,
    "phoenix_state_hash": "test123",
    "source": "test-watcher"
  },
  "session": {
    "kz": "TOKYO",
    "active": true,
    "time_remaining": "1h 30m",
    "next_session": "LONDON",
    "next_start": "08:00"
  },
  "portfolio": {
    "balance": 12500.00,
    "currency": "USD",
    "today_pnl": 150.25,
    "today_pct": 1.22,
    "week_pct": 3.5
  },
  "live_positions": [
    {
      "pair": "USDJPY",
      "direction": "SHORT",
      "entry_price": 149.50,
      "current_price": 149.20,
      "pnl_pips": 30,
      "pnl_dollars": 90.00,
      "duration": "45m",
      "bead_id": "TEST_001"
    }
  ],
  "recent_trades": {
    "items": [
      {"bead_id": "T1", "pair": "EURUSD", "result_pips": 50, "close_time": "07:30"}
    ],
    "total_count": 1
  },
  "gates_summary": [
    {"pair": "USDJPY", "passed": 5, "total": 5, "status": "READY"},
    {"pair": "EURUSD", "passed": 3, "total": 5, "status": "WATCHING"}
  ],
  "narrator": {
    "lines": [
      {"timestamp": "$(date +%H:%M)", "text": "Test watcher update!", "source_bead_id": null}
    ],
    "buffer_size": 20
  },
  "requires_action": [],
  "health": {
    "overall": "GREEN",
    "status": "HEALTHY",
    "since": "2026-01-31T12:00:00Z",
    "degraded_reasons": [],
    "components": {"ibkr": "GREEN", "river": "GREEN", "halt_state": "GREEN", "lease": "GREEN", "decay": "GREEN"},
    "heartbeat_age_seconds": 2
  },
  "lease": {
    "status": "ACTIVE",
    "strategy": "TEST_STRATEGY",
    "time_remaining": "2h 00m",
    "expires_at": "2026-01-31T20:00:00Z"
  }
}
EOF

# Atomic rename
mv "${MANIFEST}.tmp" "${MANIFEST}"
echo "   Updated! Check HUD - should show TOKYO session, USDJPY SHORT"
echo ""

sleep 3

# Test 2: Update again to verify reactivity
echo "TEST 2: Updating balance to verify reactivity..."
TIMESTAMP2=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "${MANIFEST}.tmp" << EOF
{
  "meta": {
    "schema_version": "1.1",
    "generated_at": "${TIMESTAMP2}",
    "manifest_seq": 100000,
    "phoenix_state_hash": "test456",
    "source": "test-watcher-2"
  },
  "session": {
    "kz": "TOKYO",
    "active": true,
    "time_remaining": "1h 28m",
    "next_session": "LONDON",
    "next_start": "08:00"
  },
  "portfolio": {
    "balance": 12750.00,
    "currency": "USD",
    "today_pnl": 400.25,
    "today_pct": 3.25,
    "week_pct": 5.1
  },
  "live_positions": [],
  "recent_trades": {
    "items": [
      {"bead_id": "T1", "pair": "USDJPY", "result_pips": 45, "close_time": "$(date +%H:%M)"},
      {"bead_id": "T2", "pair": "EURUSD", "result_pips": 50, "close_time": "07:30"}
    ],
    "total_count": 2
  },
  "gates_summary": [
    {"pair": "GBPUSD", "passed": 5, "total": 5, "status": "READY"}
  ],
  "narrator": {
    "lines": [
      {"timestamp": "$(date +%H:%M)", "text": "Position closed +45 pips!", "source_bead_id": "T1"}
    ],
    "buffer_size": 20
  },
  "requires_action": [],
  "health": {
    "overall": "GREEN",
    "status": "HEALTHY",
    "since": "2026-01-31T12:00:00Z",
    "degraded_reasons": [],
    "components": {"ibkr": "GREEN", "river": "GREEN", "halt_state": "GREEN", "lease": "GREEN", "decay": "GREEN"},
    "heartbeat_age_seconds": 1
  },
  "lease": {
    "status": "ACTIVE",
    "strategy": "TEST_STRATEGY",
    "time_remaining": "1h 58m",
    "expires_at": "2026-01-31T20:00:00Z"
  }
}
EOF

mv "${MANIFEST}.tmp" "${MANIFEST}"
echo "   Updated! Check HUD - balance should now be \$12,750, 0 positions"
echo ""

echo "✅ File watcher tests complete!"
echo ""
echo "To test STALE detection, wait 60+ seconds without updating the manifest."
echo "Or run: ./scripts/test-stale.sh"
