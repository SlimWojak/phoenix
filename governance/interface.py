"""
GovernanceInterface — Abstract Base Class for Phoenix Organs

VERSION: 0.2 (lint-hardened)
CONTRACT: GOVERNANCE_INTERFACE_CONTRACT.md

INVARIANTS:
  INV-HALT-1: halt_local_latency < 50ms (proven, not claimed)
  INV-GOV-1: all Phoenix organs inherit GovernanceInterface
  INV-GOV-2: tier violations trigger automatic escalation
  INV-GOV-NO-T1-WRITE-EXEC: T1 may not write execution_state, orders, positions
  INV-GOV-HALT-BEFORE-ACTION: gate checks halt_signal before capital-affecting submit
  INV-CONTRACT-1: deterministic state machine (same input → same output)
"""

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from .errors import (
    TierViolationError,
    classify_error,
)
from .halt import HaltManager, HaltMesh
from .telemetry import TelemetryEmitter
from .tokens import ApprovalToken, TokenValidator
from .types import (
    TIER_PERMISSIONS,
    AckReceipt,
    DegradationAction,
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
    ViolationTicket,
)


class GovernanceInterface(ABC):
    """
    Abstract base class for all Phoenix organs.

    ALL Phoenix modules MUST inherit this interface.

    Provides:
    - Identity (module_id, tier, invariants)
    - Halt mechanism (request_halt, propagate_halt, check_halt)
    - State machine (process_state, compute_state_hash)
    - Quality telemetry
    - Tier enforcement
    - Violation reporting
    """

    # ==========================================================================
    # IDENTITY (Abstract - must be implemented)
    # ==========================================================================

    @property
    @abstractmethod
    def module_id(self) -> str:
        """Unique identifier for this module."""
        pass

    @property
    @abstractmethod
    def module_tier(self) -> ModuleTier:
        """Module tier (T0, T1, T2)."""
        pass

    @property
    @abstractmethod
    def enforced_invariants(self) -> list[str]:
        """List of invariant IDs this module commits to."""
        pass

    @property
    def yield_points(self) -> list[str]:
        """
        Declared locations where check_halt() is called.

        Override if module has loops or long compute.
        """
        return []

    # ==========================================================================
    # INITIALIZATION
    # ==========================================================================

    def __init__(self):
        """Initialize governance infrastructure."""
        # Will be set in initialize()
        self._halt_manager: HaltManager | None = None
        self._telemetry: TelemetryEmitter | None = None
        self._state: dict = {}
        self._state_hash: str = ""
        self._initialized: bool = False

    def initialize(self, config: dict | None = None) -> InitResult:
        """
        Initialize module.

        - Sets up halt manager
        - Sets up telemetry
        - Runs self_check
        - Registers with mesh
        """
        config = config or {}

        # Create halt manager
        self._halt_manager = HaltManager(module_id=self.module_id)

        # Create telemetry emitter
        self._telemetry = TelemetryEmitter(module_id=self.module_id)

        # Register with global mesh
        mesh = HaltMesh()
        mesh.register(self._halt_manager)

        # Run self-check
        self_check = self.self_check()

        if not self_check.passed():
            return InitResult(success=False, self_check=self_check, error="Self-check failed")

        self._initialized = True
        self._state_hash = self.compute_state_hash()

        return InitResult(success=True, self_check=self_check)

    def self_check(self) -> SelfCheckReport:
        """
        Run self-check on invariants.

        Override to add module-specific checks.
        """
        results = {}
        logic_hashes = {}

        for inv_id in self.enforced_invariants:
            # Default: pass (subclasses should implement real checks)
            results[inv_id] = "PASS"
            logic_hashes[inv_id] = self._compute_logic_hash(inv_id)

        return SelfCheckReport(
            invariants_checked=self.enforced_invariants.copy(),
            results=results,
            logic_hashes=logic_hashes,
        )

    def _compute_logic_hash(self, invariant_id: str) -> str:
        """Compute hash of logic for an invariant."""
        # Simple hash based on module and invariant
        content = f"{self.module_id}|{invariant_id}|v0.2"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def shutdown(self, reason: str) -> bool:
        """
        Graceful shutdown.

        - Halts downstream BEFORE deregistering
        - Deregisters from mesh
        """
        if self._halt_manager:
            # Halt downstream first
            result = self._halt_manager.request_halt()
            if self._halt_manager.get_dependents():
                self._halt_manager.propagate_halt(result.halt_id)

            # Deregister
            mesh = HaltMesh()
            mesh.deregister(self.module_id)

        self._initialized = False
        return True

    # ==========================================================================
    # HALT MECHANISM
    # ==========================================================================

    def request_halt(self) -> HaltSignalSetResult:
        """
        Request halt (local only).

        LATENCY: < 50ms (INV-HALT-1)
        NO IO, NO logging, NO propagation.
        """
        if self._halt_manager is None:
            raise RuntimeError("Module not initialized")
        return self._halt_manager.request_halt()

    def propagate_halt(self, halt_id: str) -> HaltCascadeReport:
        """
        Propagate halt to dependents.

        LATENCY: < 500ms SLO (INV-HALT-2)
        """
        if self._halt_manager is None:
            raise RuntimeError("Module not initialized")
        return self._halt_manager.propagate_halt(halt_id)

    def check_halt(self) -> None:
        """
        Cooperative yield point.

        MUST be called at declared yield_points.
        Raises HaltException if signal set.
        """
        if self._halt_manager:
            self._halt_manager.check_halt()

    def acknowledge_halt(self, halt_id: str) -> AckReceipt:
        """Acknowledge halt from upstream."""
        if self._halt_manager is None:
            raise RuntimeError("Module not initialized")
        return self._halt_manager.acknowledge_halt(halt_id)

    def get_dependents(self) -> list[str]:
        """Return modules that depend on this module."""
        if self._halt_manager is None:
            return []
        return self._halt_manager.get_dependents()

    @property
    def dependency_graph_hash(self) -> str:
        """Hash of [module_id, get_dependents()] for wiring validation."""
        deps = self.get_dependents()
        content = json.dumps([self.module_id] + sorted(deps), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    # ==========================================================================
    # STATE MACHINE
    # ==========================================================================

    @abstractmethod
    def process_state(self, input: StateInput) -> StateTransition:
        """
        Core execution method.

        - Deterministic (same input → same output)
        - Must call check_halt() at yield_points

        Returns:
            StateTransition with previous/new hash and mutations
        """
        pass

    def compute_state_hash(self) -> str:
        """
        Compute current state hash.

        Includes: positions, orders, constraints, risk_state.status
        Excludes: timestamps, heartbeats, diagnostics
        """
        # Filter state to hashable components
        hashable_state = {
            k: v
            for k, v in self._state.items()
            if k not in ["timestamp", "heartbeat", "diagnostics", "last_update"]
        }

        # Canonical JSON serialization
        canonical = json.dumps(hashable_state, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    # ==========================================================================
    # QUALITY TELEMETRY
    # ==========================================================================

    def get_quality_telemetry(self) -> QualityTelemetry:
        """Get current quality telemetry."""
        if self._telemetry is None:
            # Return degraded telemetry if not initialized
            return QualityTelemetry(
                data_health=HealthState.CRITICAL,
                lifecycle_state=LifecycleState.STOPPED,
                quality_score=0.0,
                last_update=datetime.now(UTC),
                anomaly_count=0,
                gap_count=0,
                staleness_seconds=float("inf"),
            )
        return self._telemetry.get_telemetry()

    def report_violation(self, invariant_id: str, evidence: dict) -> ViolationTicket:
        """
        Self-report contract breach.

        Creates violation ticket with auto-escalation schedule.
        """
        now = datetime.now(UTC)

        # Determine severity based on invariant
        if invariant_id.startswith("INV-HALT"):
            severity = ViolationSeverity.CRITICAL
        elif invariant_id.startswith("INV-GOV"):
            severity = ViolationSeverity.VIOLATION
        else:
            severity = ViolationSeverity.WARNING

        ticket = ViolationTicket(
            ticket_id=hashlib.sha256(f"{self.module_id}|{invariant_id}|{now}".encode()).hexdigest()[
                :12
            ],
            invariant_id=invariant_id,
            timestamp=now,
            severity=severity,
            evidence=evidence,
        )

        # If critical, trigger immediate halt
        if severity == ViolationSeverity.CRITICAL and self._halt_manager:
            self._halt_manager.request_halt()

        return ticket

    # ==========================================================================
    # TIER ENFORCEMENT
    # ==========================================================================

    def check_tier_permission(self, action: str, target: str) -> bool:
        """
        Check if action is permitted for this tier.

        Raises:
            TierViolationError if action forbidden
        """
        permissions = TIER_PERMISSIONS.get(self.module_tier, {})
        forbidden = permissions.get("forbidden", [])

        if target in forbidden:
            raise TierViolationError(
                module_tier=self.module_tier.name, attempted_action=action, forbidden=target
            )

        return True

    def validate_t2_action(self, action: str, token: ApprovalToken) -> bool:
        """
        Validate T2 action with approval token.

        Enforces INV-GOV-HALT-BEFORE-ACTION.
        """
        if self.module_tier != ModuleTier.T2:
            raise TierViolationError(
                module_tier=self.module_tier.name,
                attempted_action=action,
                forbidden="T2 action from non-T2 module",
            )

        if self._halt_manager is None:
            raise RuntimeError("Module not initialized")

        validator = TokenValidator(
            halt_signal=self._halt_manager.signal, state_hash_fn=self.compute_state_hash
        )

        return validator.validate(token, action)

    # ==========================================================================
    # ERROR HANDLING
    # ==========================================================================

    def classify_error(self, error: Exception) -> ErrorClassification:
        """Classify error into category and action."""
        return classify_error(error)

    @abstractmethod
    def get_failure_modes(self) -> list[FailureMode]:
        """Return declared failure modes for this module."""
        pass

    @abstractmethod
    def get_degradation_paths(self) -> dict[str, DegradationAction]:
        """Return map of failure mode ID → degradation action."""
        pass
