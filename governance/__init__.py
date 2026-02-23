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
from .backoff import (
    ExponentialBackoff,
    RetryExhaustedError,
    retry_with_backoff,
    retry_with_backoff_async,
)
from .cartridge import (
    CartridgeConflictError,
    CartridgeHashMismatchError,
    CartridgeInvariantError,
    CartridgeLinter,
    CartridgeLoader,
    CartridgeRegistry,
    CartridgeSchemaError,
    CartridgeValidationError,
    create_minimal_cartridge,
)

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
from .health_fsm import (
    HealthConfig,
    HealthRegistry,
    HealthStateMachine,
    any_system_critical,
    get_all_health_status,
    get_health_fsm,
)
from .insertion import (
    InsertionProtocol,
    InsertionResult,
    quick_insert,
    validate_bounds_ceiling,
)

# Interface
from .interface import GovernanceInterface
from .lease import (
    BoundsBreachError,
    LeaseInterpreter,
    LeaseManager,
    LeaseStateMachine,
    NullBeadEmitter,
    create_lease_from_cartridge,
)

# Lease System (S47)
from .lease_types import (
    AllowedMode,
    CartridgeManifest,
    DrawerConfig,
    DrawerName,
    ExpiryBehavior,
    Lease,
    LeaseBounds,
    LeaseState,
    RenewalType,
    TransitionResult,
)

# Runtime Assertions (S40 Track C)
from .runtime_assertions import (
    ConstitutionalViolation,
    GradeViolation,
    ProvenanceMissing,
    RankingViolation,
    RuntimeConstitutionalChecker,
    ScalarScoreViolation,
    assert_no_grade,
    assert_no_ranking,
    assert_no_scalar_score,
    assert_provenance,
    cfp_output,
    constitutional_boundary,
    enforce_constitution,
    hunt_output,
    validate_output,
)

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
    # Runtime Assertions (S40 Track C)
    "ConstitutionalViolation",
    "ScalarScoreViolation",
    "ProvenanceMissing",
    "RankingViolation",
    "GradeViolation",
    "assert_no_scalar_score",
    "assert_provenance",
    "assert_no_ranking",
    "assert_no_grade",
    "constitutional_boundary",
    "enforce_constitution",
    "validate_output",
    "cfp_output",
    "hunt_output",
    "RuntimeConstitutionalChecker",
    # Lease System (S47)
    "AllowedMode",
    "BoundsBreachError",
    "DrawerConfig",
    "DrawerName",
    "CartridgeConflictError",
    "CartridgeHashMismatchError",
    "CartridgeInvariantError",
    "CartridgeLinter",
    "CartridgeLoader",
    "CartridgeManifest",
    "CartridgeRegistry",
    "CartridgeSchemaError",
    "CartridgeValidationError",
    "create_lease_from_cartridge",
    "create_minimal_cartridge",
    "ExpiryBehavior",
    "InsertionProtocol",
    "InsertionResult",
    "Lease",
    "LeaseBounds",
    "LeaseInterpreter",
    "LeaseManager",
    "LeaseState",
    "LeaseStateMachine",
    "NullBeadEmitter",
    "quick_insert",
    "RenewalType",
    "TransitionResult",
    "validate_bounds_ceiling",
]
