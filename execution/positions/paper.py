"""
Paper Position Model — Simplified position lifecycle for paper trading.

SPRINT: S28.C (relocated to positions/ package in S52)
STATUS: PAPER_ONLY
CAPITAL: PAPER_ONLY

5-state position lifecycle for paper broker / replay testing:
  PENDING → OPEN → PARTIAL → CLOSED
  Any state → HALTED (system halt)

P&L_v0 (SIMPLIFIED):
- P&L = (exit_price - entry_price) * size * direction_multiplier
- NO fees, NO slippage

INVARIANTS:
- INV-CONTRACT-1: deterministic state machine
- INV-EXEC-LIFECYCLE-1: valid transitions only

NOTE: This is the PAPER BROKER position model. For production lifecycle
with T2 gates, use execution.positions (9-state FSM).
"""

import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# =============================================================================
# BEAD EMISSION
# =============================================================================

_violation_callback: Callable[[dict[str, Any]], None] | None = None


def set_violation_callback(callback: Callable[[dict[str, Any]], None]) -> None:
    """Set callback for violation bead emission."""
    global _violation_callback
    _violation_callback = callback


def _emit_violation_bead(
    violation_type: str, from_state: str, to_state: str, position_id: str | None = None
) -> dict[str, Any]:
    """Emit VIOLATION bead for InvalidTransitionError."""
    now = datetime.now(UTC)

    bead = {
        "bead_id": f"BEAD-TRANS-{now.strftime('%Y%m%d%H%M%S')}",
        "bead_type": "VIOLATION",
        "timestamp": now.isoformat(),
        "source_module": "execution.positions.paper",
        "violation_type": violation_type,
        "from_state": from_state,
        "to_state": to_state,
        "position_id": position_id,
        "invariant": "INV-EXEC-LIFECYCLE-1",
    }

    logger.warning(f"VIOLATION BEAD: {violation_type} ({from_state} → {to_state})")

    if _violation_callback:
        try:
            _violation_callback(bead)
        except Exception as e:
            logger.error(f"Violation callback error: {e}")

    return bead


# =============================================================================
# EXCEPTIONS
# =============================================================================


class InvalidTransitionError(Exception):
    """Raised when attempting invalid state transition."""

    def __init__(
        self,
        from_state: "PaperPositionState",
        to_state: "PaperPositionState",
        position_id: str | None = None,
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.position_id = position_id

        _emit_violation_bead(
            violation_type="invalid_state_transition",
            from_state=from_state.value,
            to_state=to_state.value,
            position_id=position_id,
        )

        super().__init__(
            f"INV-EXEC-LIFECYCLE-1 violated: "
            f"Invalid transition {from_state.value} → {to_state.value}"
        )


class PositionMutationError(Exception):
    """Raised when attempting to mutate closed/halted position."""

    pass


# =============================================================================
# PAPER POSITION STATE ENUM
# =============================================================================


class PaperPositionState(Enum):
    """
    Paper broker position lifecycle states (5-state).

    For production lifecycle with T2 gates, see execution.positions.states.PositionState.
    """

    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    CLOSED = "CLOSED"
    HALTED = "HALTED"


# =============================================================================
# STATE MACHINE TRANSITIONS
# =============================================================================

VALID_TRANSITIONS: dict[PaperPositionState, set[PaperPositionState]] = {
    PaperPositionState.PENDING: {
        PaperPositionState.OPEN,
        PaperPositionState.PARTIAL,
        PaperPositionState.CLOSED,
        PaperPositionState.HALTED,
    },
    PaperPositionState.OPEN: {
        PaperPositionState.PARTIAL,
        PaperPositionState.CLOSED,
        PaperPositionState.HALTED,
    },
    PaperPositionState.PARTIAL: {
        PaperPositionState.OPEN,
        PaperPositionState.CLOSED,
        PaperPositionState.HALTED,
    },
    PaperPositionState.CLOSED: set(),
    PaperPositionState.HALTED: set(),
}


def validate_transition(from_state: PaperPositionState, to_state: PaperPositionState) -> bool:
    """
    Validate state transition.

    INV-EXEC-LIFECYCLE-1: only valid transitions allowed.
    """
    valid_targets = VALID_TRANSITIONS.get(from_state, set())
    return to_state in valid_targets


# =============================================================================
# PAPER POSITION DATA CLASS
# =============================================================================


@dataclass
class PaperPosition:
    """
    Paper broker position with lifecycle state machine.

    P&L_v0 (SIMPLIFIED): No fees, no slippage.
    PAPER ONLY for testing execution flow.
    """

    position_id: str
    intent_id: str
    state: PaperPositionState
    symbol: str
    direction: str  # "LONG" or "SHORT"

    state_history: list[dict[str, Any]] = field(default_factory=list)

    entry_price: float | None = None
    exit_price: float | None = None
    size: float = 0.0
    filled_size: float = 0.0

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    opened_at: datetime | None = None
    closed_at: datetime | None = None

    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    position_hash: str = ""

    def __post_init__(self) -> None:
        if not self.state_history:
            self._record_state_change(None, self.state, "created")
        if not self.position_hash:
            self.position_hash = self._compute_hash()

    def _record_state_change(
        self, from_state: PaperPositionState | None, to_state: PaperPositionState, reason: str
    ) -> None:
        self.state_history.append(
            {
                "from": from_state.value if from_state else None,
                "to": to_state.value,
                "reason": reason,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    def _compute_hash(self) -> str:
        """INV-CONTRACT-1: Same state → same hash."""
        hashable = {
            "position_id": self.position_id,
            "intent_id": self.intent_id,
            "state": self.state.value,
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "size": self.size,
            "filled_size": self.filled_size,
            "realized_pnl": self.realized_pnl,
        }
        canonical = json.dumps(hashable, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def transition_to(self, new_state: PaperPositionState, reason: str = "") -> None:
        """INV-EXEC-LIFECYCLE-1: Validates transition before applying."""
        if not validate_transition(self.state, new_state):
            raise InvalidTransitionError(self.state, new_state, self.position_id)

        old_state = self.state
        self.state = new_state
        self._record_state_change(old_state, new_state, reason)
        self.position_hash = self._compute_hash()

    def fill(self, price: float, size: float) -> None:
        if self.state in (PaperPositionState.CLOSED, PaperPositionState.HALTED):
            raise PositionMutationError(f"Cannot fill {self.state.value} position")

        if self.entry_price is None:
            self.entry_price = price

        self.filled_size += size

        if self.state == PaperPositionState.PENDING:
            if self.filled_size >= self.size:
                self.transition_to(PaperPositionState.OPEN, f"filled at {price}")
                self.opened_at = datetime.now(UTC)
            else:
                self.transition_to(PaperPositionState.PARTIAL, f"partial fill at {price}")

    def close(self, exit_price: float, reason: str = "exit") -> None:
        if self.state in (PaperPositionState.CLOSED, PaperPositionState.HALTED):
            raise PositionMutationError(f"Cannot close {self.state.value} position")

        self.exit_price = exit_price
        self.closed_at = datetime.now(UTC)

        if self.entry_price is not None:
            direction_mult = 1.0 if self.direction == "LONG" else -1.0
            self.realized_pnl = (exit_price - self.entry_price) * self.filled_size * direction_mult

        self.unrealized_pnl = 0.0
        self.transition_to(PaperPositionState.CLOSED, reason)

    def halt(self, halt_id: str) -> None:
        if self.state in (PaperPositionState.CLOSED, PaperPositionState.HALTED):
            return
        self.transition_to(PaperPositionState.HALTED, f"system halt: {halt_id}")
        self.closed_at = datetime.now(UTC)

    def update_unrealized(self, current_price: float) -> float:
        if self.state not in (PaperPositionState.OPEN, PaperPositionState.PARTIAL):
            return 0.0
        if self.entry_price is None:
            return 0.0
        direction_mult = 1.0 if self.direction == "LONG" else -1.0
        self.unrealized_pnl = (current_price - self.entry_price) * self.filled_size * direction_mult
        return self.unrealized_pnl

    def to_dict(self) -> dict[str, Any]:
        return {
            "position_id": self.position_id,
            "intent_id": self.intent_id,
            "state": self.state.value,
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "size": self.size,
            "filled_size": self.filled_size,
            "created_at": self.created_at.isoformat(),
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "position_hash": self.position_hash,
            "state_history": self.state_history,
        }


# =============================================================================
# PAPER POSITION REGISTRY
# =============================================================================


class PaperPositionRegistry:
    """Registry for paper broker position tracking."""

    def __init__(self) -> None:
        self._positions: dict[str, PaperPosition] = {}
        self._counter = 0

    def create_position(
        self, intent_id: str, symbol: str, direction: str, size: float
    ) -> PaperPosition:
        self._counter += 1
        now = datetime.now(UTC)
        position_id = f"POS-{now.strftime('%Y%m%d%H%M%S')}-{self._counter:04d}"

        position = PaperPosition(
            position_id=position_id,
            intent_id=intent_id,
            state=PaperPositionState.PENDING,
            symbol=symbol,
            direction=direction,
            size=size,
        )

        self._positions[position_id] = position
        return position

    def get_position(self, position_id: str) -> PaperPosition | None:
        return self._positions.get(position_id)

    def get_by_intent(self, intent_id: str) -> PaperPosition | None:
        for pos in self._positions.values():
            if pos.intent_id == intent_id:
                return pos
        return None

    def get_active_positions(self) -> list[PaperPosition]:
        return [
            p
            for p in self._positions.values()
            if p.state not in (PaperPositionState.CLOSED, PaperPositionState.HALTED)
        ]

    def get_closed_positions(self) -> list[PaperPosition]:
        return [p for p in self._positions.values() if p.state == PaperPositionState.CLOSED]

    def halt_all(self, halt_id: str) -> int:
        count = 0
        for position in self.get_active_positions():
            position.halt(halt_id)
            count += 1
        return count

    def get_total_pnl(self) -> dict[str, float]:
        realized = sum(p.realized_pnl for p in self._positions.values())
        unrealized = sum(p.unrealized_pnl for p in self._positions.values())
        return {
            "realized": realized,
            "unrealized": unrealized,
            "total": realized + unrealized,
        }

    def get_state_hash(self) -> str:
        """INV-CONTRACT-1: Same state → same hash."""
        position_hashes = sorted([p.position_hash for p in self._positions.values()])
        combined = "|".join(position_hashes)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "positions": {pid: p.to_dict() for pid, p in self._positions.items()},
            "count": len(self._positions),
            "state_hash": self.get_state_hash(),
        }
