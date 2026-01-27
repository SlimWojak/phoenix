"""
Position States — State machine definition
==========================================

S32: EXECUTION_PATH

Defines the 9-state position lifecycle with valid transitions.

States:
- PROPOSED: Intent received, awaiting T2 approval
- APPROVED: Human approved, T2 token issued
- SUBMITTED: Order sent to broker, awaiting fill
- STALLED: Broker timeout (60s without ACK) — WP_C1
- FILLED: Entry executed, position open
- MANAGED: SL/TP in place, monitoring
- CLOSED: Position exited
- CANCELLED: Order cancelled before fill
- REJECTED: Broker rejected order
- EXPIRED: T2 token expired before submission

INVARIANT: INV-POSITION-SM-1
Only valid state transitions are allowed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PositionState(Enum):
    """Position lifecycle states."""

    # Pre-execution states
    PROPOSED = "PROPOSED"      # Intent received, awaiting T2
    APPROVED = "APPROVED"      # Human approved, token issued
    SUBMITTED = "SUBMITTED"    # Sent to broker, awaiting fill

    # Problem states
    STALLED = "STALLED"        # WP_C1: 60s timeout, no broker ACK
    REJECTED = "REJECTED"      # Broker rejected order
    EXPIRED = "EXPIRED"        # T2 token expired before submission

    # Active states
    FILLED = "FILLED"          # Entry executed
    MANAGED = "MANAGED"        # SL/TP in place

    # Terminal states
    CLOSED = "CLOSED"          # Exited (win/loss/BE)
    CANCELLED = "CANCELLED"    # Cancelled before fill

    @property
    def is_terminal(self) -> bool:
        """Check if state is terminal."""
        return self in {
            PositionState.CLOSED,
            PositionState.CANCELLED,
            PositionState.REJECTED,
            PositionState.EXPIRED,
        }

    @property
    def is_active(self) -> bool:
        """Check if position is actively in market."""
        return self in {
            PositionState.FILLED,
            PositionState.MANAGED,
        }

    @property
    def requires_attention(self) -> bool:
        """Check if state requires human attention."""
        return self in {
            PositionState.STALLED,
            PositionState.REJECTED,
        }


@dataclass
class StateTransition:
    """Definition of a valid state transition."""

    from_state: PositionState
    to_state: PositionState
    trigger: str
    requires_human: bool = False
    emits_alert: bool = False

    @property
    def key(self) -> tuple[PositionState, PositionState]:
        """Transition key for lookup."""
        return (self.from_state, self.to_state)


# Valid state transitions (INV-POSITION-SM-1)
VALID_TRANSITIONS: dict[tuple[PositionState, PositionState], StateTransition] = {}


def _register_transition(
    from_state: PositionState,
    to_state: PositionState,
    trigger: str,
    requires_human: bool = False,
    emits_alert: bool = False,
) -> None:
    """Register a valid transition."""
    transition = StateTransition(
        from_state=from_state,
        to_state=to_state,
        trigger=trigger,
        requires_human=requires_human,
        emits_alert=emits_alert,
    )
    VALID_TRANSITIONS[transition.key] = transition


# Register all valid transitions
# PROPOSED transitions
_register_transition(PositionState.PROPOSED, PositionState.APPROVED, "T2 token issued")
_register_transition(
    PositionState.PROPOSED, PositionState.CANCELLED, "Human passes", requires_human=True
)

# APPROVED transitions
_register_transition(PositionState.APPROVED, PositionState.SUBMITTED, "Order sent")
_register_transition(
    PositionState.APPROVED, PositionState.EXPIRED, "Token timeout", emits_alert=True
)

# SUBMITTED transitions
_register_transition(PositionState.SUBMITTED, PositionState.FILLED, "Broker confirms")
_register_transition(
    PositionState.SUBMITTED, PositionState.STALLED, "60s timeout", emits_alert=True
)  # WP_C1
_register_transition(
    PositionState.SUBMITTED, PositionState.REJECTED, "Broker rejects", emits_alert=True
)

# STALLED transitions (WP_C1: NO auto-retry)
_register_transition(PositionState.STALLED, PositionState.FILLED, "Late broker fill")
_register_transition(
    PositionState.STALLED, PositionState.CANCELLED, "Human cancels", requires_human=True
)

# FILLED transitions
_register_transition(PositionState.FILLED, PositionState.MANAGED, "SL/TP placed")

# MANAGED transitions
_register_transition(PositionState.MANAGED, PositionState.CLOSED, "Exit triggered")


def is_valid_transition(from_state: PositionState, to_state: PositionState) -> bool:
    """Check if a transition is valid."""
    return (from_state, to_state) in VALID_TRANSITIONS


def get_transition(from_state: PositionState, to_state: PositionState) -> StateTransition | None:
    """Get transition definition if valid."""
    return VALID_TRANSITIONS.get((from_state, to_state))


def get_valid_next_states(current_state: PositionState) -> list[PositionState]:
    """Get all valid next states from current state."""
    return [
        trans.to_state
        for trans in VALID_TRANSITIONS.values()
        if trans.from_state == current_state
    ]


class TransitionError(Exception):
    """Raised when an invalid transition is attempted."""

    def __init__(
        self,
        from_state: PositionState,
        to_state: PositionState,
        reason: str = "",
    ) -> None:
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        valid_next = get_valid_next_states(from_state)
        super().__init__(
            f"Invalid transition {from_state.value} → {to_state.value}. "
            f"Valid: {[s.value for s in valid_next]}. {reason}"
        )
