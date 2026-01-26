"""
Phoenix Execution — Halt-first execution with paper broker.

SPRINT: S28.C
STATUS: MOCK_SIGNALS
CAPITAL: PAPER_ONLY

S28.C CAPABILITIES:
- Intent schema enforcement
- Position lifecycle state machine
- Paper broker stub (immediate fills)
- Deterministic replay harness
- Halt integration

CONSTRAINTS:
- PAPER ONLY — no real broker connection
- Mock signals only (NOT Olya methodology)
- Simplified P&L v0 (no fees, no slippage)

INVARIANTS:
- INV-GOV-HALT-BEFORE-ACTION: halt check precedes any action
- INV-CONTRACT-1: deterministic state machine
- INV-EXEC-LIFECYCLE-1: valid state transitions only
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

from .position import (
    Position,
    PositionState,
    PositionRegistry,
    InvalidTransitionError,
    PositionMutationError,
    VALID_TRANSITIONS,
    validate_transition,
)

from .broker_stub import (
    PaperBrokerStub,
    OrderResult,
    ExitResult,
    FillType,
    BrokerHaltedError,
    OrderRejectedError,
    PnLCalculator,
)

from .replay import (
    ReplayHarness,
    ReplayResult,
    ReplayState,
    MockSignal,
    MockSignalGenerator,
    DeterminismVerifier,
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
    # Position
    'Position',
    'PositionState',
    'PositionRegistry',
    'InvalidTransitionError',
    'PositionMutationError',
    'VALID_TRANSITIONS',
    'validate_transition',
    # Broker
    'PaperBrokerStub',
    'OrderResult',
    'ExitResult',
    'FillType',
    'BrokerHaltedError',
    'OrderRejectedError',
    'PnLCalculator',
    # Replay
    'ReplayHarness',
    'ReplayResult',
    'ReplayState',
    'MockSignal',
    'MockSignalGenerator',
    'DeterminismVerifier',
]

__version__ = '0.2.0'  # S28.C


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
