"""
IBKR Connector — Main broker interface with paper guards
=========================================================

S33: FIRST_BLOOD

Wraps IBKR API (mock or real) behind Phoenix interface.
Enforces paper-first guards on all operations.

INVARIANTS:
- INV-T2-GATE-1: No order submission without valid T2 token
- INV-IBKR-PAPER-GUARD-1: Live mode requires IBKR_ALLOW_LIVE=true + restart
- INV-IBKR-ACCOUNT-CHECK-1: Every order submit validates account matches mode
- INV-IBKR-RECONNECT-1: Max 3 reconnect attempts, then human escalation
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Callable, Protocol

from .account import AccountState
from .config import IBKRConfig, IBKRMode, ReconnectTracker
from .mock_client import MockIBKRClient
from .orders import Order, OrderResult, OrderStatus
from .positions import Position, PositionSnapshot
from .session_bead import SessionBeadData, SessionBeadEmitter

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IBKRClientProtocol(Protocol):
    """Protocol for IBKR client implementations."""

    def connect(self) -> bool: ...
    def disconnect(self) -> None: ...
    def submit_order(self, order: Order) -> OrderResult: ...
    def cancel_order(self, order_id: str) -> bool: ...
    def get_positions(self) -> PositionSnapshot: ...
    def get_position(self, symbol: str) -> Position | None: ...
    def get_account(self) -> AccountState: ...


# Type for token validator callback
TokenValidator = Callable[[str, Order], Any]

# Type for alert callback
AlertCallback = Callable[[str, str, dict[str, Any]], None]


@dataclass
class ConnectionState:
    """Tracks connection state."""

    connected: bool = False
    account_id: str = ""
    port: int = 0
    connect_time: datetime | None = None
    last_activity: datetime | None = None


class IBKRConnector:
    """
    Main IBKR connector interface with paper guards.

    Wraps either mock client (testing) or real ib_insync (production).

    INVARIANT: INV-T2-GATE-1
    Every order must have a valid T2 token.

    INVARIANT: INV-IBKR-PAPER-GUARD-1
    Live mode requires IBKR_ALLOW_LIVE=true + restart.

    INVARIANT: INV-IBKR-ACCOUNT-CHECK-1
    Every order submit validates account matches mode.

    INVARIANT: INV-IBKR-RECONNECT-1
    Max 3 reconnect attempts, then human escalation.
    """

    def __init__(
        self,
        client: IBKRClientProtocol | None = None,
        config: IBKRConfig | None = None,
        bead_emitter: Callable[[SessionBeadData], None] | None = None,
        alert_callback: AlertCallback | None = None,
    ) -> None:
        """
        Initialize connector with paper guards.

        Args:
            client: Pre-configured client (for testing)
            config: IBKR configuration
            bead_emitter: Callback for session bead emission
            alert_callback: Callback for alerts

        Raises:
            ValueError: If config validation fails for live mode
        """
        self._config = config or IBKRConfig.from_env()

        # Validate startup config (INV-IBKR-PAPER-GUARD-1)
        valid, errors = self._config.validate_startup()
        if not valid:
            raise ValueError(f"Config validation failed: {errors}")

        # Initialize client based on mode
        if client is not None:
            self._client = client
        else:
            self._client = self._create_client()

        # Connection state
        self._state = ConnectionState()

        # Reconnect tracking (INV-IBKR-RECONNECT-1)
        self._reconnect = ReconnectTracker(config=self._config.reconnect)

        # Session bead emitter
        self._session_bead = SessionBeadEmitter(bead_emitter)

        # Alert callback
        self._alert_callback = alert_callback

        # T2 token validator
        self._token_validator: TokenValidator | None = None

    def _create_client(self) -> IBKRClientProtocol:
        """Create appropriate client for mode."""
        if self._config.mode == IBKRMode.MOCK:
            return MockIBKRClient()

        # Real client for PAPER and LIVE
        try:
            from .real_client import RealIBKRClient

            return RealIBKRClient(self._config)
        except ImportError as e:
            logger.error(f"Cannot create real client: {e}")
            raise

    @property
    def connected(self) -> bool:
        """Check if connected to broker."""
        return self._state.connected

    @property
    def mode(self) -> IBKRMode:
        """Current connection mode."""
        return self._config.mode

    @property
    def account_id(self) -> str:
        """Current account ID."""
        return self._state.account_id

    def set_token_validator(self, validator: TokenValidator) -> None:
        """
        Set T2 token validator.

        Args:
            validator: Token validation callable
        """
        self._token_validator = validator

    def set_bead_emitter(self, emitter: Callable[[SessionBeadData], None]) -> None:
        """Set bead emission callback."""
        self._session_bead.set_emitter(emitter)

    def set_alert_callback(self, callback: AlertCallback) -> None:
        """Set alert callback."""
        self._alert_callback = callback

    # =========================================================================
    # CONNECTION
    # =========================================================================

    def connect(self) -> bool:
        """
        Connect to IBKR with paper guards.

        INVARIANT: INV-IBKR-PAPER-GUARD-1
        Validates mode and account on connect.

        Returns:
            True on success

        Raises:
            ConnectionError: On connection failure
            ValueError: On account mismatch
        """
        try:
            result = self._client.connect()

            if result:
                # Get account info
                account = self._client.get_account()
                self._state.account_id = account.account_id if account else ""
                self._state.port = self._config.port
                self._state.connected = True
                self._state.connect_time = datetime.now(UTC)

                # Validate account matches mode (INV-IBKR-ACCOUNT-CHECK-1)
                if self._config.mode != IBKRMode.MOCK:
                    valid, error = self._config.validate_account(self._state.account_id)
                    if not valid:
                        self.disconnect()
                        raise ValueError(error)

                # Emit CONNECT bead
                gateway_version = self._get_gateway_version()
                self._session_bead.emit_connect(
                    mode=self._config.mode.value,
                    account=self._state.account_id,
                    port=self._state.port,
                    gateway_version=gateway_version,
                )

                # Reset reconnect tracker
                self._reconnect.record_success()

                logger.info(
                    f"Connected to IBKR: mode={self._config.mode.value}, "
                    f"account={self._state.account_id}, port={self._state.port}"
                )

            return result

        except Exception as e:
            self._state.connected = False
            logger.error(f"IBKR connection failed: {e}")
            raise ConnectionError(f"Failed to connect to IBKR: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from IBKR and emit bead."""
        was_connected = self._state.connected

        self._client.disconnect()
        self._state.connected = False

        # Emit DISCONNECT bead if we were connected
        if was_connected:
            self._session_bead.emit_disconnect(
                mode=self._config.mode.value,
                account=self._state.account_id,
                port=self._state.port,
            )
            self._reconnect.record_disconnect()

        logger.info("Disconnected from IBKR")

    def reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.

        INVARIANT: INV-IBKR-RECONNECT-1
        Max 3 reconnect attempts, then human escalation.

        Returns:
            True on successful reconnection
        """
        self._reconnect.start_reconnect()

        while True:
            should_continue, delay = self._reconnect.record_attempt()

            if not should_continue:
                # Escalate to human (INV-IBKR-RECONNECT-1)
                self._escalate_connection_failure()
                return False

            # Emit RECONNECT bead
            self._session_bead.emit_reconnect(
                mode=self._config.mode.value,
                account=self._state.account_id,
                port=self._state.port,
                attempt=self._reconnect.attempts,
            )

            logger.info(
                f"Reconnect attempt {self._reconnect.attempts}, "
                f"waiting {delay}s before retry"
            )

            # Wait before retry
            time.sleep(delay)

            # Try to connect
            try:
                if self.connect():
                    logger.info(
                        f"Reconnected after {self._reconnect.attempts} attempts"
                    )
                    return True
            except Exception as e:
                logger.warning(f"Reconnect attempt failed: {e}")

        return False

    def _escalate_connection_failure(self) -> None:
        """Escalate to human after max reconnect attempts."""
        logger.critical(
            f"IBKR connection failed after {self._reconnect.attempts} attempts. "
            "Human intervention required. See RB-001."
        )

        # Fire alert
        if self._alert_callback:
            self._alert_callback(
                "CRITICAL",
                "IBKR connection rotting — run RB-001",
                self._reconnect.to_dict(),
            )

    def _get_gateway_version(self) -> str | None:
        """Try to get gateway version."""
        try:
            if hasattr(self._client, "gateway_version"):
                return self._client.gateway_version  # type: ignore
        except Exception:
            pass
        return None

    # =========================================================================
    # ORDERS
    # =========================================================================

    def submit_order(self, order: Order) -> OrderResult:
        """
        Submit order to IBKR with all guards.

        GUARD ORDER:
        1. Account guard (INV-IBKR-ACCOUNT-CHECK-1)
        2. Port guard (INV-IBKR-ACCOUNT-CHECK-1)
        3. Token guard (INV-T2-GATE-1)
        4. Submit

        Args:
            order: Order to submit

        Returns:
            OrderResult with fill details or error
        """
        self._state.last_activity = datetime.now(UTC)

        # =====================================================================
        # GUARD 1: Account + Port validation (INV-IBKR-ACCOUNT-CHECK-1)
        # =====================================================================
        if self._config.mode != IBKRMode.MOCK:
            valid, errors = self._config.validate_order_context(
                self._state.account_id, self._state.port
            )
            if not valid:
                logger.error(f"Order context validation failed: {errors}")
                return OrderResult(
                    success=False,
                    order_id=order.order_id,
                    status=OrderStatus.REJECTED,
                    requested_quantity=order.quantity,
                    message="Account/port validation failed",
                    errors=errors,
                )

        # =====================================================================
        # GUARD 2: T2 token validation (INV-T2-GATE-1)
        # =====================================================================
        if order.token_id is None:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.REJECTED,
                requested_quantity=order.quantity,
                message="T2 token required",
                errors=["INV-T2-GATE-1: No order submission without valid T2 token"],
            )

        # Validate token if validator available
        if self._token_validator is not None:
            validation = self._token_validator(order.token_id, order)
            if not validation.valid:
                return OrderResult(
                    success=False,
                    order_id=order.order_id,
                    status=OrderStatus.REJECTED,
                    requested_quantity=order.quantity,
                    message="Token validation failed",
                    errors=validation.errors,
                )

        # =====================================================================
        # GUARD 3: Connection check
        # =====================================================================
        if not self._state.connected:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.REJECTED,
                requested_quantity=order.quantity,
                message="Not connected to broker",
                errors=["Must connect before submitting orders"],
            )

        # =====================================================================
        # SUBMIT: All guards passed
        # =====================================================================
        logger.info(
            f"Submitting order: {order.order_id}, symbol={order.symbol}, "
            f"side={order.side.value}, qty={order.quantity}"
        )

        return self._client.submit_order(order)

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order to cancel

        Returns:
            True if cancelled
        """
        return self._client.cancel_order(order_id)

    # =========================================================================
    # POSITIONS
    # =========================================================================

    def get_positions(self) -> PositionSnapshot:
        """
        Get all positions from broker.

        Returns:
            PositionSnapshot with current positions
        """
        if not self._state.connected:
            return PositionSnapshot()
        return self._client.get_positions()

    def get_position(self, symbol: str) -> Position | None:
        """
        Get position for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position or None
        """
        if not self._state.connected:
            return None
        return self._client.get_position(symbol)

    # =========================================================================
    # ACCOUNT
    # =========================================================================

    def get_account(self) -> AccountState | None:
        """
        Get account state.

        Returns:
            AccountState or None if not connected
        """
        if not self._state.connected:
            return None
        return self._client.get_account()

    # =========================================================================
    # HEALTH
    # =========================================================================

    def health_check(self) -> dict[str, Any]:
        """
        Check connector health.

        Returns:
            Health status dictionary
        """
        return {
            "connected": self._state.connected,
            "mode": self._config.mode.value,
            "account_id": self._state.account_id,
            "port": self._state.port,
            "connect_time": (
                self._state.connect_time.isoformat()
                if self._state.connect_time
                else None
            ),
            "last_activity": (
                self._state.last_activity.isoformat()
                if self._state.last_activity
                else None
            ),
            "reconnect_state": self._reconnect.to_dict(),
            "config": self._config.to_dict(),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_reconnect_state(self) -> dict[str, Any]:
        """Get reconnect state for monitoring."""
        return self._reconnect.to_dict()

    def needs_human_intervention(self) -> bool:
        """Check if human intervention required due to connection issues."""
        return self._reconnect.needs_human_intervention()


# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================
# Preserve old ConnectionConfig for backwards compatibility with S32 code


@dataclass
class ConnectionConfig:
    """
    DEPRECATED: Use IBKRConfig instead.

    Legacy connection configuration for backwards compatibility.
    """

    host: str = "127.0.0.1"
    port: int = 4002
    client_id: int = 1
    timeout: float = 30.0
    readonly: bool = False

    @classmethod
    def from_env(cls) -> ConnectionConfig:
        """Load config from environment."""
        import os

        return cls(
            host=os.getenv("IBKR_HOST", "127.0.0.1"),
            port=int(os.getenv("IBKR_PORT", "4002")),
            client_id=int(os.getenv("IBKR_CLIENT_ID", "1")),
        )
