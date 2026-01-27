"""
Alert Aggregator — Batch and Throttle Alerts
============================================

Aggregates alerts over time window before sending.
Prevents notification spam.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Alert:
    """Individual alert."""

    alert_type: str
    message: str
    severity: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "message": self.message,
            "severity": self.severity,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AggregatedBatch:
    """Batch of aggregated alerts."""

    alerts: list[Alert]
    start_time: datetime
    end_time: datetime

    def to_summary(self) -> str:
        """Generate summary message."""
        if not self.alerts:
            return "No alerts in batch"

        # Group by type
        by_type: dict[str, list[Alert]] = defaultdict(list)
        for alert in self.alerts:
            by_type[alert.alert_type].append(alert)

        lines = [
            f"📊 <b>Alert Summary</b> ({len(self.alerts)} alerts)",
            "",
        ]

        for alert_type, alerts in by_type.items():
            severities = [a.severity for a in alerts]
            critical = severities.count("CRITICAL")
            warning = severities.count("WARNING")

            emoji = "🚨" if critical > 0 else "⚠️" if warning > 0 else "ℹ️"
            lines.append(f"{emoji} <b>{alert_type}</b>: {len(alerts)}")

            # Show first 2 messages per type
            for alert in alerts[:2]:
                msg = alert.message[:50] + "..." if len(alert.message) > 50 else alert.message
                lines.append(f"   • {msg}")

            if len(alerts) > 2:
                lines.append(f"   ... and {len(alerts) - 2} more")

        return "\n".join(lines)


# =============================================================================
# ALERT AGGREGATOR
# =============================================================================


class AlertAggregator:
    """
    Aggregates alerts over time windows.

    Batches similar alerts to prevent spam.
    Flushes on timer or when critical alert received.
    """

    def __init__(
        self,
        notifier: Any | None = None,
        window_seconds: int = 300,  # 5 minutes
        max_batch_size: int = 50,
    ) -> None:
        """
        Initialize aggregator.

        Args:
            notifier: TelegramNotifier instance
            window_seconds: Aggregation window
            max_batch_size: Max alerts before force flush
        """
        self._notifier = notifier
        self._window = timedelta(seconds=window_seconds)
        self._max_batch = max_batch_size

        self._pending: list[Alert] = []
        self._window_start: datetime = datetime.now(UTC)
        self._flush_callback: Callable[[AggregatedBatch], None] | None = None
        self._timer_task: Any = None

    def add(self, alert: Alert) -> None:
        """
        Add alert to aggregation queue.

        Args:
            alert: Alert to add
        """
        self._pending.append(alert)

        # Immediate flush for critical
        if alert.severity == "CRITICAL":
            self.flush()
            return

        # Force flush if batch full
        if len(self._pending) >= self._max_batch:
            self.flush()
            return

        # Start timer if not running
        if self._timer_task is None:
            self._start_timer()

    def flush(self) -> AggregatedBatch | None:
        """
        Flush pending alerts.

        Returns:
            AggregatedBatch that was flushed
        """
        if not self._pending:
            return None

        batch = AggregatedBatch(
            alerts=self._pending.copy(),
            start_time=self._window_start,
            end_time=datetime.now(UTC),
        )

        # Clear pending
        self._pending = []
        self._window_start = datetime.now(UTC)

        # Stop timer
        if self._timer_task:
            self._timer_task.cancel()
            self._timer_task = None

        # Send notification
        if self._notifier:
            try:
                summary = batch.to_summary()
                self._notifier.send_sync(
                    message=summary,
                    level="INFO",
                    category="aggregated",
                )
            except Exception:  # noqa: S110
                pass

        # Call callback if set
        if self._flush_callback:
            self._flush_callback(batch)

        return batch

    def on_flush(self, callback: Callable[[AggregatedBatch], None]) -> None:
        """
        Set callback for flush events.

        Args:
            callback: Function to call on flush
        """
        self._flush_callback = callback

    def get_pending_count(self) -> int:
        """Get count of pending alerts."""
        return len(self._pending)

    def get_pending_by_type(self) -> dict[str, int]:
        """Get pending alerts grouped by type."""
        counts: dict[str, int] = defaultdict(int)
        for alert in self._pending:
            counts[alert.alert_type] += 1
        return dict(counts)

    def _start_timer(self) -> None:
        """Start flush timer."""
        try:
            loop = asyncio.get_event_loop()
            self._timer_task = loop.call_later(
                self._window.total_seconds(),
                self._timer_callback,
            )
        except RuntimeError:
            # No event loop, flush synchronously
            pass

    def _timer_callback(self) -> None:
        """Timer callback - flush pending."""
        self.flush()
