"""
Telegram Notifier — Direct Telegram Integration
================================================

Sends notifications directly to Telegram.
Uses python-telegram-bot library.

Features:
- Inline keyboards for acknowledgment
- Throttling per notification type
- HTML formatting
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

# =============================================================================
# ENUMS
# =============================================================================


class NotificationLevel(str, Enum):
    """Notification severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    SUCCESS = "SUCCESS"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class NotificationResult:
    """Result of notification send."""

    success: bool
    message_id: int | None = None
    error: str | None = None


@dataclass
class ThrottleState:
    """Throttle state for notification type."""

    last_sent: datetime | None = None
    count_in_window: int = 0
    window_start: datetime = field(default_factory=lambda: datetime.now(UTC))


# =============================================================================
# TELEGRAM NOTIFIER
# =============================================================================


class TelegramNotifier:
    """
    Sends notifications to Telegram.

    Uses python-telegram-bot directly.
    Supports inline keyboards and throttling.
    """

    # Throttle settings per level
    THROTTLE_WINDOWS = {
        NotificationLevel.INFO: timedelta(minutes=15),
        NotificationLevel.WARNING: timedelta(minutes=5),
        NotificationLevel.CRITICAL: timedelta(seconds=30),
        NotificationLevel.SUCCESS: timedelta(minutes=10),
    }

    MAX_IN_WINDOW = {
        NotificationLevel.INFO: 5,
        NotificationLevel.WARNING: 10,
        NotificationLevel.CRITICAL: 50,  # Don't throttle criticals much
        NotificationLevel.SUCCESS: 10,
    }

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
    ) -> None:
        """
        Initialize notifier.

        Args:
            bot_token: Telegram bot token (or from env)
            chat_id: Telegram chat ID (or from env)
        """
        self._token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self._throttle: dict[str, ThrottleState] = {}
        self._bot: Any = None

    async def _get_bot(self) -> Any:
        """Get or create bot instance."""
        if self._bot is None:
            try:
                from telegram import Bot

                self._bot = Bot(token=self._token)
            except ImportError:
                return None
        return self._bot

    async def send(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        category: str = "general",
        keyboard: list[list[dict]] | None = None,
    ) -> NotificationResult:
        """
        Send notification to Telegram.

        Args:
            message: Message text (HTML supported)
            level: Notification level
            category: Category for throttling
            keyboard: Optional inline keyboard

        Returns:
            NotificationResult
        """
        # Check throttle
        if not self._should_send(level, category):
            return NotificationResult(
                success=False,
                error="Throttled",
            )

        # Format message
        formatted = self._format_message(message, level)

        # Get bot
        bot = await self._get_bot()
        if bot is None:
            return NotificationResult(
                success=False,
                error="Bot not available",
            )

        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            # Build keyboard if provided
            reply_markup = None
            if keyboard:
                buttons = [
                    [
                        InlineKeyboardButton(
                            text=btn.get("text", ""),
                            callback_data=btn.get("callback_data", ""),
                        )
                        for btn in row
                    ]
                    for row in keyboard
                ]
                reply_markup = InlineKeyboardMarkup(buttons)

            # Send message
            result = await bot.send_message(
                chat_id=self._chat_id,
                text=formatted,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )

            # Update throttle state
            self._update_throttle(level, category)

            return NotificationResult(
                success=True,
                message_id=result.message_id,
            )

        except Exception as e:
            return NotificationResult(
                success=False,
                error=str(e),
            )

    async def send_decay_alert(
        self,
        strategy_id: str,
        severity: str,
        reason: str,
        signals: list[dict],
    ) -> NotificationResult:
        """
        Send decay alert with action buttons.

        Args:
            strategy_id: Affected strategy
            severity: Alert severity
            reason: Alert reason
            signals: Decay signals

        Returns:
            NotificationResult
        """
        emoji = {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️"}.get(severity, "ℹ️")

        message = f"""
{emoji} <b>DECAY ALERT</b>

<b>Strategy:</b> <code>{strategy_id}</code>
<b>Severity:</b> {severity}
<b>Reason:</b> {reason}

<b>Signals:</b>
"""
        for signal in signals[:3]:
            message += f"• {signal.get('decay_type', 'N/A')}: {signal.get('value', 0):.3f}\n"

        # Add action buttons
        level = NotificationLevel.CRITICAL if severity == "CRITICAL" else NotificationLevel.WARNING

        keyboard = None
        if severity == "CRITICAL":
            keyboard = [
                [
                    {"text": "Acknowledge", "callback_data": f"ack:{strategy_id}"},
                    {"text": "Dismiss", "callback_data": f"dismiss:{strategy_id}"},
                ]
            ]

        return await self.send(
            message=message,
            level=level,
            category=f"decay:{strategy_id}",
            keyboard=keyboard,
        )

    async def send_setup_alert(
        self,
        pair: str,
        setup_type: str,
        direction: str,
        confidence: float,
    ) -> NotificationResult:
        """
        Send setup ready alert.

        Args:
            pair: Currency pair
            setup_type: Type of setup
            direction: Trade direction
            confidence: Setup confidence

        Returns:
            NotificationResult
        """
        emoji = "📈" if direction == "BULLISH" else "📉"

        message = f"""
{emoji} <b>SETUP READY</b>

<b>Pair:</b> {pair}
<b>Type:</b> {setup_type}
<b>Direction:</b> {direction}
<b>Confidence:</b> {confidence:.1%}
"""

        return await self.send(
            message=message,
            level=NotificationLevel.INFO,
            category=f"setup:{pair}",
        )

    async def send_position_update(
        self,
        pair: str,
        action: str,
        entry: float,
        pnl: float | None = None,
    ) -> NotificationResult:
        """
        Send position update.

        Args:
            pair: Currency pair
            action: OPENED, CLOSED, SL_HIT, TP_HIT
            entry: Entry price
            pnl: P&L if closed

        Returns:
            NotificationResult
        """
        emoji_map = {
            "OPENED": "🟢",
            "CLOSED": "⚪",
            "SL_HIT": "🔴",
            "TP_HIT": "🟢",
        }
        emoji = emoji_map.get(action, "⚪")

        message = f"""
{emoji} <b>POSITION {action}</b>

<b>Pair:</b> {pair}
<b>Entry:</b> {entry:.5f}
"""
        if pnl is not None:
            pnl_emoji = "✅" if pnl >= 0 else "❌"
            message += f"<b>P&L:</b> {pnl_emoji} {pnl:+.2f}%\n"

        level = NotificationLevel.SUCCESS if action == "TP_HIT" else NotificationLevel.INFO

        return await self.send(
            message=message,
            level=level,
            category=f"position:{pair}",
        )

    def send_sync(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        category: str = "general",
    ) -> NotificationResult:
        """
        Synchronous send wrapper.

        Args:
            message: Message text
            level: Notification level
            category: Category for throttling

        Returns:
            NotificationResult
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send(message, level, category))

    def _should_send(self, level: NotificationLevel, category: str) -> bool:
        """Check if notification should be sent (throttle check)."""
        key = f"{level.value}:{category}"
        state = self._throttle.get(key)

        if state is None:
            return True

        now = datetime.now(UTC)
        window = self.THROTTLE_WINDOWS.get(level, timedelta(minutes=5))
        max_count = self.MAX_IN_WINDOW.get(level, 10)

        # Check if window expired
        if state.window_start + window < now:
            return True

        # Check count in window
        return state.count_in_window < max_count

    def _update_throttle(self, level: NotificationLevel, category: str) -> None:
        """Update throttle state after send."""
        key = f"{level.value}:{category}"
        now = datetime.now(UTC)
        window = self.THROTTLE_WINDOWS.get(level, timedelta(minutes=5))

        state = self._throttle.get(key)

        if state is None or state.window_start + window < now:
            # New window
            self._throttle[key] = ThrottleState(
                last_sent=now,
                count_in_window=1,
                window_start=now,
            )
        else:
            # Update existing
            state.last_sent = now
            state.count_in_window += 1

    def _format_message(self, message: str, level: NotificationLevel) -> str:
        """Format message with level indicator."""
        timestamp = datetime.now(UTC).strftime("%H:%M UTC")

        return f"{message}\n\n<i>{timestamp}</i>"
