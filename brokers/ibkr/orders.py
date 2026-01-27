"""
IBKR Orders — Order data structures and types
=============================================

S32: EXECUTION_PATH

Defines order structures for IBKR submission.
S32 scope: MARKET orders only (LIMIT/BRACKET deferred to S33).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class OrderType(Enum):
    """Order type enumeration."""

    MARKET = "MKT"
    # S33: LIMIT = "LMT"
    # S33: BRACKET = "BRACKET"


class OrderSide(Enum):
    """Order side enumeration."""

    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status enumeration."""

    PENDING = "PENDING"        # Order created, not yet submitted
    SUBMITTED = "SUBMITTED"    # Sent to broker
    FILLED = "FILLED"          # Fully executed
    PARTIAL = "PARTIAL"        # Partially filled
    CANCELLED = "CANCELLED"    # Cancelled before fill
    REJECTED = "REJECTED"      # Broker rejected


@dataclass
class Order:
    """
    Order representation for IBKR submission.

    Immutable once created — changes create new Order.
    """

    order_id: str = field(default_factory=lambda: f"ORD-{uuid.uuid4().hex[:8]}")
    symbol: str = ""
    order_type: OrderType = OrderType.MARKET
    side: OrderSide = OrderSide.BUY
    quantity: float = 0.0
    limit_price: float | None = None  # S33: For limit orders
    stop_price: float | None = None
    target_price: float | None = None
    token_id: str | None = None  # T2 approval token

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "order_type": self.order_type.value,
            "side": self.side.value,
            "quantity": self.quantity,
            "limit_price": self.limit_price,
            "stop_price": self.stop_price,
            "target_price": self.target_price,
            "token_id": self.token_id,
            "created_at": self.created_at.isoformat(),
        }

    def validate(self) -> list[str]:
        """Validate order fields."""
        errors = []

        if not self.symbol:
            errors.append("Symbol is required")

        if self.quantity <= 0:
            errors.append("Quantity must be positive")

        if self.order_type == OrderType.MARKET and self.limit_price is not None:
            errors.append("Market orders cannot have limit price")

        if self.token_id is None:
            errors.append("T2 token is required (INV-T2-GATE-1)")

        return errors


@dataclass
class OrderResult:
    """Result of order submission."""

    success: bool
    order_id: str
    status: OrderStatus
    broker_order_id: str | None = None
    fill_price: float | None = None
    filled_quantity: float = 0.0
    requested_quantity: float = 0.0
    message: str = ""
    errors: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def partial_fill_ratio(self) -> float:
        """Calculate partial fill ratio."""
        if self.requested_quantity <= 0:
            return 0.0
        return self.filled_quantity / self.requested_quantity

    @property
    def is_partial(self) -> bool:
        """Check if this is a partial fill."""
        return 0 < self.partial_fill_ratio < 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "order_id": self.order_id,
            "status": self.status.value,
            "broker_order_id": self.broker_order_id,
            "fill_price": self.fill_price,
            "filled_quantity": self.filled_quantity,
            "requested_quantity": self.requested_quantity,
            "partial_fill_ratio": self.partial_fill_ratio,
            "message": self.message,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
        }


def create_market_order(
    symbol: str,
    side: OrderSide,
    quantity: float,
    token_id: str,
    stop_price: float | None = None,
    target_price: float | None = None,
) -> Order:
    """
    Factory for creating market orders.

    Args:
        symbol: Trading symbol (e.g., "EURUSD")
        side: BUY or SELL
        quantity: Position size
        token_id: T2 approval token (required)
        stop_price: Stop loss price
        target_price: Take profit price

    Returns:
        Order ready for submission
    """
    return Order(
        symbol=symbol,
        order_type=OrderType.MARKET,
        side=side,
        quantity=quantity,
        token_id=token_id,
        stop_price=stop_price,
        target_price=target_price,
    )
