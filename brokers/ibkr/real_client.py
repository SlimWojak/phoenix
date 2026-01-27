"""
IBKR Real Client — ib_insync wrapper
=====================================

S33: FIRST_BLOOD

Wraps ib_insync library for real IBKR connections.
All ib_insync imports isolated here (zero leakage).

INVARIANTS:
- INV-IBKR-PAPER-FIRST-1: Paper validation before live
- INV-IBKR-ACCOUNT-CHECK-1: Every order validates account
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .account import AccountState
from .config import IBKRConfig, IBKRMode
from .orders import Order, OrderResult, OrderStatus, OrderSide
from .positions import Position, PositionSnapshot

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Try to import ib_insync (may not be available in test environments)
try:
    from ib_insync import IB, Contract, MarketOrder, LimitOrder
    from ib_insync import Position as IBPosition
    from ib_insync import Trade

    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    logger.warning("ib_insync not available - real IBKR connections disabled")


@dataclass
class RealClientState:
    """Tracks real client state."""

    connected: bool = False
    account_id: str = ""
    port: int = 0
    gateway_version: str = ""
    last_heartbeat: datetime | None = None


class RealIBKRClient:
    """
    Real IBKR client wrapping ib_insync.

    INVARIANT: INV-IBKR-PAPER-FIRST-1
    Paper trading validation required before live.

    INVARIANT: INV-IBKR-ACCOUNT-CHECK-1
    Every order submit validates account matches mode.
    """

    def __init__(self, config: IBKRConfig) -> None:
        """
        Initialize real client.

        Args:
            config: IBKR configuration with paper guards

        Raises:
            ImportError: If ib_insync not available
            ValueError: If config validation fails
        """
        if not IB_AVAILABLE:
            raise ImportError(
                "ib_insync library not installed. "
                "Install with: pip install ib_insync"
            )

        # Validate config at startup (INV-IBKR-PAPER-GUARD-1)
        valid, errors = config.validate_startup()
        if not valid:
            raise ValueError(f"Config validation failed: {errors}")

        self._config = config
        self._ib: IB | None = None
        self._state = RealClientState()

        # Callbacks for events
        self._on_disconnect: list[Any] = []
        self._on_error: list[Any] = []

    @property
    def connected(self) -> bool:
        """Check if connected."""
        return self._state.connected and self._ib is not None and self._ib.isConnected()

    @property
    def account_id(self) -> str:
        """Current account ID."""
        return self._state.account_id

    @property
    def gateway_version(self) -> str:
        """Gateway version string."""
        return self._state.gateway_version

    # =========================================================================
    # CONNECTION
    # =========================================================================

    def connect(self) -> bool:
        """
        Connect to IB Gateway.

        INVARIANT: INV-IBKR-PAPER-FIRST-1
        Validates account matches expected mode.

        Returns:
            True on success

        Raises:
            ConnectionError: On connection failure
        """
        if self._config.mode == IBKRMode.MOCK:
            raise ValueError("RealIBKRClient cannot be used in MOCK mode")

        self._ib = IB()

        try:
            self._ib.connect(
                host=self._config.host,
                port=self._config.port,
                clientId=self._config.client_id,
                timeout=self._config.timeout,
                readonly=self._config.readonly,
            )

            # Get account info
            accounts = self._ib.managedAccounts()
            if not accounts:
                raise ConnectionError("No accounts returned from IBKR")

            self._state.account_id = accounts[0]
            self._state.port = self._config.port
            self._state.connected = True

            # Try to get gateway version
            self._state.gateway_version = self._get_gateway_version()

            # Validate account matches mode (INV-IBKR-ACCOUNT-CHECK-1)
            valid, error = self._config.validate_account(self._state.account_id)
            if not valid:
                self.disconnect()
                raise ValueError(error)

            logger.info(
                f"Connected to IBKR: account={self._state.account_id}, "
                f"port={self._state.port}, mode={self._config.mode.value}"
            )

            # Set up disconnect handler
            self._ib.disconnectedEvent += self._handle_disconnect

            return True

        except Exception as e:
            self._state.connected = False
            logger.error(f"IBKR connection failed: {e}")
            raise ConnectionError(f"Failed to connect to IBKR: {e}") from e

    def disconnect(self) -> None:
        """Disconnect from IB Gateway."""
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()

        self._state.connected = False
        logger.info("Disconnected from IBKR")

    def _handle_disconnect(self) -> None:
        """Handle unexpected disconnect."""
        self._state.connected = False
        logger.warning("IBKR connection lost")

        for callback in self._on_disconnect:
            try:
                callback()
            except Exception as e:
                logger.error(f"Disconnect callback error: {e}")

    def _get_gateway_version(self) -> str:
        """Try to get gateway version."""
        try:
            if self._ib:
                # serverVersion returns an int
                return f"IB Gateway {self._ib.client.serverVersion()}"
        except Exception:
            pass
        return "unknown"

    def on_disconnect(self, callback: Any) -> None:
        """Register disconnect callback."""
        self._on_disconnect.append(callback)

    def on_error(self, callback: Any) -> None:
        """Register error callback."""
        self._on_error.append(callback)

    # =========================================================================
    # ORDERS
    # =========================================================================

    def submit_order(self, order: Order) -> OrderResult:
        """
        Submit order to IBKR.

        INVARIANT: INV-IBKR-ACCOUNT-CHECK-1
        Validates account and port before every order.

        Args:
            order: Order to submit

        Returns:
            OrderResult with fill details or error
        """
        if not self.connected:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.REJECTED,
                requested_quantity=order.quantity,
                message="Not connected to broker",
                errors=["Must connect before submitting orders"],
            )

        # Validate order context (INV-IBKR-ACCOUNT-CHECK-1)
        valid, errors = self._config.validate_order_context(
            self._state.account_id, self._state.port
        )
        if not valid:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.REJECTED,
                requested_quantity=order.quantity,
                message="Order context validation failed",
                errors=errors,
            )

        # Validate order itself
        validation_errors = order.validate()
        if validation_errors:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.REJECTED,
                requested_quantity=order.quantity,
                message="Order validation failed",
                errors=validation_errors,
            )

        try:
            # Create contract
            contract = self._create_forex_contract(order.symbol)

            # Create order
            ib_order = self._create_ib_order(order)

            # Place order
            trade = self._ib.placeOrder(contract, ib_order)

            # Wait for fill (with timeout)
            self._ib.sleep(2)  # Give time for fill

            return self._trade_to_result(trade, order)

        except Exception as e:
            logger.error(f"Order submission failed: {e}")
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.REJECTED,
                requested_quantity=order.quantity,
                message=f"Order submission error: {e}",
                errors=[str(e)],
            )

    def _create_forex_contract(self, symbol: str) -> Contract:
        """Create forex contract from symbol."""
        # Parse symbol (e.g., "EURUSD" -> EUR.USD)
        if len(symbol) == 6:
            base = symbol[:3]
            quote = symbol[3:]
        else:
            base = symbol
            quote = "USD"

        contract = Contract()
        contract.symbol = base
        contract.secType = "CASH"
        contract.currency = quote
        contract.exchange = "IDEALPRO"

        return contract

    def _create_ib_order(self, order: Order) -> MarketOrder | LimitOrder:
        """Create IB order from Phoenix order."""
        action = "BUY" if order.side == OrderSide.BUY else "SELL"

        # S33: MARKET orders only
        return MarketOrder(action, order.quantity)

    def _trade_to_result(self, trade: Trade, order: Order) -> OrderResult:
        """Convert IB Trade to OrderResult."""
        status_map = {
            "Submitted": OrderStatus.SUBMITTED,
            "Filled": OrderStatus.FILLED,
            "Cancelled": OrderStatus.CANCELLED,
            "Inactive": OrderStatus.REJECTED,
        }

        ib_status = trade.orderStatus.status
        status = status_map.get(ib_status, OrderStatus.SUBMITTED)

        fill_price = None
        filled_qty = 0.0

        if trade.fills:
            fill_price = trade.fills[-1].execution.avgPrice
            filled_qty = sum(f.execution.shares for f in trade.fills)

        return OrderResult(
            success=status in (OrderStatus.FILLED, OrderStatus.SUBMITTED),
            order_id=order.order_id,
            status=status,
            broker_order_id=str(trade.order.orderId),
            fill_price=fill_price,
            filled_quantity=filled_qty,
            requested_quantity=order.quantity,
            message=f"Order {ib_status}",
        )

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        # In real implementation, would need to track order ID mapping
        logger.warning(f"cancel_order not fully implemented: {order_id}")
        return False

    # =========================================================================
    # POSITIONS
    # =========================================================================

    def get_positions(self) -> PositionSnapshot:
        """Get all positions from broker."""
        if not self.connected:
            return PositionSnapshot()

        try:
            ib_positions = self._ib.positions()
            positions = [self._ib_position_to_phoenix(p) for p in ib_positions]

            return PositionSnapshot(
                positions=positions,
                account=self._state.account_id,
                timestamp=datetime.now(UTC),
            )
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return PositionSnapshot()

    def get_position(self, symbol: str) -> Position | None:
        """Get position for symbol."""
        snapshot = self.get_positions()
        for pos in snapshot.positions:
            if pos.symbol == symbol:
                return pos
        return None

    def _ib_position_to_phoenix(self, ib_pos: IBPosition) -> Position:
        """Convert IB Position to Phoenix Position."""
        symbol = f"{ib_pos.contract.symbol}{ib_pos.contract.currency}"

        return Position(
            symbol=symbol,
            quantity=float(ib_pos.position),
            avg_cost=float(ib_pos.avgCost),
            market_price=float(ib_pos.avgCost),  # Would need market data for real price
            account=ib_pos.account,
        )

    # =========================================================================
    # ACCOUNT
    # =========================================================================

    def get_account(self) -> AccountState:
        """Get account state."""
        if not self.connected:
            return AccountState(account_id="")

        try:
            summary = self._ib.accountSummary()

            # Parse summary into AccountState
            values: dict[str, float] = {}
            for item in summary:
                if item.tag in [
                    "NetLiquidation",
                    "TotalCashValue",
                    "AvailableFunds",
                    "BuyingPower",
                    "MaintMarginReq",
                    "InitMarginReq",
                    "UnrealizedPnL",
                ]:
                    values[item.tag] = float(item.value)

            return AccountState(
                account_id=self._state.account_id,
                net_liquidation=values.get("NetLiquidation", 0.0),
                total_cash=values.get("TotalCashValue", 0.0),
                available_funds=values.get("AvailableFunds", 0.0),
                buying_power=values.get("BuyingPower", 0.0),
                maintenance_margin=values.get("MaintMarginReq", 0.0),
                initial_margin=values.get("InitMarginReq", 0.0),
                unrealized_pnl=values.get("UnrealizedPnL", 0.0),
            )

        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            return AccountState(account_id=self._state.account_id)

    # =========================================================================
    # HEALTH
    # =========================================================================

    def health_check(self) -> dict[str, Any]:
        """Check client health."""
        return {
            "connected": self.connected,
            "account_id": self._state.account_id,
            "port": self._state.port,
            "gateway_version": self._state.gateway_version,
            "mode": self._config.mode.value,
            "timestamp": datetime.now(UTC).isoformat(),
        }
