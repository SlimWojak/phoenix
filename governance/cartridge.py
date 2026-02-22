"""
Cartridge Loader — YAML Schema Validation
==========================================

Sprint: S47 LEASE_IMPLEMENTATION / S50.T1 CABINET_REFACTOR
Design Spec: docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md (v1.1)

Design Principles:
  P1_DECLARATIVE: Strategy is data, not code
  P2_SELF_CONTAINED_CABINET: Each cartridge carries complete 5-drawer cabinet
  P3_INVARIANTS_REQUIRED: Must declare constitutional compliance
  P4_TIMEZONE_EXPLICIT: All times include TZ + UTC offset
  P5_SLOT_OR_PERISH: Conflicts = rejection, not silent merge
  P6_PRIMITIVE_DECLARED: Must declare which ICT primitives used
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .lease_types import (
    CartridgeIdentity,
    CartridgeInsertionBead,
    CartridgeManifest,
    CartridgeRemovalBead,
    CartridgeRiskDefaults,
    CartridgeScope,
    Constitutional,
    CSOIntegration,
    DrawerConfig,
    DrawerName,
)

# =============================================================================
# VALIDATION ERRORS
# =============================================================================


class CartridgeValidationError(Exception):
    """Base error for cartridge validation failures."""

    pass


class CartridgeSchemaError(CartridgeValidationError):
    """Schema validation failed — missing required fields or invalid types."""

    def __init__(self, errors: list[dict[str, Any]]):
        self.errors = errors
        msg = "; ".join(f"{e.get('loc', '?')}: {e.get('msg', '?')}" for e in errors)
        super().__init__(f"Schema validation failed: {msg}")


class CartridgeInvariantError(CartridgeValidationError):
    """Required invariant missing from cartridge declaration."""

    def __init__(self, missing: set[str]):
        self.missing = missing
        super().__init__(f"Missing required invariants: {sorted(missing)}")


class CartridgeHashMismatchError(CartridgeValidationError):
    """Methodology hash doesn't match computed hash."""

    def __init__(self, declared: str, computed: str):
        self.declared = declared
        self.computed = computed
        super().__init__(f"Hash mismatch: declared={declared[:16]}..., computed={computed[:16]}...")


class CartridgeConflictError(CartridgeValidationError):
    """
    Cartridge conflicts with existing slot.

    P5_SLOT_OR_PERISH: Conflicts = rejection, not silent merge.
    """

    def __init__(self, conflict_type: str, details: str):
        self.conflict_type = conflict_type
        self.details = details
        super().__init__(f"Cartridge conflict ({conflict_type}): {details}")


# =============================================================================
# CARTRIDGE LOADER
# =============================================================================


class CartridgeLoader:
    """
    Loads and validates cartridge manifests from YAML files.

    Validation pipeline:
      1. Parse YAML
      2. Validate against Pydantic schema
      3. Verify required invariants
      4. Compute and verify methodology hash
      5. Return validated CartridgeManifest
    """

    # Required invariants for ANY cartridge
    REQUIRED_INVARIANTS = frozenset({"INV-NO-UNSOLICITED", "INV-HALT-1"})

    def load_from_file(self, path: Path | str) -> CartridgeManifest:
        """
        Load cartridge from YAML file.

        Args:
            path: Path to cartridge YAML file

        Returns:
            Validated CartridgeManifest

        Raises:
            CartridgeValidationError: If validation fails
        """
        path = Path(path)

        if not path.exists():
            raise CartridgeValidationError(f"Cartridge file not found: {path}")

        with open(path) as f:
            raw = yaml.safe_load(f)

        return self.validate(raw)

    def load_from_dict(self, data: dict[str, Any]) -> CartridgeManifest:
        """
        Load cartridge from dictionary.

        Useful for programmatic cartridge creation or testing.
        """
        return self.validate(data)

    def validate(self, raw: dict[str, Any]) -> CartridgeManifest:
        """
        Validate raw dictionary against cartridge schema.

        Pipeline:
          1. Pydantic schema validation
          2. Required invariants check
          3. Hash verification (if provided)
        """
        # Step 1: Pydantic validation
        try:
            manifest = CartridgeManifest(**raw)
        except ValidationError as e:
            raise CartridgeSchemaError(e.errors()) from e

        # Step 2: Required invariants (redundant with model but explicit)
        declared = set(manifest.constitutional.invariants_required)
        missing = self.REQUIRED_INVARIANTS - declared
        if missing:
            raise CartridgeInvariantError(missing)

        # Step 3: Hash verification (if hash was provided)
        if manifest.identity.methodology_hash is not None:
            computed = manifest.compute_methodology_hash()
            if manifest.identity.methodology_hash != computed:
                raise CartridgeHashMismatchError(
                    manifest.identity.methodology_hash,
                    computed,
                )
        else:
            # Auto-compute hash if not provided
            manifest.identity.methodology_hash = manifest.compute_methodology_hash()

        return manifest

    def compute_hash(self, manifest: CartridgeManifest) -> str:
        """Compute methodology hash for a manifest."""
        return manifest.compute_methodology_hash()


# =============================================================================
# CARTRIDGE REGISTRY — Slot Management
# =============================================================================


class CartridgeRegistry:
    """
    Registry of slotted cartridges.

    v1.0: Single active cartridge only.
    Design: P5_SLOT_OR_PERISH — conflicts = rejection.
    """

    def __init__(self):
        self._slotted: dict[str, CartridgeManifest] = {}
        self._active: CartridgeManifest | None = None
        self._beads: list[CartridgeInsertionBead | CartridgeRemovalBead] = []

    @property
    def active_cartridge(self) -> CartridgeManifest | None:
        """Get currently active cartridge (or None)."""
        return self._active

    @property
    def active_ref(self) -> str | None:
        """Get reference string for active cartridge."""
        if self._active is None:
            return None
        ident = self._active.identity
        return f"{ident.name}_v{ident.version}"

    def slot(self, manifest: CartridgeManifest, linter_result: dict[str, Any] | None = None) -> str:
        """
        Slot a cartridge into the registry.

        v1.0: Only one active cartridge allowed.

        Returns:
            Cartridge reference string

        Raises:
            CartridgeConflictError: If another cartridge is already slotted
        """
        ref = f"{manifest.identity.name}_v{manifest.identity.version}"

        # v1.0: Only one active cartridge
        if self._active is not None:
            active_ref = f"{self._active.identity.name}_v{self._active.identity.version}"
            if active_ref != ref:
                raise CartridgeConflictError(
                    "SINGLE_CARTRIDGE_LIMIT",
                    f"Cannot slot {ref}: {active_ref} already active (v1.0 limit)",
                )

        # Slot the cartridge
        self._slotted[ref] = manifest
        self._active = manifest

        # Emit insertion bead
        bead = CartridgeInsertionBead(
            cartridge_ref=ref,
            methodology_hash=manifest.identity.methodology_hash or "",
            linter_result=linter_result or {},
        )
        self._beads.append(bead)

        return ref

    def remove(self, ref: str, removed_by: str, reason: str) -> bool:
        """
        Remove a cartridge from the registry.

        Returns:
            True if removed, False if not found
        """
        if ref not in self._slotted:
            return False

        manifest = self._slotted.pop(ref)

        # Clear active if it was the removed one
        if self._active is manifest:
            self._active = None

        # Emit removal bead
        bead = CartridgeRemovalBead(
            cartridge_ref=ref,
            removed_by=removed_by,
            reason=reason,
        )
        self._beads.append(bead)

        return True

    def get(self, ref: str) -> CartridgeManifest | None:
        """Get cartridge by reference string."""
        return self._slotted.get(ref)

    def get_beads(self) -> list[CartridgeInsertionBead | CartridgeRemovalBead]:
        """Get all emitted beads (for testing/audit)."""
        return self._beads.copy()


# =============================================================================
# LINTER — Guard Dog Scan
# =============================================================================


class CartridgeLinter:
    """
    Static analysis of cartridge manifests.

    Checks:
      - Cabinet completeness (all 5 drawers, canonical names, non-empty)
      - Cabinet content scan (forbidden patterns in drawer keys/values)
      - P6_PRIMITIVE_DECLARED: All used primitives declared
      - Constitutional completeness
      - Session window validity
      - Risk bounds sanity
    """

    FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
        re.compile(r"\b(best|worst|strongest|weakest)\b", re.IGNORECASE),
        re.compile(r"\b(recommend|should|must trade)\b", re.IGNORECASE),
        re.compile(r"\b(grade|score|rating)\b", re.IGNORECASE),
        re.compile(r"\bedge concentrates\b", re.IGNORECASE),
    ]

    def lint(self, manifest: CartridgeManifest) -> dict[str, Any]:
        """
        Run all lint checks on a manifest.

        Returns:
            Dictionary with lint results:
            {
                "passed": bool,
                "warnings": [...],
                "errors": [...],
            }
        """
        warnings: list[str] = []
        errors: list[str] = []

        # Cabinet validation — all 5 drawers present and non-empty
        cabinet = manifest.cso_integration.drawer_config
        for drawer_name in DrawerName:
            value = getattr(cabinet, drawer_name.value, None)
            if value is None:
                errors.append(f"Missing drawer: {drawer_name.value}")
            elif not value:
                errors.append(f"Empty drawer: {drawer_name.value}")

        # Cabinet content scan — forbidden patterns in drawer keys and values
        if manifest.constitutional.guard_dog_scan:
            errors.extend(self._scan_cabinet_content(cabinet))

        # Check primitive set
        if not manifest.cso_integration.primitive_set:
            warnings.append("No ICT primitives declared (P6_PRIMITIVE_DECLARED)")

        # Check session windows
        if not manifest.scope.session_windows:
            warnings.append("No session windows defined — will use all sessions")

        # Check risk bounds
        if manifest.risk_defaults.per_trade_pct > 3.0:
            warnings.append(
                f"High per_trade_pct: {manifest.risk_defaults.per_trade_pct}% (recommended ≤3%)"
            )

        if manifest.risk_defaults.min_rr < 1.5:
            warnings.append(f"Low min_rr: {manifest.risk_defaults.min_rr} (recommended ≥1.5)")

        # Check gate requirements
        if not manifest.cso_integration.gate_requirements:
            warnings.append(
                "No explicit gate requirements — cartridge does not filter which gates apply."
            )

        # Check forbidden patterns declaration
        if (
            manifest.constitutional.guard_dog_scan
            and not manifest.constitutional.forbidden_patterns
        ):
            warnings.append("Guard dog enabled but no forbidden patterns declared")

        return {
            "passed": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
        }

    def _scan_cabinet_content(
        self,
        cabinet: DrawerConfig,
    ) -> list[str]:
        """Scan all drawer keys and values for forbidden patterns."""
        hits: list[str] = []
        for drawer_name in DrawerName:
            drawer_dict = getattr(cabinet, drawer_name.value, {})
            if not isinstance(drawer_dict, dict):
                continue
            serialized = json.dumps(drawer_dict, default=str)
            for pattern in self.FORBIDDEN_PATTERNS:
                match = pattern.search(serialized)
                if match:
                    hits.append(
                        f"Forbidden pattern '{match.group()}' found in "
                        f"drawer {drawer_name.value}"
                    )
        return hits


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def create_minimal_cartridge(
    name: str,
    version: str,
    author: str,
    pairs: list[str],
    per_trade_pct: float = 1.0,
    min_rr: float = 2.0,
    max_trades_per_session: int = 3,
    drawer_config: dict[str, Any] | None = None,
) -> CartridgeManifest:
    """
    Create a minimal valid cartridge for testing.

    All required fields populated with sensible defaults.
    Provides a stub cabinet if drawer_config is not supplied.
    """
    from datetime import UTC, datetime

    if drawer_config is None:
        drawer_config = {
            "HTF_BIAS": {"enabled": True},
            "MARKET_STRUCTURE": {"enabled": True},
            "PREMIUM_DISCOUNT": {"enabled": True},
            "ENTRY_MODEL": {"enabled": True},
            "CONFIRMATION": {"enabled": True},
        }

    manifest = CartridgeManifest(
        identity=CartridgeIdentity(
            name=name,
            version=version,
            author=author,
            created_at=datetime.now(UTC),
        ),
        scope=CartridgeScope(
            pairs=pairs,
        ),
        risk_defaults=CartridgeRiskDefaults(
            per_trade_pct=per_trade_pct,
            min_rr=min_rr,
            max_trades_per_session=max_trades_per_session,
        ),
        cso_integration=CSOIntegration(
            drawer_config=DrawerConfig(**drawer_config),
        ),
        constitutional=Constitutional(
            invariants_required=["INV-NO-UNSOLICITED", "INV-HALT-1"],
        ),
    )

    # Compute hash
    manifest.identity.methodology_hash = manifest.compute_methodology_hash()

    return manifest
