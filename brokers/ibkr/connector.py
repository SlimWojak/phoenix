"""
IBKR Connector — Main broker interface
======================================

S32: EXECUTION_PATH

Wraps IBKR API (or mock) behind Phoenix interface.
Library isolation: ib_insync only imported here.

INVARIANTS:
- INV-T2-GATE-1: No order submission without valid T2 token
- INV-IBKR-MOCK-1: All tests use mock client
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol

from .account import AccountState
from .mock_client import MockIBKRClient
from .orders import Order, OrderResult, OrderStatus
from .positions import Position, PositionSnapshot

if TYPE_CHECKING:
    pass


class IBKRClientProtocol(Protocol):
    """Protocol for IBKR client implementations."""

    def connect(self) -> bool: ...
    def disconnect(self) -> None: ...
    def submit_order(self, order: Order) -> OrderResult: ...
    def cancel_order(self, order_id: str) -> bool: ...
    def get_positions(self) -> PositionSnapshot: ...
    def get_position(self, symbol: str) -> Position | None: ...
    def get_account(self) -> AccountState: ...


@dataclass
class ConnectionConfig:
    """IBKR connection configuration."""

    host: str = "127.0.0.1"
    port: int = 4002  # Paper trading port
    client_id: int = 1
    timeout: float = 30.0
    readonly: bool = False

    @classmethod
    def from_env(cls) -> ConnectionConfig:
        """Load config from environment."""
        return cls(
            host=os.getenv("IBKR_HOST", "127.0.0.1"),
            port=int(os.getenv("IBKR_PORT", "4002")),
            client_id=int(os.getenv("IBKR_CLIENT_ID", "1")),
        )


class IBKRConnector:
    """
    Main IBKR connector interface.

    Wraps either mock client (testing) or real ib_insync (production).

    INVARIANT: INV-T2-GATE-1
    Every order must have a valid T2 token.
    """

    def __init__(
        self,
        client: IBKRClientProtocol | None = None,
        config: ConnectionConfig | None = None,
        use_mock: bool = True,
    ) -> None:
        """
        Initialize connector.

        Args:
            client: Pre-configured client (for testing)
            config: Connection config
            use_mock: Use mock client (default True for safety)
        """
        self._config = config or ConnectionConfig.from_env()
        self._use_mock = use_mock

        if client is not None:
            self._client = client
        elif use_mock:
            self._client = MockIBKRClient()
        else:
            # Real ib_insync client would be created here
            # Deferred until S32 live testing phase
            raise NotImplementedError("Real IBKR client not yet implemented")

        self._connected = False
        self._token_validator: Any = None  # Injected by T2 workflow

    @property
    def connected(self) -> bool:
        """Check if connected to broker."""
        return self._connected

    def set_token_validator(self, validator: Any) -> None:
        """
        Set T2 token validator.

        Args:
            validator: Token validation callable
        """
        self._token_validator = validator

    # =========================================================================
    # CONNECTION
    # =========================================================================

    def connect(self) -> bool:
        """
        Connect to IBKR.

        Returns:
            True on success
        """
        try:
            result = self._client.connect()
            self._connected = result
            return result
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to IBKR: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from IBKR."""
        self._client.disconnect()
        self._connected = False

    # =========================================================================
    # ORDERS
    # =========================================================================

    def submit_order(self, order: Order) -> OrderResult:
        """
        Submit order to IBKR.

        INVARIANT: INV-T2-GATE-1
        Requires valid T2 token.

        Args:
            order: Order to submit

        Returns:
            OrderResult with fill details or error
        """
        # Validate T2 token (INV-T2-GATE-1)
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

        # Check connection
        if not self._connected:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.REJECTED,
                requested_quantity=order.quantity,
                message="Not connected to broker",
                errors=["Must connect before submitting orders"],
            )

        # Submit to client
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
        if not self._connected:
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
        if not self._connected:
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
        if not self._connected:
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
            "connected": self._connected,
            "use_mock": self._use_mock,
            "host": self._config.host,
            "port": self._config.port,
            "timestamp": datetime.now(UTC).isoformat(),
        }
