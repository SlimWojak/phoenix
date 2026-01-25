"""
Phoenix Governance — Skeleton for all Phoenix organs

VERSION: 0.2 (lint-hardened)
CONTRACT: GOVERNANCE_INTERFACE_CONTRACT.md

This module provides the GovernanceInterface ABC that all Phoenix
organs must inherit, along with supporting types and mechanisms.

INVARIANTS:
  INV-HALT-1: halt_local_latency < 50ms (proven, not claimed)
  INV-HALT-2: halt_cascade_latency < 500ms (SLO)
  INV-GOV-1: all Phoenix organs inherit GovernanceInterface
  INV-GOV-2: tier violations trigger automatic escalation
  INV-GOV-NO-T1-WRITE-EXEC: T1 may not write execution_state, orders, positions
  INV-GOV-HALT-BEFORE-ACTION: gate checks halt_signal before capital-affecting submit
  INV-CONTRACT-1: deterministic state machine (same input → same output)
"""

# Core interface
from .interface import GovernanceInterface

# Types
from .types import (
    # Enums
    ModuleTier,
    HealthState,
    LifecycleState,
    ViolationSeverity,
    ViolationStatus,
    ErrorCategory,
    ErrorAction,
    
    # Dataclasses
    HaltSignalSetResult,
    AckReceipt,
    HaltCascadeReport,
    StateInput,
    StateTransition,
    QualityTelemetry,
    ViolationTicket,
    ErrorClassification,
    FailureMode,
    DegradationAction,
    SelfCheckReport,
    InitResult,
    
    # Constants
    TIER_PERMISSIONS,
)

# Halt mechanism
from .halt import (
    HaltSignal,
    HaltManager,
    HaltMesh,
)

# Telemetry
from .telemetry import (
    TelemetryEmitter,
    TelemetryAggregator,
    AggregatedTelemetry,
)

# Tokens
from .tokens import (
    ApprovalToken,
    TokenValidator,
    TokenIssuer,
)

# Errors
from .errors import (
    GovernanceError,
    HaltException,
    TierViolationError,
    ApprovalTokenError,
    TokenExpiredError,
    TokenStateMismatchError,
    TokenScopeError,
    HaltBlocksActionError,
    InvariantViolationError,
    InitializationError,
    DependencyError,
    classify_error,
)


__all__ = [
    # Core
    'GovernanceInterface',
    
    # Enums
    'ModuleTier',
    'HealthState',
    'LifecycleState',
    'ViolationSeverity',
    'ViolationStatus',
    'ErrorCategory',
    'ErrorAction',
    
    # Halt
    'HaltSignal',
    'HaltManager',
    'HaltMesh',
    'HaltSignalSetResult',
    'AckReceipt',
    'HaltCascadeReport',
    
    # State
    'StateInput',
    'StateTransition',
    
    # Telemetry
    'QualityTelemetry',
    'TelemetryEmitter',
    'TelemetryAggregator',
    'AggregatedTelemetry',
    
    # Violations
    'ViolationTicket',
    'ErrorClassification',
    'FailureMode',
    'DegradationAction',
    
    # Init
    'SelfCheckReport',
    'InitResult',
    
    # Tokens
    'ApprovalToken',
    'TokenValidator',
    'TokenIssuer',
    
    # Errors
    'GovernanceError',
    'HaltException',
    'TierViolationError',
    'ApprovalTokenError',
    'TokenExpiredError',
    'TokenStateMismatchError',
    'TokenScopeError',
    'HaltBlocksActionError',
    'InvariantViolationError',
    'InitializationError',
    'DependencyError',
    'classify_error',
    
    # Constants
    'TIER_PERMISSIONS',
]

__version__ = '0.2.0'
