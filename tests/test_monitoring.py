"""
Test monitoring components — Dashboard, Alerts, Debounce

SPRINT: S28.B
"""

import json
import sys
import time
import urllib.request
from pathlib import Path

# Add phoenix to path
PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

from monitoring.alerts import AlertClass, AlertLevel, AlertManager
from monitoring.dashboard import HealthDashboard, MetricsStore

# =============================================================================
# ALERT TESTS
# =============================================================================


def test_halt_threshold_warn():
    """Test halt latency WARN threshold (>10ms)."""
    manager = AlertManager()
    manager.clear_history()

    # Below threshold - no alert
    alert = manager.emit_halt_violation(5.0)
    assert alert is None, "Should not alert below threshold"

    # Above WARN threshold
    alert = manager.emit_halt_violation(15.0)
    assert alert is not None, "Should alert above WARN threshold"
    assert alert.level == AlertLevel.WARN

    print("✓ test_halt_threshold_warn PASS")


def test_halt_threshold_critical():
    """Test halt latency CRITICAL threshold (>50ms)."""
    manager = AlertManager()
    manager.clear_history()

    # Above CRITICAL threshold
    alert = manager.emit_halt_violation(60.0)
    assert alert is not None, "Should alert above CRITICAL threshold"
    assert alert.level == AlertLevel.CRITICAL

    print("✓ test_halt_threshold_critical PASS")


def test_quality_threshold():
    """Test quality degradation thresholds."""
    manager = AlertManager()
    manager.clear_history()

    # Healthy quality - no alert
    alert = manager.emit_quality_degraded(0.95)
    assert alert is None, "Should not alert for healthy quality"

    # Degraded quality - WARN
    alert = manager.emit_quality_degraded(0.7)
    assert alert is not None, "Should alert for degraded quality"
    assert alert.level == AlertLevel.WARN

    print("✓ test_quality_threshold PASS")


def test_debounce_suppression():
    """Test that duplicate alerts are suppressed within debounce window."""
    manager = AlertManager(debounce_seconds=1.0)  # Short debounce for testing
    manager.clear_history()

    # First alert - should fire
    alert1 = manager.emit_halt_violation(60.0)
    assert alert1 is not None, "First alert should fire"

    # Rapid subsequent alerts - should be suppressed
    alert2 = manager.emit_halt_violation(65.0)
    alert3 = manager.emit_halt_violation(70.0)
    alert4 = manager.emit_halt_violation(75.0)
    alert5 = manager.emit_halt_violation(80.0)

    assert alert2 is None, "Second alert should be suppressed"
    assert alert3 is None, "Third alert should be suppressed"
    assert alert4 is None, "Fourth alert should be suppressed"
    assert alert5 is None, "Fifth alert should be suppressed"

    # Wait for debounce to expire
    time.sleep(1.1)

    # Now should fire again
    alert6 = manager.emit_halt_violation(85.0)
    assert alert6 is not None, "Alert after debounce should fire"

    # Check stats
    stats = manager.get_stats()
    assert stats["suppressed_count"] == 4, f"Expected 4 suppressed, got {stats['suppressed_count']}"

    print("✓ test_debounce_suppression PASS")


def test_debounce_critical_override():
    """Test that CRITICAL can override WARN during debounce."""
    manager = AlertManager(debounce_seconds=10.0)
    manager.clear_history()

    # WARN alert first
    alert1 = manager.emit_halt_violation(15.0)  # WARN
    assert alert1 is not None
    assert alert1.level == AlertLevel.WARN

    # CRITICAL should override even during debounce
    alert2 = manager.emit_halt_violation(60.0)  # CRITICAL
    assert alert2 is not None, "CRITICAL should override WARN during debounce"
    assert alert2.level == AlertLevel.CRITICAL

    print("✓ test_debounce_critical_override PASS")


def test_worker_death_alert():
    """Test worker death alerts."""
    manager = AlertManager()
    manager.clear_history()

    # Worker death - always CRITICAL
    alert = manager.emit_worker_death("worker-1", "connection lost")
    assert alert is not None
    assert alert.level == AlertLevel.CRITICAL
    assert alert.alert_class == AlertClass.WORKER_DEATH

    print("✓ test_worker_death_alert PASS")


# =============================================================================
# DASHBOARD TESTS
# =============================================================================


def test_metrics_store():
    """Test metrics store updates."""
    store = MetricsStore()

    # Record halt latencies
    store.record_halt_latency(5.0)
    store.record_halt_latency(10.0)
    store.record_halt_latency(3.0)

    snapshot = store.get_snapshot()
    assert snapshot["halt"]["last_ms"] == 3.0
    assert snapshot["halt"]["samples"] == 3

    # Update quality
    store.update_river_quality(0.85)
    snapshot = store.get_snapshot()
    assert snapshot["river"]["quality"] == 0.85
    assert snapshot["river"]["health"] == "healthy"

    # Worker heartbeat
    store.update_worker_heartbeat("worker-1", "alive", 10)
    snapshot = store.get_snapshot()
    assert len(snapshot["workers"]) == 1
    assert snapshot["workers"][0]["id"] == "worker-1"

    print("✓ test_metrics_store PASS")


def test_dashboard_server():
    """Test dashboard HTTP server."""
    dashboard = HealthDashboard(port=18080)

    # Add test data
    dashboard.record_halt_latency(5.0)
    dashboard.update_river_quality(0.92)
    dashboard.update_worker_heartbeat("test-worker", "alive", 5)
    dashboard.update_chaos_status(4, 4, 0, {"V3-1": "pass", "V3-2": "pass"})

    # Start server
    dashboard.start()
    time.sleep(0.5)  # Let server start

    try:
        # Test HTML endpoint
        with urllib.request.urlopen(f"{dashboard.url}/") as response:
            html = response.read().decode()
            assert "Phoenix Health Dashboard" in html
            assert "Halt Latency" in html
            assert "River Quality" in html

        # Test JSON API endpoint
        with urllib.request.urlopen(f"{dashboard.url}/api/metrics") as response:
            data = json.loads(response.read().decode())
            assert "halt" in data
            assert "river" in data
            assert "workers" in data
            assert data["river"]["quality"] == 0.92

        # Test alerts API endpoint
        with urllib.request.urlopen(f"{dashboard.url}/api/alerts") as response:
            data = json.loads(response.read().decode())
            assert "alerts" in data
            assert "stats" in data

        print("✓ test_dashboard_server PASS")

    finally:
        dashboard.stop()


# =============================================================================
# INTEGRATION TEST
# =============================================================================


def test_full_alert_flow():
    """Integration test: inject violations, verify alerts fire."""
    manager = AlertManager(debounce_seconds=0.1)  # Fast debounce for test
    manager.clear_history()

    alerts_received = []
    manager.register_callback(lambda a: alerts_received.append(a))

    # Inject halt violation > 50ms
    manager.emit_halt_violation(60.0)

    # Inject quality degradation
    time.sleep(0.15)  # Wait for debounce
    manager.emit_quality_degraded(0.6)

    # Inject worker death
    time.sleep(0.15)
    manager.emit_worker_death("worker-1", "crash")

    # Verify alerts
    assert len(alerts_received) == 3, f"Expected 3 alerts, got {len(alerts_received)}"

    # Check alert types
    classes = [a.alert_class for a in alerts_received]
    assert AlertClass.HALT_LATENCY in classes
    assert AlertClass.QUALITY_DEGRADED in classes
    assert AlertClass.WORKER_DEATH in classes

    print("✓ test_full_alert_flow PASS")


# =============================================================================
# MAIN
# =============================================================================


def run_all_tests():
    """Run all monitoring tests."""
    print("\n" + "=" * 60)
    print("MONITORING TESTS — S28.B")
    print("=" * 60 + "\n")

    # Alert tests
    test_halt_threshold_warn()
    test_halt_threshold_critical()
    test_quality_threshold()
    test_debounce_suppression()
    test_debounce_critical_override()
    test_worker_death_alert()

    # Dashboard tests
    test_metrics_store()
    test_dashboard_server()

    # Integration test
    test_full_alert_flow()

    print("\n" + "=" * 60)
    print("ALL TESTS PASS")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()
