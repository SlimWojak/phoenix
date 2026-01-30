"""
Governance — Human sovereignty enforcement
==========================================

S32: EXECUTION_PATH

Contains T2 approval workflow, halt mechanisms, and tier enforcement.
This is where human authority over capital is enforced.

CONSTITUTIONAL:
- Human sovereignty over capital is absolute
- Tier 2 (capital-adjacent) always requires human gate
- Forge amplifies judgment, never replaces it
"""

# Errors
from .errors import (
    ApprovalTokenError,
    DependencyError,
    GovernanceError,
    HaltBlocksActionError,
    HaltError,
    HaltException,  # Alias for HaltError
    InitializationError,
    InvariantViolationError,
    TierViolationError,
    TokenExpiredError,
    TokenScopeError,
    TokenStateMismatchError,
    classify_error,
)

# Halt mechanism
from .halt import HaltManager, HaltMesh, HaltSignal

# Interface
from .interface import GovernanceInterface

# Stale gate
from .stale_gate import StaleCheckResult, StaleGate

# T2 workflow
from .t2 import EvidenceBundle, T2Workflow, Token, TokenStatus

# Telemetry
from .telemetry import (
    AggregatedTelemetry,
    BoundsViolationTelemetry,
    CascadeTimingTelemetry,
    ExtendedTelemetryEmitter,
    SignalGenerationTelemetry,
    TelemetryAggregator,
    TelemetryEmitter,
)

# Tokens
from .tokens import ApprovalToken, TokenIssuer, TokenValidator

# Self-Healing (S40 Track A)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitHalfOpenError,
    CircuitOpenError,
    CircuitState,
    get_all_circuit_metrics,
    get_circuit_breaker,
)
from .backoff import (
    ExponentialBackoff,
    RetryExhaustedError,
    retry_with_backoff,
    retry_with_backoff_async,
)
from .health_fsm import (
    HealthConfig,
    HealthRegistry,
    HealthStateMachine,
    any_system_critical,
    get_all_health_status,
    get_health_fsm,
)

# Types
from .types import (
    TIER_PERMISSIONS,
    AckReceipt,
    DegradationAction,
    ErrorAction,
    ErrorCategory,
    ErrorClassification,
    FailureMode,
    HaltCascadeReport,
    HaltSignalSetResult,
    HealthState,
    InitResult,
    LifecycleState,
    ModuleTier,
    QualityTelemetry,
    SelfCheckReport,
    StateInput,
    StateTransition,
    ViolationSeverity,
    ViolationStatus,
    ViolationTicket,
)

__all__ = [
    # Errors
    "GovernanceError",
    "HaltError",
    "HaltException",  # Alias for HaltError
    "TierViolationError",
    "ApprovalTokenError",
    "TokenExpiredError",
    "TokenStateMismatchError",
    "TokenScopeError",
    "HaltBlocksActionError",
    "InvariantViolationError",
    "InitializationError",
    "DependencyError",
    "classify_error",
    # Halt
    "HaltSignal",
    "HaltManager",
    "HaltMesh",
    # Interface
    "GovernanceInterface",
    # Stale gate
    "StaleGate",
    "StaleCheckResult",
    # T2
    "T2Workflow",
    "Token",
    "TokenStatus",
    "EvidenceBundle",
    # Telemetry
    "TelemetryEmitter",
    "AggregatedTelemetry",
    "TelemetryAggregator",
    "CascadeTimingTelemetry",
    "SignalGenerationTelemetry",
    "BoundsViolationTelemetry",
    "ExtendedTelemetryEmitter",
    # Tokens
    "ApprovalToken",
    "TokenValidator",
    "TokenIssuer",
    # Types - Enums
    "ModuleTier",
    "HealthState",
    "LifecycleState",
    "ViolationSeverity",
    "ViolationStatus",
    "ErrorCategory",
    "ErrorAction",
    # Types - Dataclasses
    "HaltSignalSetResult",
    "AckReceipt",
    "HaltCascadeReport",
    "StateInput",
    "StateTransition",
    "QualityTelemetry",
    "ViolationTicket",
    "ErrorClassification",
    "FailureMode",
    "DegradationAction",
    "SelfCheckReport",
    "InitResult",
    # Constants
    "TIER_PERMISSIONS",
    # Self-Healing (S40 Track A)
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "CircuitState",
    "CircuitOpenError",
    "CircuitHalfOpenError",
    "get_circuit_breaker",
    "get_all_circuit_metrics",
    "ExponentialBackoff",
    "RetryExhaustedError",
    "retry_with_backoff",
    "retry_with_backoff_async",
    "HealthStateMachine",
    "HealthConfig",
    "HealthRegistry",
    "get_health_fsm",
    "get_all_health_status",
    "any_system_critical",
]
