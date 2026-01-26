"""
Phoenix Execution — Halt-first execution skeleton.

SPRINT: S27.0
STATUS: SKELETON
CAPITAL: DISABLED

S27 CONSTRAINTS:
- Halt-first wiring (halt check before ANY action)
- Intent objects only (no actual orders)
- NO broker connections
- NO capital mutation

FORBIDDEN:
- submit_order
- execute_order
- broker.connect
- capital.allocate

INVARIANTS:
- INV-GOV-HALT-BEFORE-ACTION: halt check precedes any action
- INV-EXEC-NO-CAPITAL: no capital actions in S27
"""

from .intent import (
    ExecutionIntent,
    IntentFactory,
    IntentType,
    IntentStatus,
    Direction,
    IntentMutationError,
    CapitalActionForbiddenError,
)

from .halt_gate import (
    HaltGate,
    HaltCheckResult,
    HaltGateViolation,
    HaltBlockedError,
    ExecutionGateCoordinator,
    halt_gated,
)

__all__ = [
    # Intent
    'ExecutionIntent',
    'IntentFactory',
    'IntentType',
    'IntentStatus',
    'Direction',
    'IntentMutationError',
    'CapitalActionForbiddenError',
    # Halt Gate
    'HaltGate',
    'HaltCheckResult',
    'HaltGateViolation',
    'HaltBlockedError',
    'ExecutionGateCoordinator',
    'halt_gated',
]

__version__ = '0.1.0'


# =============================================================================
# CAPITAL GUARD
# =============================================================================

# These patterns are FORBIDDEN in S27
FORBIDDEN_ACTIONS = frozenset([
    'submit_order',
    'execute_order',
    'broker',
    'connect',
    'send_order',
    'place_trade',
    'allocate_capital',
])


def guard_capital_action(action: str) -> None:
    """
    Guard against capital actions.
    
    Raises CapitalActionForbiddenError if action is forbidden.
    """
    action_lower = action.lower()
    for forbidden in FORBIDDEN_ACTIONS:
        if forbidden in action_lower:
            raise CapitalActionForbiddenError(action)
