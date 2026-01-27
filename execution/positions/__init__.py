"""
Positions — Position lifecycle management
=========================================

S32: EXECUTION_PATH

9-state position lifecycle with STALLED handling.

INVARIANTS:
- INV-POSITION-SM-1: Only valid state transitions allowed
- INV-POSITION-AUDIT-1: POSITION bead at every transition
- INV-POSITION-SUBMITTED-TTL-1: SUBMITTED > 60s → STALLED + alert

WATCHPOINTS:
- WP_C1: STALLED with alert + bead + reason
- WP_C3: partial_fill_ratio drift detection
"""

from .lifecycle import Position, PositionLifecycle
from .states import VALID_TRANSITIONS, PositionState, StateTransition
from .tracker import PositionTracker

__all__ = [
    "PositionState",
    "StateTransition",
    "VALID_TRANSITIONS",
    "Position",
    "PositionLifecycle",
    "PositionTracker",
]
