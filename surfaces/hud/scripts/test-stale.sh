#!/bin/bash
# Test stale detection by writing an old timestamp

MANIFEST="/Users/echopeso/phoenix-hud/WarBoarHUD/Preview Content/MockManifest.json"

echo "🐗 Testing STALE detection..."
echo ""

# Write manifest with old timestamp (2 minutes ago)
OLD_TIMESTAMP=$(date -u -v-2M +"%Y-%m-%dT%H:%M:%SZ")

cat > "${MANIFEST}.tmp" << EOF
{
  "meta": {
    "schema_version": "1.1",
    "generated_at": "${OLD_TIMESTAMP}",
    "manifest_seq": 100001,
    "phoenix_state_hash": "stale_test",
    "source": "stale-test"
  },
  "session": {
    "kz": "LONDON",
    "active": false,
    "time_remaining": "0m",
    "next_session": "NEW_YORK",
    "next_start": "13:00"
  },
  "portfolio": {
    "balance": 10000.00,
    "currency": "USD",
    "today_pnl": 0,
    "today_pct": 0,
    "week_pct": 0
  },
  "live_positions": [],
  "recent_trades": {"items": [], "total_count": 0},
  "gates_summary": [],
  "narrator": {
    "lines": [{"timestamp": "OLD", "text": "This manifest is stale!", "source_bead_id": null}],
    "buffer_size": 20
  },
  "requires_action": [],
  "health": {
    "overall": "YELLOW",
    "status": "DEGRADED",
    "since": "${OLD_TIMESTAMP}",
    "degraded_reasons": ["Stale test"],
    "components": {"ibkr": "GREEN", "river": "YELLOW", "halt_state": "GREEN", "lease": "GREEN", "decay": "GREEN"},
    "heartbeat_age_seconds": 120
  },
  "lease": {"status": "ABSENT", "strategy": null, "time_remaining": null, "expires_at": null}
}
EOF

mv "${MANIFEST}.tmp" "${MANIFEST}"

echo "Written manifest with timestamp: ${OLD_TIMESTAMP} (2 minutes ago)"
echo ""
echo "⚠️  HUD should now show STALE overlay within 5 seconds!"
echo ""
echo "To restore fresh state, run: ./scripts/test-watcher.sh"
