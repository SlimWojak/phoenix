"""
Execution — Order execution and position management
===================================================

S32: EXECUTION_PATH

Contains position lifecycle, reconciliation, and promotion.

CONSTITUTIONAL:
- Human sovereignty over capital is absolute
- No automatic retry without human decision
- Reconciliation is read-only (never mutates state)
"""

from .positions import (
    Position,
    PositionLifecycle,
    PositionState,
    PositionTracker,
)
from .reconciliation import (
    DriftSeverity,
    DriftType,
    Reconciler,
)

__all__ = [
    "Position",
    "PositionState",
    "PositionLifecycle",
    "PositionTracker",
    "Reconciler",
    "DriftType",
    "DriftSeverity",
]
