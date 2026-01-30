"""
Phoenix Notification Module — Telegram Integration
===================================================

Aggregated notifications to Telegram.
Uses python-telegram-bot directly (not Takopi bridge).

Components:
- TelegramNotifier: Send alerts to Telegram
- AlertAggregator: Batch and throttle alerts
- AlertTaxonomy (S41): Severity classification + deduplication

PATTERN:
- Aggregate alerts over window (e.g., 5 min)
- Throttle per-alert-type
- Support inline keyboards for acknowledgment
- S41: Glanceable alerts with severity taxonomy
"""

from .alert_aggregator import Alert as LegacyAlert, AlertAggregator
from .alert_taxonomy import (
    Alert,
    AlertCategory,
    AlertDeduplicator,
    AlertRouter,
    AlertSeverity,
    TelegramAlertFormatter,
    create_circuit_open_alert,
    create_constitutional_violation_alert,
    create_halt_alert,
    create_health_transition_alert,
    create_ibkr_connection_alert,
    create_supervisor_alert,
)
from .telegram_notifier import NotificationLevel, TelegramNotifier

__all__ = [
    # Legacy
    "TelegramNotifier",
    "NotificationLevel",
    "AlertAggregator",
    "LegacyAlert",
    # S41 Taxonomy
    "Alert",
    "AlertSeverity",
    "AlertCategory",
    "AlertDeduplicator",
    "AlertRouter",
    "TelegramAlertFormatter",
    # Factory functions
    "create_halt_alert",
    "create_circuit_open_alert",
    "create_health_transition_alert",
    "create_ibkr_connection_alert",
    "create_supervisor_alert",
    "create_constitutional_violation_alert",
]
