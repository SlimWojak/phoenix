"""
Insertion Protocol — 8-Step Cartridge+Lease Activation
=======================================================

Sprint: S47 LEASE_IMPLEMENTATION / S50.T1 CABINET_REFACTOR
Design Spec: docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md (v1.1)

8-Step Insertion Protocol:
  1. Load cartridge YAML
  2. Schema validation (Pydantic) — includes cabinet completeness
  3. Hash verification (if provided)
  4. Linter/guard dog scan — cabinet validation (all 5 drawers, canonical names)
  5. Slot into registry (conflicts = rejection)
  6. Create lease
  7. Lease activation ceremony
  8. Emit CARTRIDGE_INSERTION_BEAD + LEASE_ACTIVATION_BEAD

S50.T1: Drawer merge replaced with cabinet validation.
  Each cartridge carries a self-contained 5-drawer cabinet.
  No merge against methodology base. Pydantic enforces completeness.

Invariants:
  INV-LEASE-CEILING: Lease bounds can only tighten cartridge defaults
  INV-NO-SESSION-OVERLAP: One lease per session (v1.0: single lease)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .cartridge import (
    CartridgeConflictError,
    CartridgeLinter,
    CartridgeLoader,
    CartridgeRegistry,
    CartridgeValidationError,
)
from .lease import (
    LeaseManager,
    create_lease_from_cartridge,
)
from .lease_types import (
    AllowedMode,
    CartridgeManifest,
    LeaseBounds,
    TransitionResult,
)

# =============================================================================
# INSERTION RESULT
# =============================================================================


@dataclass
class InsertionResult:
    """Result of the 8-step insertion protocol."""

    success: bool
    cartridge_ref: str | None
    lease_id: str | None
    step_reached: int
    error: str | None
    lint_result: dict[str, Any] | None

    @classmethod
    def failure(cls, step: int, error: str) -> InsertionResult:
        """Create failure result."""
        return cls(
            success=False,
            cartridge_ref=None,
            lease_id=None,
            step_reached=step,
            error=error,
            lint_result=None,
        )

    @classmethod
    def success_result(
        cls,
        cartridge_ref: str,
        lease_id: str,
        lint_result: dict[str, Any],
    ) -> InsertionResult:
        """Create success result."""
        return cls(
            success=True,
            cartridge_ref=cartridge_ref,
            lease_id=lease_id,
            step_reached=8,
            error=None,
            lint_result=lint_result,
        )


# =============================================================================
# BOUNDS VALIDATION (INV-LEASE-CEILING)
# =============================================================================


def validate_bounds_ceiling(
    cartridge: CartridgeManifest,
    lease_bounds: LeaseBounds,
) -> list[str]:
    """
    Validate INV-LEASE-CEILING: Lease bounds can only tighten, never loosen.

    Returns:
        List of violations (empty if valid)
    """
    violations: list[str] = []
    defaults = cartridge.risk_defaults

    # Position size cap must be <= cartridge default
    if lease_bounds.position_size_cap is not None:
        if lease_bounds.position_size_cap > defaults.per_trade_pct:
            violations.append(
                f"position_size_cap ({lease_bounds.position_size_cap}%) > "
                f"cartridge per_trade_pct ({defaults.per_trade_pct}%)"
            )

    # Allowed pairs must be subset of cartridge pairs
    if lease_bounds.allowed_pairs_mode == AllowedMode.SUBSET:
        cartridge_pairs = set(cartridge.scope.pairs)
        lease_pairs = set(lease_bounds.allowed_pairs)
        extra = lease_pairs - cartridge_pairs
        if extra:
            violations.append(f"allowed_pairs contains pairs not in cartridge: {extra}")

    # Allowed sessions must be subset of cartridge sessions (if defined)
    if lease_bounds.allowed_sessions_mode == AllowedMode.SUBSET and cartridge.scope.session_windows:
        cartridge_sessions = {sw.name for sw in cartridge.scope.session_windows}
        lease_sessions = set(lease_bounds.allowed_sessions)
        extra = lease_sessions - cartridge_sessions
        if extra:
            violations.append(f"allowed_sessions contains sessions not in cartridge: {extra}")

    return violations


# =============================================================================
# INSERTION PROTOCOL
# =============================================================================


class InsertionProtocol:
    """
    8-Step Cartridge+Lease Activation Protocol.

    Coordinates:
      - CartridgeLoader (validation)
      - CartridgeLinter (guard dog)
      - CartridgeRegistry (slot management)
      - LeaseManager (activation)
    """

    def __init__(
        self,
        loader: CartridgeLoader | None = None,
        linter: CartridgeLinter | None = None,
        registry: CartridgeRegistry | None = None,
        lease_manager: LeaseManager | None = None,
    ):
        self._loader = loader or CartridgeLoader()
        self._linter = linter or CartridgeLinter()
        self._registry = registry or CartridgeRegistry()
        self._lease_manager = lease_manager or LeaseManager()

    @property
    def registry(self) -> CartridgeRegistry:
        """Get cartridge registry."""
        return self._registry

    @property
    def lease_manager(self) -> LeaseManager:
        """Get lease manager."""
        return self._lease_manager

    def insert_from_file(
        self,
        cartridge_path: Path | str,
        created_by: str,
        duration_days: int,
        bounds: dict[str, Any],
        starts_at: datetime | None = None,
    ) -> InsertionResult:
        """
        Execute full 8-step insertion protocol from YAML file.

        Args:
            cartridge_path: Path to cartridge YAML
            created_by: Human creating the lease
            duration_days: Lease duration (1-30 days)
            bounds: Lease bounds dictionary
            starts_at: When lease starts (default: now)

        Returns:
            InsertionResult with success/failure details
        """
        # Step 1: Load cartridge YAML
        try:
            manifest = self._loader.load_from_file(cartridge_path)
        except CartridgeValidationError as e:
            return InsertionResult.failure(1, f"Load failed: {e}")

        return self._complete_insertion(
            manifest=manifest,
            created_by=created_by,
            duration_days=duration_days,
            bounds=bounds,
            starts_at=starts_at,
        )

    def insert_from_dict(
        self,
        cartridge_data: dict[str, Any],
        created_by: str,
        duration_days: int,
        bounds: dict[str, Any],
        starts_at: datetime | None = None,
    ) -> InsertionResult:
        """
        Execute full 8-step insertion protocol from dictionary.

        Useful for programmatic insertion or testing.
        """
        # Step 1: Parse (no file to load)
        # Step 2: Schema validation
        try:
            manifest = self._loader.load_from_dict(cartridge_data)
        except CartridgeValidationError as e:
            return InsertionResult.failure(2, f"Validation failed: {e}")

        return self._complete_insertion(
            manifest=manifest,
            created_by=created_by,
            duration_days=duration_days,
            bounds=bounds,
            starts_at=starts_at,
            step_offset=2,
        )

    def insert_manifest(
        self,
        manifest: CartridgeManifest,
        created_by: str,
        duration_days: int,
        bounds: dict[str, Any],
        starts_at: datetime | None = None,
    ) -> InsertionResult:
        """
        Execute insertion protocol with pre-validated manifest.

        Skips steps 1-3 (load, validation, hash verification).
        """
        return self._complete_insertion(
            manifest=manifest,
            created_by=created_by,
            duration_days=duration_days,
            bounds=bounds,
            starts_at=starts_at,
            step_offset=3,
        )

    def _complete_insertion(
        self,
        manifest: CartridgeManifest,
        created_by: str,
        duration_days: int,
        bounds: dict[str, Any],
        starts_at: datetime | None,
        step_offset: int = 1,
    ) -> InsertionResult:
        """Complete steps 4-8 of insertion protocol."""

        # Step 4: Linter/guard dog scan
        lint_result = self._linter.lint(manifest)
        if not lint_result["passed"]:
            errors = "; ".join(lint_result["errors"])
            return InsertionResult.failure(4, f"Lint failed: {errors}")

        # Step 5: Slot into registry
        try:
            cartridge_ref = self._registry.slot(manifest, lint_result)
        except CartridgeConflictError as e:
            return InsertionResult.failure(5, f"Slot failed: {e}")

        # Step 6: Create lease
        starts_at = starts_at or datetime.now(UTC)

        # Parse bounds into LeaseBounds for validation
        try:
            lease_bounds = LeaseBounds(**bounds)
        except Exception as e:
            # Rollback slot on failure
            self._registry.remove(cartridge_ref, "SYSTEM", f"Lease bounds invalid: {e}")
            return InsertionResult.failure(6, f"Invalid lease bounds: {e}")

        # Validate INV-LEASE-CEILING
        ceiling_violations = validate_bounds_ceiling(manifest, lease_bounds)
        if ceiling_violations:
            # Rollback slot on failure
            self._registry.remove(
                cartridge_ref, "SYSTEM", f"INV-LEASE-CEILING violation: {ceiling_violations}"
            )
            return InsertionResult.failure(6, f"INV-LEASE-CEILING: {ceiling_violations}")

        lease = create_lease_from_cartridge(
            cartridge_ref=cartridge_ref,
            cartridge_hash=manifest.identity.methodology_hash or "",
            created_by=created_by,
            starts_at=starts_at,
            duration_days=duration_days,
            bounds=bounds,
        )

        # Step 7: Lease activation ceremony
        state_machine, result = self._lease_manager.activate_lease(lease)

        if result != TransitionResult.SUCCESS:
            # Rollback slot on failure
            self._registry.remove(cartridge_ref, "SYSTEM", f"Lease activation failed: {result}")
            return InsertionResult.failure(7, f"Activation failed: {result.value}")

        # Step 8: Complete — beads emitted by registry and lease manager
        return InsertionResult.success_result(
            cartridge_ref=cartridge_ref,
            lease_id=lease.identity.lease_id,
            lint_result=lint_result,
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def quick_insert(
    cartridge_data: dict[str, Any],
    bounds: dict[str, Any],
    created_by: str = "SYSTEM",
    duration_days: int = 7,
) -> InsertionResult:
    """
    Quick insertion for testing.

    Uses fresh instances (no singleton state).
    """
    protocol = InsertionProtocol(
        loader=CartridgeLoader(),
        linter=CartridgeLinter(),
        registry=CartridgeRegistry(),
        lease_manager=LeaseManager(),
    )

    return protocol.insert_from_dict(
        cartridge_data=cartridge_data,
        created_by=created_by,
        duration_days=duration_days,
        bounds=bounds,
    )
