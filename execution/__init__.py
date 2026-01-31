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
from .intent import (
    CapitalActionForbiddenError,
    Direction,
    ExecutionIntent,
    IntentFactory,
    IntentMutationError,
    IntentStatus,
    IntentType,
)
from .halt_gate import (
    ExecutionGateCoordinator,
    HaltBlockedError,
    HaltCheckResult,
    HaltGate,
    HaltGateViolation,
    halt_gated,
)

# Guard function for capital actions
def guard_capital_action(action: str) -> None:
    """
    Guard against forbidden capital actions.
    
    Raises CapitalActionForbiddenError for any action that would
    directly affect capital (submit_order, execute_order, etc.)
    """
    # Normalize action string (handle both broker_connect and broker.connect)
    normalized = action.replace(".", "_").lower()
    
    forbidden = {"submit_order", "execute_order", "send_order", "broker_connect"}
    if normalized in forbidden:
        raise CapitalActionForbiddenError(
            f"Capital action '{action}' forbidden. Use intents + T2 gate."
        )

__all__ = [
    # Positions
    "Position",
    "PositionState",
    "PositionLifecycle",
    "PositionTracker",
    # Reconciliation
    "Reconciler",
    "DriftType",
    "DriftSeverity",
    # Intents
    "Direction",
    "ExecutionIntent",
    "IntentFactory",
    "IntentType",
    "IntentStatus",
    "IntentMutationError",
    "CapitalActionForbiddenError",
    # Halt gate
    "HaltGate",
    "HaltBlockedError",
    "HaltGateViolation",
    "HaltCheckResult",
    "ExecutionGateCoordinator",
    "halt_gated",
    # Guards
    "guard_capital_action",
]
