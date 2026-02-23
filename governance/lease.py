"""
Lease State Machine and Interpreter
====================================

Sprint: S47 LEASE_IMPLEMENTATION
Design Spec: docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md

Invariants:
  INV-HALT-OVERRIDES-LEASE: Halt wins. Always. <50ms.
  INV-NO-SESSION-OVERLAP: One lease per session
  INV-LEASE-CEILING: Lease bounds = ceiling, Cartridge = floor
  INV-EXPIRY-BUFFER: Software halt governance_buffer_seconds BEFORE legal expiry
  INV-STATE-LOCK: State transition guard prevents race conditions

State Machine (Section 4):
  DRAFT → ACTIVE (activation ceremony)
  ACTIVE → EXPIRED (automatic, at expires_at - governance_buffer)
  ACTIVE → REVOKED (human revocation)
  ACTIVE → HALTED (bounds exceeded OR global halt)
  HALTED → REVOKED (human must revoke; NO resurrection)

Terminal States: EXPIRED, REVOKED
"""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .halt import HaltManager, HaltMesh
from .lease_types import (
    AllowedMode,
    Lease,
    LeaseActivationBead,
    LeaseExpiryBead,
    LeaseHaltBead,
    LeaseRevocationBead,
    LeaseState,
    StateLockBead,
    TransitionResult,
)

if TYPE_CHECKING:
    from .lease_types import BeadType


# =============================================================================
# BEAD EMITTER PROTOCOL
# =============================================================================


@runtime_checkable
class BeadEmitter(Protocol):
    """Protocol for bead emission — allows dependency injection."""

    def emit(self, bead: BeadType) -> None:
        """Emit a bead to the chronicle."""
        ...


class NullBeadEmitter:
    """No-op bead emitter for testing."""

    def __init__(self):
        self.beads: list[BeadType] = []

    def emit(self, bead: BeadType) -> None:
        """Store bead for test assertions."""
        self.beads.append(bead)


# =============================================================================
# LEASE STATE MACHINE
# =============================================================================


# Valid transitions: from_state -> [to_states]
VALID_TRANSITIONS: dict[LeaseState, list[LeaseState]] = {
    LeaseState.DRAFT: [LeaseState.ACTIVE],
    LeaseState.ACTIVE: [LeaseState.EXPIRED, LeaseState.REVOKED, LeaseState.HALTED],
    LeaseState.HALTED: [LeaseState.REVOKED],  # HALTED can ONLY go to REVOKED
    LeaseState.EXPIRED: [],  # Terminal
    LeaseState.REVOKED: [],  # Terminal
}

TERMINAL_STATES = frozenset({LeaseState.EXPIRED, LeaseState.REVOKED})


class LeaseStateMachine:
    """
    Thread-safe lease state machine.

    All transitions:
      1. Verify state_lock_hash (INV-STATE-LOCK)
      2. Check valid transition
      3. Emit StateLockBead
      4. Update state
      5. Emit transition-specific bead
    """

    def __init__(
        self,
        lease: Lease,
        bead_emitter: BeadEmitter | None = None,
        halt_manager: HaltManager | None = None,
    ):
        self._lease = lease
        self._emitter = bead_emitter or NullBeadEmitter()
        self._halt_manager = halt_manager
        self._lock = threading.Lock()

    @property
    def lease(self) -> Lease:
        """Get current lease (read-only view)."""
        return self._lease

    @property
    def state(self) -> LeaseState:
        """Get current state."""
        return self._lease.status.current

    @property
    def is_active(self) -> bool:
        """Check if lease is active."""
        return self._lease.status.current == LeaseState.ACTIVE

    @property
    def is_terminal(self) -> bool:
        """Check if lease is in terminal state."""
        return self._lease.status.current in TERMINAL_STATES

    def _verify_state_lock(self, expected_hash: str | None) -> bool:
        """
        Verify state_lock_hash for race protection.

        INV-STATE-LOCK: Concurrent operations that fail hash check = REJECT
        """
        if expected_hash is None:
            # First transition — no prior hash to verify
            return True

        current_hash = self._lease.compute_state_hash()
        return current_hash == expected_hash

    def _emit_state_lock_bead(
        self,
        prior_state: LeaseState,
        requested_transition: str,
        result: TransitionResult,
    ) -> None:
        """Emit StateLockBead for audit trail."""
        bead = StateLockBead(
            lease_id=self._lease.identity.lease_id,
            prior_state=prior_state,
            prior_state_hash=self._lease.governance.state_lock_hash or "",
            requested_transition=requested_transition,
            transition_result=result,
        )
        self._emitter.emit(bead)

    def activate(self, expected_hash: str | None = None) -> TransitionResult:
        """
        Transition DRAFT → ACTIVE.

        Args:
            expected_hash: Prior state hash for race protection

        Returns:
            TransitionResult indicating success or failure reason
        """
        with self._lock:
            # Verify valid transition
            if self.state != LeaseState.DRAFT:
                self._emit_state_lock_bead(
                    self.state,
                    "DRAFT→ACTIVE",
                    TransitionResult.REJECTED_INVALID_TRANSITION,
                )
                return TransitionResult.REJECTED_INVALID_TRANSITION

            # Verify state lock
            if not self._verify_state_lock(expected_hash):
                self._emit_state_lock_bead(
                    self.state,
                    "DRAFT→ACTIVE",
                    TransitionResult.REJECTED_HASH_MISMATCH,
                )
                return TransitionResult.REJECTED_HASH_MISMATCH

            # Update state
            now = datetime.now(UTC)
            self._lease.status.current = LeaseState.ACTIVE
            self._lease.status.activated_at = now
            self._lease.governance.state_lock_hash = self._lease.compute_state_hash()

            # Emit beads
            self._emit_state_lock_bead(
                LeaseState.DRAFT,
                "DRAFT→ACTIVE",
                TransitionResult.SUCCESS,
            )

            activation_bead = LeaseActivationBead(
                lease_id=self._lease.identity.lease_id,
                strategy_ref=self._lease.subject.strategy_ref,
                bounds_snapshot=self._lease.bounds.model_dump(),
            )
            self._emitter.emit(activation_bead)

            return TransitionResult.SUCCESS

    def expire(
        self, expected_hash: str | None = None, final_stats: dict | None = None
    ) -> TransitionResult:
        """
        Transition ACTIVE → EXPIRED.

        Automatic expiry at (expires_at - governance_buffer_seconds).
        """
        with self._lock:
            if self.state != LeaseState.ACTIVE:
                self._emit_state_lock_bead(
                    self.state,
                    "ACTIVE→EXPIRED",
                    TransitionResult.REJECTED_INVALID_TRANSITION,
                )
                return TransitionResult.REJECTED_INVALID_TRANSITION

            if not self._verify_state_lock(expected_hash):
                self._emit_state_lock_bead(
                    self.state,
                    "ACTIVE→EXPIRED",
                    TransitionResult.REJECTED_HASH_MISMATCH,
                )
                return TransitionResult.REJECTED_HASH_MISMATCH

            # Update state
            self._lease.status.current = LeaseState.EXPIRED
            self._lease.governance.state_lock_hash = self._lease.compute_state_hash()

            # Emit beads
            self._emit_state_lock_bead(
                LeaseState.ACTIVE,
                "ACTIVE→EXPIRED",
                TransitionResult.SUCCESS,
            )

            expiry_bead = LeaseExpiryBead(
                lease_id=self._lease.identity.lease_id,
                final_stats=final_stats or {},
            )
            self._emitter.emit(expiry_bead)

            return TransitionResult.SUCCESS

    def revoke(
        self,
        revoked_by: str,
        reason: str,
        expected_hash: str | None = None,
    ) -> TransitionResult:
        """
        Transition ACTIVE → REVOKED or HALTED → REVOKED.

        Human-initiated revocation.
        """
        with self._lock:
            # Valid from ACTIVE or HALTED
            if self.state not in (LeaseState.ACTIVE, LeaseState.HALTED):
                self._emit_state_lock_bead(
                    self.state,
                    f"{self.state.value}→REVOKED",
                    TransitionResult.REJECTED_INVALID_TRANSITION,
                )
                return TransitionResult.REJECTED_INVALID_TRANSITION

            if not self._verify_state_lock(expected_hash):
                self._emit_state_lock_bead(
                    self.state,
                    f"{self.state.value}→REVOKED",
                    TransitionResult.REJECTED_HASH_MISMATCH,
                )
                return TransitionResult.REJECTED_HASH_MISMATCH

            prior = self.state

            # Update state
            now = datetime.now(UTC)
            self._lease.status.current = LeaseState.REVOKED
            self._lease.status.revoked_at = now
            self._lease.status.revocation_reason = reason
            self._lease.governance.state_lock_hash = self._lease.compute_state_hash()

            # Emit beads
            self._emit_state_lock_bead(
                prior,
                f"{prior.value}→REVOKED",
                TransitionResult.SUCCESS,
            )

            revocation_bead = LeaseRevocationBead(
                lease_id=self._lease.identity.lease_id,
                revoked_by=revoked_by,
                reason=reason,
            )
            self._emitter.emit(revocation_bead)

            return TransitionResult.SUCCESS

    def halt(
        self,
        trigger: str,
        bound_exceeded: str,
        value: float | int,
        expected_hash: str | None = None,
    ) -> TransitionResult:
        """
        Transition ACTIVE → HALTED.

        Auto-halt from bounds breach OR global halt signal.
        INV-HALT-OVERRIDES-LEASE: This always wins, <50ms.
        """
        with self._lock:
            if self.state != LeaseState.ACTIVE:
                self._emit_state_lock_bead(
                    self.state,
                    "ACTIVE→HALTED",
                    TransitionResult.REJECTED_INVALID_TRANSITION,
                )
                return TransitionResult.REJECTED_INVALID_TRANSITION

            # NOTE: For halt, we don't verify state_lock_hash
            # INV-HALT-OVERRIDES-LEASE: Halt must succeed regardless of race

            prior = self.state

            # Update state
            now = datetime.now(UTC)
            self._lease.status.current = LeaseState.HALTED
            self._lease.status.halted_at = now
            self._lease.status.halt_trigger = trigger
            self._lease.governance.state_lock_hash = self._lease.compute_state_hash()

            # Emit beads
            self._emit_state_lock_bead(
                prior,
                "ACTIVE→HALTED",
                TransitionResult.SUCCESS,
            )

            halt_bead = LeaseHaltBead(
                lease_id=self._lease.identity.lease_id,
                trigger=trigger,
                bound_exceeded=bound_exceeded,
                value=value,
            )
            self._emitter.emit(halt_bead)

            return TransitionResult.SUCCESS


# =============================================================================
# LEASE INTERPRETER — Bounds Checking
# =============================================================================


class BoundsBreachError(Exception):
    """Raised when a lease bound is breached."""

    def __init__(self, bound_name: str, current_value: float | int, limit: float | int):
        self.bound_name = bound_name
        self.current_value = current_value
        self.limit = limit
        super().__init__(f"Bound '{bound_name}' breached: {current_value} > {limit}")


class LeaseInterpreter:
    """
    Interprets lease bounds and enforces constraints.

    Design Decision D8: OR logic for bounds (any breach = halt)
    """

    def __init__(self, state_machine: LeaseStateMachine):
        self._state_machine = state_machine

    @property
    def lease(self) -> Lease:
        return self._state_machine.lease

    @property
    def is_active(self) -> bool:
        return self._state_machine.is_active

    def check_all_bounds(
        self,
        current_drawdown_pct: float,
        consecutive_losses: int,
        daily_loss_pct: float | None = None,
    ) -> list[BoundsBreachError]:
        """
        Check all bounds and return list of breaches.

        Design Decision D8: OR logic — any breach = halt.

        Returns:
            List of breaches (empty if all bounds OK)
        """
        if not self._state_machine.is_active:
            return []

        breaches = []
        bounds = self.lease.bounds

        # Check drawdown
        if current_drawdown_pct > bounds.max_drawdown_pct:
            breaches.append(
                BoundsBreachError(
                    "max_drawdown_pct",
                    current_drawdown_pct,
                    bounds.max_drawdown_pct,
                )
            )

        # Check consecutive losses
        if consecutive_losses > bounds.max_consecutive_losses:
            breaches.append(
                BoundsBreachError(
                    "max_consecutive_losses",
                    consecutive_losses,
                    bounds.max_consecutive_losses,
                )
            )

        # Check daily loss limit (if set)
        if daily_loss_pct is not None and bounds.daily_loss_limit_pct is not None:
            if daily_loss_pct > bounds.daily_loss_limit_pct:
                breaches.append(
                    BoundsBreachError(
                        "daily_loss_limit_pct",
                        daily_loss_pct,
                        bounds.daily_loss_limit_pct,
                    )
                )

        return breaches

    def enforce_bounds(
        self,
        current_drawdown_pct: float,
        consecutive_losses: int,
        daily_loss_pct: float | None = None,
    ) -> TransitionResult | None:
        """
        Check bounds and trigger halt if any breached.

        Returns:
            TransitionResult if halt was triggered, None if bounds OK
        """
        breaches = self.check_all_bounds(
            current_drawdown_pct,
            consecutive_losses,
            daily_loss_pct,
        )

        if not breaches:
            return None

        # First breach triggers halt (OR logic)
        breach = breaches[0]
        return self._state_machine.halt(
            trigger="BOUNDS_BREACH",
            bound_exceeded=breach.bound_name,
            value=breach.current_value,
        )

    def is_pair_allowed(self, pair: str) -> bool:
        """Check if pair is allowed by lease bounds."""
        bounds = self.lease.bounds
        if bounds.allowed_pairs_mode == AllowedMode.ALL:
            return True
        return pair in bounds.allowed_pairs

    def is_session_allowed(self, session: str) -> bool:
        """Check if session is allowed by lease bounds."""
        bounds = self.lease.bounds
        if bounds.allowed_sessions_mode == AllowedMode.ALL:
            return True
        return session in bounds.allowed_sessions

    def check_position_size(self, proposed_size_pct: float) -> bool:
        """Check if position size is within lease cap."""
        bounds = self.lease.bounds
        if bounds.position_size_cap is None:
            return True
        return proposed_size_pct <= bounds.position_size_cap

    def get_effective_expiry(self) -> datetime:
        """
        Get effective expiry time (with governance buffer).

        INV-EXPIRY-BUFFER: Software halt governance_buffer_seconds BEFORE legal expiry.
        """
        legal_expiry = self.lease.duration.expires_at
        buffer_seconds = self.lease.halt_integration.governance_buffer_seconds
        return legal_expiry - timedelta(seconds=buffer_seconds)

    def check_expiry(self, now: datetime | None = None) -> bool:
        """
        Check if lease should expire.

        Returns True if current time >= effective expiry.
        """
        if now is None:
            now = datetime.now(UTC)

        effective_expiry = self.get_effective_expiry()
        return now >= effective_expiry


# =============================================================================
# LEASE MANAGER — Singleton-ish Process-Wide Coordination
# =============================================================================


class LeaseManager:
    """
    Process-wide lease management.

    INV-NO-SESSION-OVERLAP: One lease per session.
    Integrates with HaltMesh for global halt coordination.
    """

    _instance: LeaseManager | None = None
    _lock = threading.Lock()

    def __new__(cls) -> LeaseManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._active_lease: LeaseStateMachine | None = None
                    cls._instance._bead_emitter: BeadEmitter | None = None
                    cls._instance._halt_mesh: HaltMesh | None = None
        return cls._instance

    def configure(
        self,
        bead_emitter: BeadEmitter | None = None,
        halt_mesh: HaltMesh | None = None,
    ) -> None:
        """Configure manager with dependencies."""
        self._bead_emitter = bead_emitter
        self._halt_mesh = halt_mesh or HaltMesh()

    @property
    def has_active_lease(self) -> bool:
        """Check if there's currently an active lease."""
        return self._active_lease is not None and self._active_lease.is_active

    @property
    def active_lease(self) -> LeaseStateMachine | None:
        """Get active lease state machine (or None)."""
        if self._active_lease and self._active_lease.is_active:
            return self._active_lease
        return None

    def activate_lease(self, lease: Lease) -> tuple[LeaseStateMachine, TransitionResult]:
        """
        Activate a new lease.

        INV-NO-SESSION-OVERLAP: Rejects if another lease is already active.
        """
        with self._lock:
            # Check for existing active lease
            if self.has_active_lease:
                # Return current + rejection
                assert self._active_lease is not None
                return self._active_lease, TransitionResult.REJECTED_LEASE_NOT_ACTIVE

            # Create state machine
            state_machine = LeaseStateMachine(
                lease=lease,
                bead_emitter=self._bead_emitter,
            )

            # Attempt activation
            result = state_machine.activate()

            if result == TransitionResult.SUCCESS:
                self._active_lease = state_machine

            return state_machine, result

    def revoke_active_lease(self, revoked_by: str, reason: str) -> TransitionResult | None:
        """Revoke the currently active lease."""
        with self._lock:
            if not self.has_active_lease:
                return None

            assert self._active_lease is not None
            result = self._active_lease.revoke(revoked_by, reason)
            return result

    def on_global_halt(self, halt_id: str) -> None:
        """
        Handle global halt signal.

        INV-HALT-OVERRIDES-LEASE: Halt always wins, <50ms.
        """
        start = time.perf_counter_ns()

        if self._active_lease and self._active_lease.is_active:
            self._active_lease.halt(
                trigger=f"GLOBAL_HALT:{halt_id}",
                bound_exceeded="global_halt",
                value=0,
            )

        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000

        # INV-HALT-1: Must complete in <50ms
        assert elapsed_ms < 50, f"Lease halt took {elapsed_ms:.2f}ms, exceeds 50ms limit"

    def reset(self) -> None:
        """Reset manager state (for testing)."""
        self._active_lease = None


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def create_lease_from_cartridge(
    cartridge_ref: str,
    cartridge_hash: str,
    created_by: str,
    starts_at: datetime,
    duration_days: int,
    bounds: dict,
) -> Lease:
    """
    Create a new Lease instance from cartridge reference.

    This is a helper factory for common lease creation pattern.
    """
    from .lease_types import (
        LeaseBounds,
        LeaseDuration,
        LeaseIdentity,
        LeaseSubject,
    )

    expires_at = starts_at + timedelta(days=duration_days)

    return Lease(
        identity=LeaseIdentity(
            created_at=datetime.now(UTC),
            created_by=created_by,
        ),
        subject=LeaseSubject(
            strategy_ref=cartridge_ref,
            strategy_hash=cartridge_hash,
        ),
        duration=LeaseDuration(
            starts_at=starts_at,
            expires_at=expires_at,
            duration_days=duration_days,
        ),
        bounds=LeaseBounds(**bounds),
    )
