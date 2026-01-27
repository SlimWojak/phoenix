"""
Paper Position — Paper Trading Position Management
===================================================

Tracks paper positions without touching real capital.

INVARIANTS:
- INV-SHADOW-ISO-1: NEVER affects live capital
- INV-POSITION-TRACK-1: All position changes logged
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# =============================================================================
# ENUMS
# =============================================================================


class PositionState(str, Enum):
    """Position lifecycle states."""

    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class PositionSide(str, Enum):
    """Position side (direction)."""

    LONG = "LONG"
    SHORT = "SHORT"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class PositionResult:
    """Result of position operation."""

    position_id: str
    state: PositionState
    pnl: float = 0.0
    pnl_pips: float = 0.0
    errors: list[str] = field(default_factory=list)


@dataclass
class PaperPosition:
    """
    Paper trading position.

    INVARIANT: INV-SHADOW-ISO-1 — Exists ONLY in paper domain
    """

    position_id: str
    signal_id: str  # CSE signal that triggered this
    pair: str
    side: PositionSide
    state: PositionState

    # Entry
    entry_price: float
    entry_time: datetime
    size: float  # Units (not lots)

    # Risk parameters
    stop_price: float
    target_price: float
    risk_percent: float

    # Exit (populated on close)
    exit_price: float | None = None
    exit_time: datetime | None = None
    exit_reason: str | None = None

    # P&L
    realized_pnl: float = 0.0
    realized_pnl_pips: float = 0.0

    # Tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "position_id": self.position_id,
            "signal_id": self.signal_id,
            "pair": self.pair,
            "side": self.side.value,
            "state": self.state.value,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat(),
            "size": self.size,
            "stop_price": self.stop_price,
            "target_price": self.target_price,
            "risk_percent": self.risk_percent,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_reason": self.exit_reason,
            "realized_pnl": self.realized_pnl,
            "realized_pnl_pips": self.realized_pnl_pips,
            "created_at": self.created_at.isoformat(),
        }

    def open_position(self, current_price: float) -> PositionResult:
        """
        Open the position.

        Args:
            current_price: Current market price for slippage calc

        Returns:
            PositionResult
        """
        if self.state != PositionState.PENDING:
            return PositionResult(
                position_id=self.position_id,
                state=self.state,
                errors=[f"Cannot open from state {self.state}"],
            )

        # Apply simulated slippage (1 pip)
        slippage = 0.0001 if self.pair.endswith("USD") else 0.01
        if self.side == PositionSide.LONG:
            self.entry_price = current_price + slippage
        else:
            self.entry_price = current_price - slippage

        self.entry_time = datetime.now(UTC)
        self.state = PositionState.OPEN

        self._log_event("OPENED", {"price": self.entry_price})

        return PositionResult(
            position_id=self.position_id,
            state=self.state,
        )

    def close_position(
        self,
        exit_price: float,
        reason: str = "manual",
    ) -> PositionResult:
        """
        Close the position.

        Args:
            exit_price: Exit price
            reason: Close reason (stop, target, manual)

        Returns:
            PositionResult with P&L
        """
        if self.state != PositionState.OPEN:
            return PositionResult(
                position_id=self.position_id,
                state=self.state,
                errors=[f"Cannot close from state {self.state}"],
            )

        self.exit_price = exit_price
        self.exit_time = datetime.now(UTC)
        self.exit_reason = reason
        self.state = PositionState.CLOSED

        # Calculate P&L
        self._calculate_pnl()

        self._log_event("CLOSED", {
            "price": exit_price,
            "reason": reason,
            "pnl": self.realized_pnl,
            "pnl_pips": self.realized_pnl_pips,
        })

        return PositionResult(
            position_id=self.position_id,
            state=self.state,
            pnl=self.realized_pnl,
            pnl_pips=self.realized_pnl_pips,
        )

    def check_stops(self, current_price: float) -> PositionResult | None:
        """
        Check if stop or target hit.

        Args:
            current_price: Current market price

        Returns:
            PositionResult if position closed, None otherwise
        """
        if self.state != PositionState.OPEN:
            return None

        # Check stop loss
        if self.side == PositionSide.LONG:
            if current_price <= self.stop_price:
                return self.close_position(self.stop_price, "stop_loss")
            if current_price >= self.target_price:
                return self.close_position(self.target_price, "take_profit")
        else:  # SHORT
            if current_price >= self.stop_price:
                return self.close_position(self.stop_price, "stop_loss")
            if current_price <= self.target_price:
                return self.close_position(self.target_price, "take_profit")

        return None

    def _calculate_pnl(self) -> None:
        """Calculate realized P&L."""
        if self.exit_price is None:
            return

        # Calculate price movement
        if self.side == PositionSide.LONG:
            price_diff = self.exit_price - self.entry_price
        else:
            price_diff = self.entry_price - self.exit_price

        # Convert to pips (assuming standard pairs)
        pip_value = 0.0001 if self.pair.endswith("USD") else 0.01
        self.realized_pnl_pips = price_diff / pip_value

        # Calculate monetary P&L (simplified)
        self.realized_pnl = price_diff * self.size

    def _log_event(self, event: str, data: dict[str, Any]) -> None:
        """Log position event for audit trail."""
        self.history.append({
            "event": event,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": data,
        })


# =============================================================================
# FACTORY
# =============================================================================


def create_paper_position(
    signal_id: str,
    pair: str,
    side: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    risk_percent: float,
    account_balance: float = 10000.0,
) -> PaperPosition:
    """
    Create paper position from CSE signal.

    Args:
        signal_id: CSE signal ID
        pair: Currency pair
        side: LONG or SHORT
        entry_price: Entry price
        stop_price: Stop loss price
        target_price: Take profit price
        risk_percent: Risk as percentage of account
        account_balance: Paper account balance

    Returns:
        PaperPosition (PENDING state)
    """
    # Calculate position size from risk
    risk_amount = account_balance * (risk_percent / 100)
    pip_value = 0.0001 if pair.endswith("USD") else 0.01
    stop_distance = abs(entry_price - stop_price)
    stop_pips = stop_distance / pip_value

    # Size = risk_amount / (stop_pips * pip_value_per_unit)
    # Simplified: assume $10 per pip per standard lot
    if stop_pips > 0:
        size = risk_amount / (stop_pips * 10)
    else:
        size = 0.1  # Minimum size

    return PaperPosition(
        position_id=f"PAPER-{uuid.uuid4().hex[:8]}",
        signal_id=signal_id,
        pair=pair,
        side=PositionSide(side),
        state=PositionState.PENDING,
        entry_price=entry_price,
        entry_time=datetime.now(UTC),
        size=size,
        stop_price=stop_price,
        target_price=target_price,
        risk_percent=risk_percent,
    )
