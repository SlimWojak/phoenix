"""
Position Lifecycle — Position management
========================================

S32: EXECUTION_PATH

Position class and lifecycle state machine implementation.

INVARIANTS:
- INV-POSITION-SM-1: Only valid transitions allowed
- INV-POSITION-AUDIT-1: POSITION bead at every transition
- INV-POSITION-SUBMITTED-TTL-1: SUBMITTED > 60s → STALLED + alert

WATCHPOINTS:
- WP_C1: STALLED with alert + bead + reason
- WP_C3: partial_fill_ratio tracking
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .states import (
    PositionState,
    TransitionError,
    get_transition,
    is_valid_transition,
)

# Constants
SUBMITTED_TIMEOUT_SEC = 60  # WP_C1: Timeout before STALLED
TOKEN_EXPIRY_SEC = 300  # 5 minutes


@dataclass
class Position:
    """
    Position in the lifecycle.

    Tracks a position from PROPOSED through to CLOSED.
    """

    position_id: str = field(default_factory=lambda: f"POS-{uuid.uuid4().hex[:8]}")
    signal_id: str = ""
    intent_id: str = ""

    # State
    state: PositionState = PositionState.PROPOSED
    previous_state: PositionState | None = None
    state_changed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Trade details
    pair: str = ""
    side: str = ""  # LONG or SHORT

    # Prices
    entry_price: float | None = None
    stop_price: float = 0.0
    target_price: float = 0.0
    exit_price: float | None = None

    # Quantities (WP_C3: partial fill tracking)
    requested_quantity: float = 0.0
    filled_quantity: float = 0.0

    # P&L
    realized_pnl: float | None = None
    exit_reason: str | None = None

    # Broker details
    broker_order_id: str | None = None
    token_id: str | None = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    closed_at: datetime | None = None

    # Stall tracking (WP_C1)
    stall_reason: str | None = None

    @property
    def partial_fill_ratio(self) -> float:
        """WP_C3: Partial fill ratio (0.0 - 1.0)."""
        if self.requested_quantity <= 0:
            return 0.0
        return min(1.0, self.filled_quantity / self.requested_quantity)

    @property
    def is_partial_fill(self) -> bool:
        """Check if position has partial fill."""
        ratio = self.partial_fill_ratio
        return 0 < ratio < 1.0

    @property
    def is_terminal(self) -> bool:
        """Check if position is in terminal state."""
        return self.state.is_terminal

    @property
    def is_active(self) -> bool:
        """Check if position is actively in market."""
        return self.state.is_active

    @property
    def time_in_state_sec(self) -> float:
        """Seconds in current state."""
        return (datetime.now(UTC) - self.state_changed_at).total_seconds()

    @property
    def is_submitted_stale(self) -> bool:
        """WP_C1: Check if SUBMITTED state has timed out."""
        if self.state != PositionState.SUBMITTED:
            return False
        return self.time_in_state_sec > SUBMITTED_TIMEOUT_SEC

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "position_id": self.position_id,
            "signal_id": self.signal_id,
            "intent_id": self.intent_id,
            "state": self.state.value,
            "previous_state": self.previous_state.value if self.previous_state else None,
            "pair": self.pair,
            "side": self.side,
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
            "target_price": self.target_price,
            "exit_price": self.exit_price,
            "requested_quantity": self.requested_quantity,
            "filled_quantity": self.filled_quantity,
            "partial_fill_ratio": self.partial_fill_ratio,
            "realized_pnl": self.realized_pnl,
            "exit_reason": self.exit_reason,
            "broker_order_id": self.broker_order_id,
            "token_id": self.token_id,
            "stall_reason": self.stall_reason,
            "created_at": self.created_at.isoformat(),
            "state_changed_at": self.state_changed_at.isoformat(),
        }


class PositionLifecycle:
    """
    Position lifecycle state machine.

    Manages state transitions with validation and bead emission.

    INVARIANTS:
    - INV-POSITION-SM-1: Only valid transitions
    - INV-POSITION-AUDIT-1: Bead at every transition
    - INV-POSITION-SUBMITTED-TTL-1: 60s timeout → STALLED
    """

    def __init__(
        self,
        emit_bead: Callable[[dict[str, Any]], None] | None = None,
        emit_alert: Callable[[str, str], None] | None = None,
    ) -> None:
        """
        Initialize lifecycle manager.

        Args:
            emit_bead: Callback for POSITION bead emission
            emit_alert: Callback for alerts (message, level)
        """
        self._emit_bead = emit_bead
        self._emit_alert = emit_alert

    def transition(
        self,
        position: Position,
        to_state: PositionState,
        reason: str = "",
        **kwargs: Any,
    ) -> Position:
        """
        Transition position to new state.

        INVARIANT: INV-POSITION-SM-1
        Only valid transitions are allowed.

        Args:
            position: Position to transition
            to_state: Target state
            reason: Reason for transition
            **kwargs: Additional data for transition

        Returns:
            Updated position

        Raises:
            TransitionError: If transition is invalid
        """
        from_state = position.state

        # Validate transition (INV-POSITION-SM-1)
        if not is_valid_transition(from_state, to_state):
            raise TransitionError(from_state, to_state, reason)

        # Get transition definition
        transition = get_transition(from_state, to_state)

        # Update position state
        position.previous_state = from_state
        position.state = to_state
        position.state_changed_at = datetime.now(UTC)

        # Handle state-specific updates
        self._handle_state_entry(position, to_state, reason, **kwargs)

        # Emit alert if required
        if transition and transition.emits_alert:
            self._send_alert(position, to_state, reason)

        # Emit POSITION bead (INV-POSITION-AUDIT-1)
        self._emit_position_bead(position, reason)

        return position

    def _handle_state_entry(
        self,
        position: Position,
        to_state: PositionState,
        reason: str,
        **kwargs: Any,
    ) -> None:
        """Handle state-specific entry logic."""
        if to_state == PositionState.APPROVED:
            position.token_id = kwargs.get("token_id")

        elif to_state == PositionState.SUBMITTED:
            position.submitted_at = datetime.now(UTC)
            position.broker_order_id = kwargs.get("broker_order_id")

        elif to_state == PositionState.STALLED:
            # WP_C1: Record stall reason
            position.stall_reason = reason or "60s timeout without broker ACK"

        elif to_state == PositionState.FILLED:
            position.filled_at = datetime.now(UTC)
            position.entry_price = kwargs.get("fill_price", position.entry_price)
            position.filled_quantity = kwargs.get("filled_quantity", position.requested_quantity)
            position.broker_order_id = kwargs.get("broker_order_id", position.broker_order_id)

        elif to_state == PositionState.CLOSED:
            position.closed_at = datetime.now(UTC)
            position.exit_price = kwargs.get("exit_price")
            position.realized_pnl = kwargs.get("realized_pnl")
            position.exit_reason = kwargs.get("exit_reason", reason)

        elif to_state == PositionState.REJECTED:
            position.stall_reason = reason or "Broker rejected order"

    def _send_alert(self, position: Position, state: PositionState, reason: str) -> None:
        """Send alert for significant state changes."""
        if self._emit_alert is None:
            return

        level = "WARNING" if state.requires_attention else "INFO"
        message = f"Position {position.position_id}: {state.value}"
        if reason:
            message += f" - {reason}"

        try:
            self._emit_alert(message, level)
        except Exception:  # noqa: S110
            pass  # Non-blocking

    def _emit_position_bead(self, position: Position, reason: str) -> None:
        """
        Emit POSITION bead.

        INVARIANT: INV-POSITION-AUDIT-1
        Every state transition emits a bead.
        """
        if self._emit_bead is None:
            return

        bead_data = {
            "bead_type": "POSITION",
            "position_id": position.position_id,
            "signal_id": position.signal_id,
            "state": position.state.value,
            "previous_state": position.previous_state.value if position.previous_state else "INIT",
            "pair": position.pair,
            "side": position.side,
            "entry_price": position.entry_price,
            "stop_price": position.stop_price,
            "target_price": position.target_price,
            "requested_quantity": position.requested_quantity,
            "filled_quantity": position.filled_quantity,
            "partial_fill_ratio": position.partial_fill_ratio,
            "broker_order_id": position.broker_order_id,
            "token_id": position.token_id,
            "stall_reason": position.stall_reason,
            "reason": reason,
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }

        try:
            self._emit_bead(bead_data)
        except Exception:  # noqa: S110
            pass  # Non-blocking

    def check_stale_submitted(self, position: Position) -> bool:
        """
        Check if SUBMITTED position should transition to STALLED.

        INVARIANT: INV-POSITION-SUBMITTED-TTL-1
        SUBMITTED > 60s without ACK → STALLED + alert

        WP_C1: NO automatic retry. Human decides.

        Args:
            position: Position to check

        Returns:
            True if position was transitioned to STALLED
        """
        if not position.is_submitted_stale:
            return False

        self.transition(
            position,
            PositionState.STALLED,
            reason=f"Timeout after {SUBMITTED_TIMEOUT_SEC}s without broker ACK",
        )
        return True


def create_position(
    signal_id: str,
    pair: str,
    side: str,
    quantity: float,
    stop_price: float,
    target_price: float,
    intent_id: str = "",
) -> Position:
    """
    Factory for creating new positions.

    Args:
        signal_id: CSE signal that triggered this position
        pair: Currency pair
        side: LONG or SHORT
        quantity: Requested quantity
        stop_price: Stop loss price
        target_price: Take profit price
        intent_id: Intent ID from T2 workflow

    Returns:
        New Position in PROPOSED state
    """
    return Position(
        signal_id=signal_id,
        intent_id=intent_id,
        pair=pair,
        side=side,
        requested_quantity=quantity,
        stop_price=stop_price,
        target_price=target_price,
    )
