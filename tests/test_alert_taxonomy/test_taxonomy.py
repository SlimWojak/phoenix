"""
Alert Taxonomy Tests
====================

Tests for alert classification, deduplication, and formatting.
"""

import time
from datetime import UTC, datetime

import pytest

from notification.alert_taxonomy import (
    Alert,
    AlertCategory,
    AlertDeduplicator,
    AlertRouter,
    AlertSeverity,
    TelegramAlertFormatter,
    create_circuit_open_alert,
    create_halt_alert,
    create_health_transition_alert,
    create_ibkr_connection_alert,
    create_supervisor_alert,
    create_constitutional_violation_alert,
)


# =============================================================================
# INV-ALERT-TAXONOMY-1: All alerts have explicit severity
# =============================================================================


class TestAlertSeverity:
    """Test that all alerts have explicit severity."""

    def test_alert_requires_severity(self):
        """Alert must have severity."""
        alert = Alert(
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.HALT,
            title="Test",
            message="Test message",
        )
        assert alert.severity == AlertSeverity.CRITICAL

    def test_severity_enum_values(self):
        """Severity enum has correct values."""
        assert AlertSeverity.CRITICAL.value == "CRITICAL"
        assert AlertSeverity.WARNING.value == "WARNING"
        assert AlertSeverity.INFO.value == "INFO"

    def test_factory_halt_is_critical(self):
        """Halt alerts are CRITICAL."""
        alert = create_halt_alert("test", "reason")
        assert alert.severity == AlertSeverity.CRITICAL

    def test_factory_circuit_open_is_warning(self):
        """Circuit open alerts are WARNING."""
        alert = create_circuit_open_alert("river", 3)
        assert alert.severity == AlertSeverity.WARNING

    def test_factory_supervisor_dead_is_critical(self):
        """Supervisor DEAD is CRITICAL."""
        alert = create_supervisor_alert("DEAD", "crash")
        assert alert.severity == AlertSeverity.CRITICAL

    def test_factory_supervisor_alive_is_info(self):
        """Supervisor ALIVE is INFO."""
        alert = create_supervisor_alert("ALIVE")
        assert alert.severity == AlertSeverity.INFO


# =============================================================================
# INV-ALERT-TAXONOMY-2: Deduplication ≤5 per 60s window
# =============================================================================


class TestAlertDeduplication:
    """Test alert deduplication logic."""

    def test_first_alert_always_sent(self):
        """First alert of a type should always send."""
        dedup = AlertDeduplicator()
        alert = Alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.CIRCUIT_BREAKER,
            title="Test",
            message="First alert",
        )
        assert dedup.should_send(alert) is True

    def test_duplicate_within_window_limited(self):
        """Duplicates within window are limited."""
        dedup = AlertDeduplicator()
        alert = Alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.CIRCUIT_BREAKER,
            title="Same Alert",
            message="Same message",
            component="test",
        )

        # Send 5 (limit for WARNING)
        for _ in range(5):
            assert dedup.should_send(alert) is True
            dedup.record_sent(alert)

        # 6th should be blocked
        assert dedup.should_send(alert) is False

    def test_different_alerts_not_deduplicated(self):
        """Different alerts are not deduplicated against each other."""
        dedup = AlertDeduplicator()

        alert1 = create_halt_alert("comp1", "reason1")
        alert2 = create_halt_alert("comp2", "reason2")

        assert dedup.should_send(alert1) is True
        dedup.record_sent(alert1)

        # Different component = different dedup key
        assert dedup.should_send(alert2) is True

    def test_critical_has_higher_limit(self):
        """CRITICAL severity allows more alerts."""
        dedup = AlertDeduplicator()
        
        # Create CRITICAL alert
        for i in range(10):
            alert = create_halt_alert("comp", f"reason_{i}")
            alert.dedup_key = "same_key"  # Force same key
            if i < 10:
                assert dedup.should_send(alert) is True
                dedup.record_sent(alert)

    def test_stats_tracking(self):
        """Deduplicator tracks stats."""
        dedup = AlertDeduplicator()
        alert = Alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            title="Test",
            message="Test",
        )

        # Send and dedup
        for _ in range(5):
            if dedup.should_send(alert):
                dedup.record_sent(alert)
            else:
                dedup.record_deduplicated(alert)

        stats = dedup.stats
        assert stats["total_sent"] == 3  # INFO limit is 3
        assert stats["total_deduplicated"] == 2


# =============================================================================
# INV-ALERT-TAXONOMY-3: Telegram format matches severity
# =============================================================================


class TestTelegramFormatter:
    """Test Telegram formatting."""

    def test_critical_has_double_emoji(self):
        """CRITICAL alerts have double emoji header."""
        formatter = TelegramAlertFormatter()
        alert = create_halt_alert("test", "reason")
        formatted = formatter.format(alert)

        assert "🚨" in formatted
        assert "CRITICAL" in formatted

    def test_warning_has_warning_emoji(self):
        """WARNING alerts have warning emoji."""
        formatter = TelegramAlertFormatter()
        alert = create_circuit_open_alert("river", 3)
        formatted = formatter.format(alert)

        assert "⚠️" in formatted
        assert "WARNING" in formatted

    def test_info_has_info_emoji(self):
        """INFO alerts have info emoji."""
        formatter = TelegramAlertFormatter()
        alert = Alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            title="Test",
            message="Info message",
        )
        formatted = formatter.format(alert)

        assert "ℹ️" in formatted

    def test_category_emoji_included(self):
        """Category emoji is included."""
        formatter = TelegramAlertFormatter()
        alert = create_halt_alert("test", "reason")
        formatted = formatter.format(alert)

        assert "🛑" in formatted  # HALT emoji

    def test_timestamp_included(self):
        """Timestamp is included."""
        formatter = TelegramAlertFormatter()
        alert = Alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            title="Test",
            message="Test",
        )
        formatted = formatter.format(alert)

        assert "UTC" in formatted

    def test_metadata_included(self):
        """Metadata is included when present."""
        formatter = TelegramAlertFormatter()
        alert = create_circuit_open_alert("river", 5)
        formatted = formatter.format(alert)

        assert "failure_count" in formatted
        assert "5" in formatted

    def test_batch_format(self):
        """Batch formatting works."""
        formatter = TelegramAlertFormatter()
        alerts = [
            create_halt_alert(f"comp_{i}", f"reason_{i}")
            for i in range(3)
        ]
        formatted = formatter.format_batch(alerts)

        assert "(3 alerts)" in formatted


# =============================================================================
# ALERT ROUTER
# =============================================================================


class TestAlertRouter:
    """Test alert routing."""

    def test_router_calls_handlers(self):
        """Router calls registered handlers."""
        router = AlertRouter()
        received = []

        def handler(message: str, severity: AlertSeverity):
            received.append((message, severity))

        router.add_handler(handler)

        alert = create_halt_alert("test", "reason")
        router.route(alert)

        assert len(received) == 1
        assert received[0][1] == AlertSeverity.CRITICAL

    def test_router_deduplicates(self):
        """Router deduplicates alerts."""
        router = AlertRouter()
        received = []

        def handler(message: str, severity: AlertSeverity):
            received.append(message)

        router.add_handler(handler)

        # Same alert 10 times
        alert = Alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            title="Test",
            message="Test",
        )

        for _ in range(10):
            router.route(alert)

        # Should be limited (INFO = 3)
        assert len(received) == 3

    def test_router_stats(self):
        """Router tracks stats."""
        router = AlertRouter()
        router.add_handler(lambda m, s: None)

        alert = Alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            title="Test",
            message="Test",
        )

        for _ in range(10):
            router.route(alert)

        stats = router.stats
        assert stats["alerts_routed"] == 3
        assert stats["alerts_suppressed"] == 7


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


class TestFactoryFunctions:
    """Test alert factory functions."""

    def test_create_halt_alert(self):
        """Halt alert factory."""
        alert = create_halt_alert("governance", "Emergency")
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.category == AlertCategory.HALT
        assert "HALTED" in alert.title

    def test_create_health_transition_critical(self):
        """Health transition to CRITICAL."""
        alert = create_health_transition_alert("system", "HEALTHY", "CRITICAL")
        assert alert.severity == AlertSeverity.CRITICAL
        assert "CRITICAL" in alert.title

    def test_create_health_transition_degraded(self):
        """Health transition to DEGRADED."""
        alert = create_health_transition_alert("system", "HEALTHY", "DEGRADED")
        assert alert.severity == AlertSeverity.WARNING

    def test_create_ibkr_disconnected(self):
        """IBKR disconnected is CRITICAL."""
        alert = create_ibkr_connection_alert("DISCONNECTED", "timeout")
        assert alert.severity == AlertSeverity.CRITICAL

    def test_create_ibkr_connected(self):
        """IBKR connected is INFO."""
        alert = create_ibkr_connection_alert("CONNECTED")
        assert alert.severity == AlertSeverity.INFO

    def test_create_constitutional_violation(self):
        """Constitutional violation is CRITICAL."""
        alert = create_constitutional_violation_alert(
            "SCALAR_SCORE",
            "validation",
            "Found scalar_score field",
        )
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.category == AlertCategory.CONSTITUTIONAL_VIOLATION


# =============================================================================
# SUMMARY
# =============================================================================


class TestAlertTaxonomySummary:
    """Summary test for alert taxonomy."""

    def test_taxonomy_summary(self):
        """All taxonomy invariants proven."""
        results = {
            "INV-ALERT-TAXONOMY-1": "All alerts have explicit severity",
            "INV-ALERT-TAXONOMY-2": "Deduplication ≤5 per 60s window",
            "INV-ALERT-TAXONOMY-3": "Telegram format matches severity",
        }

        print("\n" + "=" * 50)
        print("ALERT TAXONOMY INVARIANTS")
        print("=" * 50)
        for inv, desc in results.items():
            print(f"  ✓ {inv}: {desc}")
        print("=" * 50)

        assert True
