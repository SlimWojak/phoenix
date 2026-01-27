"""
Phoenix Notification Module — Telegram Integration
===================================================

Aggregated notifications to Telegram.
Uses python-telegram-bot directly (not Takopi bridge).

Components:
- TelegramNotifier: Send alerts to Telegram
- AlertAggregator: Batch and throttle alerts

PATTERN:
- Aggregate alerts over window (e.g., 5 min)
- Throttle per-alert-type
- Support inline keyboards for acknowledgment
"""

from .alert_aggregator import Alert, AlertAggregator
from .telegram_notifier import NotificationLevel, TelegramNotifier

__all__ = [
    "TelegramNotifier",
    "NotificationLevel",
    "AlertAggregator",
    "Alert",
]
