"""
IBKR Account — Account state data structures
============================================

S32: EXECUTION_PATH

Defines account state structures for IBKR queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class AccountState:
    """
    Account state from IBKR.

    Represents current broker account state.
    """

    account_id: str
    net_liquidation: float = 0.0
    total_cash: float = 0.0
    available_funds: float = 0.0
    buying_power: float = 0.0
    excess_liquidity: float = 0.0
    maintenance_margin: float = 0.0
    initial_margin: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    currency: str = "USD"
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def margin_utilization(self) -> float:
        """Margin utilization percentage."""
        if self.net_liquidation <= 0:
            return 0.0
        return self.maintenance_margin / self.net_liquidation

    @property
    def can_trade(self) -> bool:
        """Check if account can take new positions."""
        return self.available_funds > 0 and self.buying_power > 0

    def has_margin_for(self, required_margin: float) -> bool:
        """Check if account has margin for a trade."""
        return self.available_funds >= required_margin

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "account_id": self.account_id,
            "net_liquidation": self.net_liquidation,
            "total_cash": self.total_cash,
            "available_funds": self.available_funds,
            "buying_power": self.buying_power,
            "excess_liquidity": self.excess_liquidity,
            "maintenance_margin": self.maintenance_margin,
            "initial_margin": self.initial_margin,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "margin_utilization": self.margin_utilization,
            "can_trade": self.can_trade,
            "currency": self.currency,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class AccountSummary:
    """Summary of account for display."""

    account_id: str
    balance: float
    available: float
    pnl_today: float
    positions: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def from_account_state(cls, state: AccountState, position_count: int) -> AccountSummary:
        """Create summary from account state."""
        return cls(
            account_id=state.account_id,
            balance=state.net_liquidation,
            available=state.available_funds,
            pnl_today=state.unrealized_pnl + state.realized_pnl,
            positions=position_count,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "account_id": self.account_id,
            "balance": self.balance,
            "available": self.available,
            "pnl_today": self.pnl_today,
            "positions": self.positions,
            "timestamp": self.timestamp.isoformat(),
        }
