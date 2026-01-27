"""
IBKR Configuration — Paper guards and mode management
======================================================

S33: FIRST_BLOOD

Manages IBKR connection modes and enforces paper-first guards.

INVARIANTS:
- INV-IBKR-PAPER-GUARD-1: Live mode requires IBKR_ALLOW_LIVE=true + restart
- INV-IBKR-ACCOUNT-CHECK-1: Every order submit validates account matches mode
- INV-IBKR-CONFIG-1: Credentials never in code, only .env
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class IBKRMode(Enum):
    """
    IBKR connection mode (tri-state).

    MOCK: Testing only, no external connections
    PAPER: Paper trading account (DU* prefix)
    LIVE: Real capital (U* prefix) - requires explicit enable
    """

    MOCK = "MOCK"
    PAPER = "PAPER"
    LIVE = "LIVE"


class ReconnectState(Enum):
    """Reconnection state machine."""

    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"
    ESCALATED = "ESCALATED"


@dataclass
class ReconnectConfig:
    """Reconnection strategy configuration."""

    max_attempts: int = 3
    backoff_delays: tuple[float, ...] = (5.0, 15.0, 45.0)  # Seconds
    max_time_sec: float = 65.0

    def get_delay(self, attempt: int) -> float:
        """Get delay for attempt number (0-indexed)."""
        if attempt < len(self.backoff_delays):
            return self.backoff_delays[attempt]
        return self.backoff_delays[-1]


@dataclass
class IBKRConfig:
    """
    IBKR connection configuration with paper guards.

    INVARIANT: INV-IBKR-PAPER-GUARD-1
    Live mode requires explicit IBKR_ALLOW_LIVE=true.

    INVARIANT: INV-IBKR-CONFIG-1
    All credentials loaded from environment, never hardcoded.
    """

    # Connection settings
    host: str = "127.0.0.1"
    client_id: int = 1
    timeout: float = 30.0
    readonly: bool = False

    # Mode and port (linked)
    mode: IBKRMode = IBKRMode.MOCK
    port: int = 4002  # Default to paper port

    # Account validation
    expected_account_prefix: str = "DU"  # Paper = DU*, Live = U*

    # Live enable flag (requires explicit opt-in)
    allow_live: bool = False

    # Reconnect settings
    reconnect: ReconnectConfig = field(default_factory=ReconnectConfig)

    # Port mappings (enforced)
    PAPER_PORT: int = field(default=4002, init=False)
    LIVE_PORT: int = field(default=4001, init=False)

    @classmethod
    def from_env(cls) -> IBKRConfig:
        """
        Load configuration from environment.

        ENV VARS:
            IBKR_HOST: Gateway host (default: 127.0.0.1)
            IBKR_PORT: Gateway port (default: 4002)
            IBKR_CLIENT_ID: Client ID (default: 1)
            IBKR_MODE: mock|paper|live (default: mock)
            IBKR_ALLOW_LIVE: true|false (default: false)

        INVARIANT: INV-IBKR-PAPER-GUARD-1
        Live mode blocked unless IBKR_ALLOW_LIVE=true.
        """
        mode_str = os.getenv("IBKR_MODE", "mock").upper()
        mode = IBKRMode(mode_str) if mode_str in [m.value for m in IBKRMode] else IBKRMode.MOCK

        allow_live = os.getenv("IBKR_ALLOW_LIVE", "false").lower() == "true"
        port = int(os.getenv("IBKR_PORT", "4002"))

        config = cls(
            host=os.getenv("IBKR_HOST", "127.0.0.1"),
            port=port,
            client_id=int(os.getenv("IBKR_CLIENT_ID", "1")),
            mode=mode,
            allow_live=allow_live,
        )

        # Set expected prefix and validate
        config._set_mode_defaults()

        return config

    def _set_mode_defaults(self) -> None:
        """Set mode-specific defaults and validate."""
        if self.mode == IBKRMode.MOCK:
            self.expected_account_prefix = "DU"  # Doesn't matter for mock
        elif self.mode == IBKRMode.PAPER:
            self.port = self.PAPER_PORT
            self.expected_account_prefix = "DU"
        elif self.mode == IBKRMode.LIVE:
            self.port = self.LIVE_PORT
            self.expected_account_prefix = "U"

    def validate_startup(self) -> tuple[bool, list[str]]:
        """
        Validate configuration at startup.

        INVARIANT: INV-IBKR-PAPER-GUARD-1
        Live mode requires IBKR_ALLOW_LIVE=true + restart.

        Returns:
            (valid, errors) tuple
        """
        errors: list[str] = []

        # Check live mode requires explicit enable
        if self.mode == IBKRMode.LIVE and not self.allow_live:
            errors.append(
                "INV-IBKR-PAPER-GUARD-1: Live mode requires IBKR_ALLOW_LIVE=true"
            )

        # Check port matches mode
        if self.mode == IBKRMode.PAPER and self.port != self.PAPER_PORT:
            errors.append(
                f"Port mismatch: PAPER mode expects port {self.PAPER_PORT}, got {self.port}"
            )

        if self.mode == IBKRMode.LIVE and self.port != self.LIVE_PORT:
            errors.append(
                f"Port mismatch: LIVE mode expects port {self.LIVE_PORT}, got {self.port}"
            )

        return (len(errors) == 0, errors)

    def validate_account(self, account_id: str) -> tuple[bool, str | None]:
        """
        Validate account ID matches expected mode.

        INVARIANT: INV-IBKR-ACCOUNT-CHECK-1
        Every order submit validates account matches mode.

        Args:
            account_id: Account ID from broker (e.g., "DU1234567")

        Returns:
            (valid, error_message) tuple
        """
        if self.mode == IBKRMode.MOCK:
            return (True, None)  # Mock accepts any account

        if not account_id.startswith(self.expected_account_prefix):
            return (
                False,
                f"INV-IBKR-ACCOUNT-CHECK-1: Account {account_id} doesn't match "
                f"expected prefix {self.expected_account_prefix} for {self.mode.value} mode",
            )

        return (True, None)

    def validate_order_context(
        self, account_id: str, current_port: int
    ) -> tuple[bool, list[str]]:
        """
        Validate order submission context.

        Called before EVERY order submit.

        INVARIANT: INV-IBKR-ACCOUNT-CHECK-1
        Account and port must match expected values.

        Args:
            account_id: Current account ID
            current_port: Current connection port

        Returns:
            (valid, errors) tuple
        """
        errors: list[str] = []

        # Validate account
        account_valid, account_error = self.validate_account(account_id)
        if not account_valid and account_error:
            errors.append(account_error)

        # Validate port
        expected_port = self.PAPER_PORT if self.mode == IBKRMode.PAPER else self.LIVE_PORT
        if self.mode != IBKRMode.MOCK and current_port != expected_port:
            errors.append(
                f"INV-IBKR-ACCOUNT-CHECK-1: Port {current_port} doesn't match "
                f"expected {expected_port} for {self.mode.value} mode"
            )

        return (len(errors) == 0, errors)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/bead emission."""
        return {
            "host": self.host,
            "port": self.port,
            "client_id": self.client_id,
            "mode": self.mode.value,
            "allow_live": self.allow_live,
            "expected_account_prefix": self.expected_account_prefix,
            "readonly": self.readonly,
        }


@dataclass
class ReconnectTracker:
    """
    Tracks reconnection state and attempts.

    INVARIANT: INV-IBKR-RECONNECT-1
    Max 3 reconnect attempts, then human escalation.
    """

    state: ReconnectState = ReconnectState.DISCONNECTED
    attempts: int = 0
    last_attempt_time: datetime | None = None
    escalated: bool = False
    config: ReconnectConfig = field(default_factory=ReconnectConfig)

    def start_reconnect(self) -> None:
        """Begin reconnection process."""
        self.state = ReconnectState.RECONNECTING
        self.attempts = 0
        self.escalated = False

    def record_attempt(self) -> tuple[bool, float]:
        """
        Record a reconnect attempt.

        Returns:
            (should_continue, next_delay_sec) tuple
        """
        self.attempts += 1
        self.last_attempt_time = datetime.now(UTC)

        if self.attempts >= self.config.max_attempts:
            self.state = ReconnectState.ESCALATED
            self.escalated = True
            return (False, 0.0)

        delay = self.config.get_delay(self.attempts - 1)
        return (True, delay)

    def record_success(self) -> None:
        """Record successful reconnection."""
        self.state = ReconnectState.CONNECTED
        self.attempts = 0
        self.escalated = False

    def record_disconnect(self) -> None:
        """Record disconnection."""
        self.state = ReconnectState.DISCONNECTED

    def needs_human_intervention(self) -> bool:
        """Check if human intervention required."""
        return self.escalated

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/bead emission."""
        return {
            "state": self.state.value,
            "attempts": self.attempts,
            "last_attempt_time": (
                self.last_attempt_time.isoformat() if self.last_attempt_time else None
            ),
            "escalated": self.escalated,
            "max_attempts": self.config.max_attempts,
        }
