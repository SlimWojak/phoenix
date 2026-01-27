"""
IBKR Mock Client — Banteg-style chaos simulation
================================================

S32: EXECUTION_PATH

Full mock IBKR client for testing. Supports chaos modes:
- INSTANT: Fast tests, 100% fill
- REALISTIC: BUNNY tests, real-world probabilities
- ADVERSARIAL: Stress tests, worst-case scenarios

INVARIANT: INV-IBKR-MOCK-1 — All tests use this mock
"""

from __future__ import annotations

import random
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .account import AccountState
from .orders import Order, OrderResult, OrderStatus
from .positions import Position, PositionSnapshot


class ChaosMode(Enum):
    """
    Mock client chaos modes.

    INSTANT: Unit tests - fast, deterministic
    REALISTIC: BUNNY tests - real-world probabilities
    ADVERSARIAL: Stress tests - worst-case scenarios
    """

    INSTANT = "INSTANT"
    REALISTIC = "REALISTIC"
    ADVERSARIAL = "ADVERSARIAL"


@dataclass
class ChaosConfig:
    """Configuration for chaos injection."""

    fill_probability: float = 1.0
    partial_fill_prob: float = 0.0
    reject_prob: float = 0.0
    delay_prob: float = 0.0
    delay_range_sec: tuple[float, float] = (0.0, 0.0)
    partial_fill_range: tuple[float, float] = (0.3, 0.9)

    @classmethod
    def for_mode(cls, mode: ChaosMode) -> ChaosConfig:
        """Get config for chaos mode."""
        if mode == ChaosMode.INSTANT:
            return cls(
                fill_probability=1.0,
                partial_fill_prob=0.0,
                reject_prob=0.0,
                delay_prob=0.0,
                delay_range_sec=(0.0, 0.0),
            )
        elif mode == ChaosMode.REALISTIC:
            return cls(
                fill_probability=0.90,
                partial_fill_prob=0.05,
                reject_prob=0.03,
                delay_prob=0.02,
                delay_range_sec=(10.0, 30.0),
            )
        elif mode == ChaosMode.ADVERSARIAL:
            return cls(
                fill_probability=0.70,
                partial_fill_prob=0.15,
                reject_prob=0.10,
                delay_prob=0.05,
                delay_range_sec=(30.0, 60.0),
            )
        return cls()


class MockIBKRClient:
    """
    Mock IBKR client with chaos injection.

    Simulates IBKR API behavior for testing.

    INVARIANT: INV-IBKR-MOCK-1
    No test hits real IBKR — all go through this mock.
    """

    def __init__(
        self,
        mode: ChaosMode = ChaosMode.INSTANT,
        seed: int | None = None,
        account_id: str = "DU1234567",
    ) -> None:
        """
        Initialize mock client.

        Args:
            mode: Chaos mode for simulation
            seed: Random seed for reproducibility (None = random)
            account_id: Mock account ID
        """
        self._mode = mode
        self._config = ChaosConfig.for_mode(mode)
        self._account_id = account_id
        self._connected = False

        # Seed for reproducibility
        if seed is not None:
            random.seed(seed)

        # Mock state
        self._positions: dict[str, Position] = {}
        self._orders: dict[str, Order] = {}
        self._fills: list[dict[str, Any]] = []

        # Account state
        self._balance = 100000.0
        self._available = 100000.0

    @property
    def mode(self) -> ChaosMode:
        """Current chaos mode."""
        return self._mode

    @property
    def connected(self) -> bool:
        """Connection status."""
        return self._connected

    def set_mode(self, mode: ChaosMode) -> None:
        """Change chaos mode."""
        self._mode = mode
        self._config = ChaosConfig.for_mode(mode)

    def set_seed(self, seed: int) -> None:
        """Set random seed for reproducibility."""
        random.seed(seed)

    # =========================================================================
    # CONNECTION
    # =========================================================================

    def connect(self) -> bool:
        """
        Connect to mock IBKR.

        Returns:
            True on success
        """
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Disconnect from mock IBKR."""
        self._connected = False

    # =========================================================================
    # ORDERS
    # =========================================================================

    def submit_order(self, order: Order) -> OrderResult:
        """
        Submit order with chaos injection.

        Args:
            order: Order to submit

        Returns:
            OrderResult with fill details or error
        """
        if not self._connected:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.REJECTED,
                requested_quantity=order.quantity,
                message="Not connected",
                errors=["Client not connected to IBKR"],
            )

        # Validate order
        errors = order.validate()
        if errors:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.REJECTED,
                requested_quantity=order.quantity,
                message="Validation failed",
                errors=errors,
            )

        # Store order
        self._orders[order.order_id] = order

        # Apply chaos
        return self._apply_chaos(order)

    def _apply_chaos(self, order: Order) -> OrderResult:
        """Apply chaos injection to order."""
        # Check for delay
        if random.random() < self._config.delay_prob:
            delay = random.uniform(*self._config.delay_range_sec)
            time.sleep(min(delay, 0.1))  # Cap actual delay in tests

        # Check for rejection
        if random.random() < self._config.reject_prob:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.REJECTED,
                requested_quantity=order.quantity,
                message="Broker rejection (simulated)",
                errors=["Insufficient margin (simulated)"],
            )

        # Check for partial fill
        fill_ratio = 1.0
        status = OrderStatus.FILLED

        if random.random() < self._config.partial_fill_prob:
            fill_ratio = random.uniform(*self._config.partial_fill_range)
            status = OrderStatus.PARTIAL

        # Check for normal fill
        elif random.random() > self._config.fill_probability:
            return OrderResult(
                success=False,
                order_id=order.order_id,
                status=OrderStatus.SUBMITTED,
                requested_quantity=order.quantity,
                message="Order submitted, awaiting fill",
            )

        # Generate fill
        broker_order_id = f"IBKR-{uuid.uuid4().hex[:8]}"
        fill_price = self._generate_fill_price(order.symbol)
        filled_qty = order.quantity * fill_ratio

        # Update position
        self._update_position(order, filled_qty, fill_price)

        # Record fill
        self._fills.append({
            "order_id": order.order_id,
            "broker_order_id": broker_order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "filled_quantity": filled_qty,
            "fill_price": fill_price,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        return OrderResult(
            success=True,
            order_id=order.order_id,
            status=status,
            broker_order_id=broker_order_id,
            fill_price=fill_price,
            filled_quantity=filled_qty,
            requested_quantity=order.quantity,
            message=f"{'Partial' if status == OrderStatus.PARTIAL else 'Filled'} at {fill_price:.5f}",
        )

    def _generate_fill_price(self, symbol: str) -> float:
        """Generate mock fill price for symbol."""
        # Base prices for common pairs
        base_prices = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2500,
            "USDJPY": 150.00,
            "AUDUSD": 0.6500,
            "USDCAD": 1.3500,
            "NZDUSD": 0.5800,
        }
        base = base_prices.get(symbol, 1.0)

        # Add small random slippage
        slippage = random.uniform(-0.0005, 0.0005)
        return base + slippage

    def _update_position(self, order: Order, filled_qty: float, fill_price: float) -> None:
        """Update mock position state."""
        symbol = order.symbol
        side_mult = 1 if order.side.value == "BUY" else -1

        if symbol in self._positions:
            pos = self._positions[symbol]
            new_qty = pos.quantity + (filled_qty * side_mult)
            # Simple avg cost update
            if new_qty != 0:
                pos.quantity = new_qty
                pos.avg_cost = fill_price
            else:
                del self._positions[symbol]
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                quantity=filled_qty * side_mult,
                avg_cost=fill_price,
                market_price=fill_price,
                account=self._account_id,
            )

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id in self._orders:
            del self._orders[order_id]
            return True
        return False

    # =========================================================================
    # POSITIONS
    # =========================================================================

    def get_positions(self) -> PositionSnapshot:
        """Get all positions."""
        return PositionSnapshot(
            positions=list(self._positions.values()),
            account=self._account_id,
        )

    def get_position(self, symbol: str) -> Position | None:
        """Get position for symbol."""
        return self._positions.get(symbol)

    # =========================================================================
    # ACCOUNT
    # =========================================================================

    def get_account(self) -> AccountState:
        """Get account state."""
        # Calculate margin based on positions
        margin = sum(
            abs(p.quantity) * p.avg_cost * 0.02
            for p in self._positions.values()
        )

        return AccountState(
            account_id=self._account_id,
            net_liquidation=self._balance,
            total_cash=self._balance,
            available_funds=self._available - margin,
            buying_power=(self._available - margin) * 50,  # 50:1 leverage
            maintenance_margin=margin,
            initial_margin=margin * 1.1,
            unrealized_pnl=sum(p.unrealized_pnl for p in self._positions.values()),
        )

    # =========================================================================
    # TEST HELPERS
    # =========================================================================

    def set_position(self, symbol: str, quantity: float, avg_cost: float) -> None:
        """Set position directly (for testing)."""
        self._positions[symbol] = Position(
            symbol=symbol,
            quantity=quantity,
            avg_cost=avg_cost,
            market_price=avg_cost,
            account=self._account_id,
        )

    def set_balance(self, balance: float) -> None:
        """Set account balance (for testing)."""
        self._balance = balance
        self._available = balance

    def clear_positions(self) -> None:
        """Clear all positions (for testing)."""
        self._positions.clear()

    def get_fills(self) -> list[dict[str, Any]]:
        """Get fill history."""
        return self._fills.copy()

    def inject_drift(self, symbol: str, quantity_drift: float) -> None:
        """
        Inject drift for reconciliation testing.

        Args:
            symbol: Position symbol
            quantity_drift: Amount to drift quantity by
        """
        if symbol in self._positions:
            self._positions[symbol].quantity += quantity_drift
