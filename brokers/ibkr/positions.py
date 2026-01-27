"""
IBKR Positions — Position data structures
=========================================

S32: EXECUTION_PATH

Defines position structures for IBKR queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class Position:
    """
    Position representation from IBKR.

    Represents current broker state (not Phoenix state).
    """

    symbol: str
    quantity: float
    avg_cost: float
    market_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    account: str = ""
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def side(self) -> str:
        """Position side based on quantity."""
        if self.quantity > 0:
            return "LONG"
        elif self.quantity < 0:
            return "SHORT"
        return "FLAT"

    @property
    def absolute_quantity(self) -> float:
        """Absolute position size."""
        return abs(self.quantity)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "absolute_quantity": self.absolute_quantity,
            "side": self.side,
            "avg_cost": self.avg_cost,
            "market_price": self.market_price,
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "account": self.account,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class PositionQuery:
    """Query parameters for position lookup."""

    symbol: str | None = None  # None = all positions
    account: str | None = None

    def matches(self, position: Position) -> bool:
        """Check if position matches query."""
        if self.symbol and position.symbol != self.symbol:
            return False
        if self.account and position.account != self.account:
            return False
        return True


@dataclass
class PositionSnapshot:
    """Snapshot of all positions at a point in time."""

    positions: list[Position] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    account: str = ""

    @property
    def total_unrealized_pnl(self) -> float:
        """Total unrealized P&L across all positions."""
        return sum(p.unrealized_pnl for p in self.positions)

    @property
    def position_count(self) -> int:
        """Number of open positions."""
        return len([p for p in self.positions if p.quantity != 0])

    def get_position(self, symbol: str) -> Position | None:
        """Get position by symbol."""
        for p in self.positions:
            if p.symbol == symbol:
                return p
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "positions": [p.to_dict() for p in self.positions],
            "timestamp": self.timestamp.isoformat(),
            "account": self.account,
            "total_unrealized_pnl": self.total_unrealized_pnl,
            "position_count": self.position_count,
        }
