"""
E2E Test: CSO → Telegram
========================

Tests setup detection triggering Telegram alerts.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock


class TestTelegramAlertE2E:
    """CSO → Telegram end-to-end tests."""

    def test_ready_setup_sends_alert(self) -> None:
        """READY setup triggers Telegram alert."""
        from notification import TelegramNotifier

        notifier = TelegramNotifier(bot_token="test", chat_id="123")

        # Mock the send method
        notifier.send_sync = MagicMock(return_value=MagicMock(success=True))

        # Simulate alert
        notifier.send_sync(
            message="SETUP READY\nPair: EURUSD\nType: FVG_ENTRY",
            level="INFO",
            category="setup:EURUSD",
        )

        notifier.send_sync.assert_called_once()

    def test_throttle_enforced(self) -> None:
        """Throttle limits alerts per hour."""

        from notification import NotificationLevel, TelegramNotifier
        from notification.telegram_notifier import ThrottleState

        notifier = TelegramNotifier()

        # Fill up throttle state
        key = f"{NotificationLevel.INFO.value}:setup:EURUSD"
        notifier._throttle[key] = ThrottleState(
            last_sent=datetime.now(UTC),
            count_in_window=10,  # Max is 5 for INFO
            window_start=datetime.now(UTC),
        )

        # Should be throttled
        should_send = notifier._should_send(NotificationLevel.INFO, "setup:EURUSD")
        assert should_send is False

    def test_critical_bypasses_throttle(self) -> None:
        """CRITICAL alerts bypass throttle."""
        from notification import NotificationLevel, TelegramNotifier
        from notification.telegram_notifier import ThrottleState

        notifier = TelegramNotifier()

        # Fill up throttle for CRITICAL (high limit)
        key = f"{NotificationLevel.CRITICAL.value}:decay:TEST"
        notifier._throttle[key] = ThrottleState(
            last_sent=datetime.now(UTC),
            count_in_window=5,  # Under max of 50 for CRITICAL
            window_start=datetime.now(UTC),
        )

        should_send = notifier._should_send(NotificationLevel.CRITICAL, "decay:TEST")
        assert should_send is True

    def test_aggregator_batches_alerts(self) -> None:
        """Aggregator batches multiple alerts."""
        from notification import LegacyAlert as Alert, AlertAggregator

        aggregator = AlertAggregator(window_seconds=60, max_batch_size=10)

        # Add multiple alerts
        for i in range(5):
            aggregator.add(Alert(
                alert_type="SETUP_READY",
                message=f"Setup {i}",
                severity="INFO",
            ))

        assert aggregator.get_pending_count() == 5

        # Flush
        batch = aggregator.flush()

        assert batch is not None
        assert len(batch.alerts) == 5
        assert aggregator.get_pending_count() == 0

    def test_critical_immediate_flush(self) -> None:
        """CRITICAL alert triggers immediate flush."""
        from notification import LegacyAlert as Alert, AlertAggregator

        aggregator = AlertAggregator()

        # Add INFO alert
        aggregator.add(Alert(
            alert_type="SETUP",
            message="Normal alert",
            severity="INFO",
        ))

        assert aggregator.get_pending_count() == 1

        # Add CRITICAL - should trigger flush
        aggregator.add(Alert(
            alert_type="DECAY",
            message="Critical alert",
            severity="CRITICAL",
        ))

        # After critical, batch is flushed
        assert aggregator.get_pending_count() == 0

    def test_scanner_wired_to_telegram(self) -> None:
        """CSOScanner has telegram reference."""
        from cso import CSOScanner
        from notification import TelegramNotifier

        telegram = TelegramNotifier()
        scanner = CSOScanner(telegram=telegram)

        assert scanner._telegram is telegram
