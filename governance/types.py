"""
Governance Types — Enums and Dataclasses for Phoenix Governance

VERSION: 0.2 (lint-hardened)
CONTRACT: GOVERNANCE_INTERFACE_CONTRACT.md
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================


class ModuleTier(Enum):
    """
    Module tier classification.

    T0: Read-only, no capital impact
    T1: Capital-adjacent, automated gates
    T2: Capital-affecting, human gate required
    """

    T0 = 0  # Read-only
    T1 = 1  # Capital-adjacent
    T2 = 2  # Capital-affecting


class HealthState(Enum):
    """Data/system health states."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class LifecycleState(Enum):
    """Module lifecycle states."""

    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class ViolationSeverity(Enum):
    """Violation severity levels."""

    WARNING = "WARNING"
    VIOLATION = "VIOLATION"
    CRITICAL = "CRITICAL"


class ViolationStatus(Enum):
    """Violation ticket status."""

    OPEN = "OPEN"
    ACKED = "ACKED"
    RESOLVED = "RESOLVED"
    WAIVED = "WAIVED"


class ErrorCategory(Enum):
    """Error classification categories."""

    RECOVERABLE = "RECOVERABLE"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class ErrorAction(Enum):
    """Action to take for classified error."""

    RETRY = "RETRY"
    DEGRADE = "DEGRADE"
    HALT = "HALT"


# =============================================================================
# HALT DATACLASSES
# =============================================================================


@dataclass
class HaltSignalSetResult:
    """Result of request_halt() call."""

    success: bool
    latency_ms: float
    halt_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AckReceipt:
    """Acknowledgment receipt for halt propagation."""

    module_id: str
    ack: bool
    module_state: LifecycleState
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HaltCascadeReport:
    """Report of halt cascade propagation."""

    halt_id: str
    propagated_to: list[str]
    acks_received: list[AckReceipt]
    acks_failed: list[str]
    total_latency_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# =============================================================================
# STATE DATACLASSES
# =============================================================================


@dataclass
class StateInput:
    """Input for state machine processing."""

    data: dict
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def compute_hash(self) -> str:
        """Compute deterministic hash of input."""
        canonical = json.dumps(self.data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass
class StateTransition:
    """Result of state machine transition."""

    previous_hash: str
    new_hash: str
    mutations: list[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# =============================================================================
# QUALITY DATACLASSES
# =============================================================================


@dataclass
class QualityTelemetry:
    """Quality telemetry data."""

    data_health: HealthState
    lifecycle_state: LifecycleState
    quality_score: float  # 0.0-1.0
    last_update: datetime
    anomaly_count: int = 0
    gap_count: int = 0
    staleness_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "data_health": self.data_health.value,
            "lifecycle_state": self.lifecycle_state.value,
            "quality_score": self.quality_score,
            "last_update": self.last_update.isoformat(),
            "anomaly_count": self.anomaly_count,
            "gap_count": self.gap_count,
            "staleness_seconds": self.staleness_seconds,
        }


# =============================================================================
# VIOLATION DATACLASSES
# =============================================================================


@dataclass
class ViolationTicket:
    """Contract violation ticket."""

    ticket_id: str
    invariant_id: str
    timestamp: datetime
    severity: ViolationSeverity
    status: ViolationStatus = ViolationStatus.OPEN
    evidence: dict = field(default_factory=dict)
    auto_escalate_cto_at: datetime | None = None  # +12h
    auto_escalate_sovereign_at: datetime | None = None  # +24h

    def __post_init__(self):
        """Set escalation times if not provided."""
        from datetime import timedelta

        if self.auto_escalate_cto_at is None:
            self.auto_escalate_cto_at = self.timestamp + timedelta(hours=12)
        if self.auto_escalate_sovereign_at is None:
            self.auto_escalate_sovereign_at = self.timestamp + timedelta(hours=24)


# =============================================================================
# ERROR DATACLASSES
# =============================================================================


@dataclass
class ErrorClassification:
    """Classification result for an error."""

    category: ErrorCategory
    action: ErrorAction


@dataclass
class FailureMode:
    """Declared failure mode for a module."""

    id: str
    trigger: str
    classification: ErrorClassification


@dataclass
class DegradationAction:
    """Action to take when degradation occurs."""

    action_type: str  # e.g., "disable_feature", "use_fallback"
    params: dict = field(default_factory=dict)


# =============================================================================
# INIT/CHECK DATACLASSES
# =============================================================================


@dataclass
class SelfCheckReport:
    """Result of module self-check."""

    invariants_checked: list[str]
    results: dict[str, str]  # invariant_id -> "PASS" | "FAIL"
    logic_hashes: dict[str, str]

    def passed(self) -> bool:
        return all(r == "PASS" for r in self.results.values())


@dataclass
class InitResult:
    """Result of module initialization."""

    success: bool
    self_check: SelfCheckReport
    error: str | None = None


# =============================================================================
# TIER PERMISSIONS
# =============================================================================

TIER_PERMISSIONS = {
    ModuleTier.T0: {
        "writes": [],
        "reads": ["market_data", "indicators"],
        "forbidden": ["advisory_state", "execution_state", "orders", "positions"],
    },
    ModuleTier.T1: {
        "writes": ["advisory_state"],
        "reads": ["market_data", "indicators", "advisory_state"],
        "forbidden": ["execution_state", "orders", "positions"],
        "gate": "automated",
        "gate_requirements": {"quality_score_min": 0.70, "no_critical_violations_hours": 24},
    },
    ModuleTier.T2: {
        "writes": ["execution_state", "orders", "positions"],
        "reads": ["market_data", "indicators", "advisory_state", "execution_state"],
        "forbidden": [],
        "gate": "human",
        "requires_approval_token": True,
        "pre_check": "halt_signal == FALSE",
    },
}
