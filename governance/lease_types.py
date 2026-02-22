"""
Lease Types — Pydantic Models for Cartridge + Lease Schemas
===========================================================

Sprint: S47 LEASE_IMPLEMENTATION / S50.T1 CABINET_REFACTOR
Design Spec: docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md (v1.1)

Invariants:
  INV-LEASE-CEILING: Lease defines HARD CEILING; Cartridge defines LOWER FLOOR
  INV-NO-SESSION-OVERLAP: Session windows cannot overlap unless explicitly declared
  INV-STATE-LOCK: State transition guard prevents race conditions
  INV-EXPIRY-BUFFER: Software halt governance_buffer_seconds BEFORE legal expiry
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# =============================================================================
# ENUMS
# =============================================================================


class LeaseState(str, Enum):
    """
    Lease state machine states.

    Transitions:
      DRAFT → ACTIVE (activation ceremony)
      ACTIVE → EXPIRED (automatic, governance_buffer before legal expiry)
      ACTIVE → REVOKED (human revocation)
      ACTIVE → HALTED (bounds exceeded OR global halt)
      HALTED → REVOKED (human must revoke; no resurrection)

    Terminal: EXPIRED, REVOKED
    """

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    HALTED = "HALTED"


class RenewalType(str, Enum):
    """Lease renewal type — PERISH only (INV: no auto-renew)."""

    PERISH = "PERISH"


class ExpiryBehavior(str, Enum):
    """What happens to open positions on lease expiry."""

    MARKET_CLOSE = "MARKET_CLOSE"
    FREEZE_AND_WAIT = "FREEZE_AND_WAIT"


class AllowedMode(str, Enum):
    """Mode for allowed_pairs/allowed_sessions."""

    ALL = "ALL"
    SUBSET = "SUBSET"


class RegimeAffinity(str, Enum):
    """Expected market regime for valid calibration."""

    VOLATILITY_HIGH = "VOLATILITY_HIGH"
    VOLATILITY_LOW = "VOLATILITY_LOW"
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    ANY = "ANY"


class ICTPrimitive(str, Enum):
    """Declared ICT primitives for guard dog verification."""

    FVG = "FVG"
    SWEEP = "SWEEP"
    RE_ACCEPTANCE = "RE_ACCEPTANCE"
    MSS = "MSS"
    PD_ARRAY = "PD_ARRAY"
    DISPLACEMENT = "DISPLACEMENT"
    KZ_TIMING = "KZ_TIMING"


class TransitionResult(str, Enum):
    """Result of a state transition attempt."""

    SUCCESS = "SUCCESS"
    REJECTED_HASH_MISMATCH = "REJECTED_HASH_MISMATCH"
    REJECTED_INVALID_TRANSITION = "REJECTED_INVALID_TRANSITION"
    REJECTED_LEASE_NOT_ACTIVE = "REJECTED_LEASE_NOT_ACTIVE"


# =============================================================================
# CARTRIDGE SCHEMA — Section 2 of Design Spec
# =============================================================================


class SessionWindow(BaseModel):
    """
    Trading session window definition.

    INV-NO-SESSION-OVERLAP: Windows cannot overlap unless explicitly declared.
    """

    name: str = Field(..., description="Session name identifier")
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Start time HH:MM")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="End time HH:MM")
    timezone: str = Field(..., description="IANA timezone name")
    utc_offset_winter: str = Field(
        ..., pattern=r"^[+-]\d{2}:\d{2}$", description="UTC offset winter"
    )
    utc_offset_summer: str = Field(
        ..., pattern=r"^[+-]\d{2}:\d{2}$", description="UTC offset summer"
    )


class CartridgeIdentity(BaseModel):
    """Strategy identity block."""

    name: str = Field(
        ..., pattern=r"^[A-Z][A-Z0-9_]+$", description="Strategy name UPPER_SNAKE_CASE"
    )
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semver version")
    author: str = Field(..., description="Strategy author")
    description: str = Field(default="", max_length=500, description="Strategy description")
    created_at: datetime = Field(..., description="Creation timestamp ISO8601")
    methodology_hash: str | None = Field(default=None, description="SHA256 of normalized manifest")


class CartridgeScope(BaseModel):
    """Strategy scope — where and when it operates."""

    pairs: list[str] = Field(..., min_length=1, description="Trading pairs")
    session_windows: list[SessionWindow] = Field(
        default_factory=list, description="Session windows"
    )
    regime_affinity: RegimeAffinity = Field(
        default=RegimeAffinity.ANY, description="Expected regime"
    )


class CartridgeRiskDefaults(BaseModel):
    """
    Default risk parameters.

    INV-LEASE-CEILING: Lease can only tighten these, never loosen.
    """

    per_trade_pct: float = Field(..., ge=0.1, le=5.0, description="Risk per trade %")
    min_rr: float = Field(..., ge=1.0, description="Minimum risk:reward ratio")
    max_trades_per_session: int = Field(..., ge=1, description="Max trades per session")
    max_daily_trades: int | None = Field(default=None, description="Max trades per day")


class DrawerName(str, Enum):
    """Canonical 5-drawer names from Bead Field Spec."""

    HTF_BIAS = "HTF_BIAS"
    MARKET_STRUCTURE = "MARKET_STRUCTURE"
    PREMIUM_DISCOUNT = "PREMIUM_DISCOUNT"
    ENTRY_MODEL = "ENTRY_MODEL"
    CONFIRMATION = "CONFIRMATION"


REQUIRED_DRAWER_NAMES = frozenset(d.value for d in DrawerName)


class DrawerConfig(BaseModel):
    """Complete 5-drawer cabinet for a cartridge.

    Each drawer is a dict of gate configurations specific to the strategy.
    All 5 canonical drawers are REQUIRED and must be non-empty.
    Extra drawers are forbidden (extra='forbid').

    Drawers: HTF_BIAS, MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION
    See cso/knowledge/methodology_template.yaml for reference.
    """

    model_config = ConfigDict(extra="forbid")

    HTF_BIAS: dict[str, Any] = Field(..., description="HTF bias configuration")
    MARKET_STRUCTURE: dict[str, Any] = Field(..., description="Market structure configuration")
    PREMIUM_DISCOUNT: dict[str, Any] = Field(..., description="Premium/discount zone configuration")
    ENTRY_MODEL: dict[str, Any] = Field(..., description="Entry model configuration")
    CONFIRMATION: dict[str, Any] = Field(..., description="Confirmation/management configuration")

    @model_validator(mode="before")
    @classmethod
    def check_drawer_names(cls, data: Any) -> Any:
        """Reject old-style drawer names with a helpful error listing canonical names."""
        if not isinstance(data, dict):
            return data
        old_to_new = {
            "foundation": "HTF_BIAS",
            "context": "MARKET_STRUCTURE",
            "conditions": "PREMIUM_DISCOUNT",
            "entry": "ENTRY_MODEL",
            "management": "CONFIRMATION",
        }
        bad_keys = [k for k in data if k in old_to_new]
        if bad_keys:
            mapped = ", ".join(f"'{k}' → '{old_to_new[k]}'" for k in bad_keys)
            canonical = ", ".join(d.value for d in DrawerName)
            raise ValueError(
                f"Invalid drawer name(s): {mapped}. "
                f"Required drawers are: {canonical}. "
                f"See methodology_template.yaml for reference."
            )
        return data

    @model_validator(mode="after")
    def validate_non_empty_drawers(self) -> DrawerConfig:
        """Every drawer must be a non-empty dict."""
        for name in DrawerName:
            value = getattr(self, name.value)
            if not value:
                raise ValueError(f"Drawer '{name.value}' must be non-empty")
        return self


class CSOIntegration(BaseModel):
    """How strategy defines CSO evaluation (self-contained cabinet, not deltas)."""

    drawer_config: DrawerConfig = Field(..., description="Complete 5-drawer cabinet")
    gate_requirements: list[str] = Field(
        default_factory=list, description="Required gates for valid setup"
    )
    primitive_set: list[ICTPrimitive] = Field(
        default_factory=list, description="Declared ICT primitives"
    )


class ResearchHooks(BaseModel):
    """Hunt/CFP integration hooks."""

    hunt_grid_enabled: bool = Field(default=True, description="Enable Hunt grid for this strategy")
    cfp_lens_presets: list[str] = Field(default_factory=list, description="Pre-defined CFP queries")
    backtest_min_trades: int = Field(default=30, description="Minimum trades for valid backtest")
    calibration_threshold_pct: float = Field(
        default=5.0, description="Drift threshold for WARN (2x for BLOCK)"
    )


class NarratorOverrides(BaseModel):
    """Custom narrator templates."""

    templates: dict[str, str] = Field(
        default_factory=dict, description="Template name → template string"
    )


class Constitutional(BaseModel):
    """Required invariants (non-negotiable)."""

    invariants_required: list[str] = Field(
        ..., min_length=1, description="Invariants this strategy must comply with"
    )
    forbidden_patterns: list[str] = Field(
        default_factory=list, description="Patterns that would violate constitution"
    )
    guard_dog_scan: bool = Field(default=True, description="Enable guard dog scan")

    @field_validator("invariants_required")
    @classmethod
    def validate_invariants(cls, v: list[str]) -> list[str]:
        """Ensure minimum required invariants are present."""
        required = {"INV-NO-UNSOLICITED", "INV-HALT-1"}
        present = set(v)
        missing = required - present
        if missing:
            raise ValueError(f"Missing required invariants: {missing}")
        return v


class CartridgeManifest(BaseModel):
    """
    Complete cartridge manifest — the N64 game label.

    Design Principles:
      P1_DECLARATIVE: Strategy is data, not code
      P2_SELF_CONTAINED_CABINET: Each cartridge carries complete 5-drawer cabinet
      P3_INVARIANTS_REQUIRED: Must declare constitutional compliance
      P4_TIMEZONE_EXPLICIT: All times include TZ + UTC offset
      P5_SLOT_OR_PERISH: Conflicts = rejection, not silent merge
      P6_PRIMITIVE_DECLARED: Must declare which ICT primitives used
    """

    identity: CartridgeIdentity
    scope: CartridgeScope
    risk_defaults: CartridgeRiskDefaults
    cso_integration: CSOIntegration
    research_hooks: ResearchHooks = Field(default_factory=ResearchHooks)
    narrator_overrides: NarratorOverrides = Field(default_factory=NarratorOverrides)
    constitutional: Constitutional

    def compute_methodology_hash(self) -> str:
        """
        Compute SHA256 hash of normalized manifest.

        Normalization:
          1. Sort all keys alphabetically
          2. Remove whitespace
          3. UTF-8 encode
          4. SHA256 hash
        """
        # Exclude the hash itself from computation
        data = self.model_dump(exclude={"identity": {"methodology_hash"}}, mode="json")
        normalized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# =============================================================================
# LEASE SCHEMA — Section 3 of Design Spec
# =============================================================================


class LeaseIdentity(BaseModel):
    """Lease identification."""

    lease_id: str = Field(
        default_factory=lambda: f"lease_{uuid4().hex[:12]}", description="Unique lease ID"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="Human who created the lease")


class LeaseSubject(BaseModel):
    """What strategy is being leased."""

    strategy_ref: str = Field(
        ...,
        pattern=r"^[A-Z][A-Z0-9_]+_v\d+\.\d+\.\d+$",
        description="Strategy reference NAME_vX.Y.Z",
    )
    strategy_hash: str = Field(..., description="SHA256 of manifest at lease creation")


class LeaseDuration(BaseModel):
    """When is this lease valid."""

    starts_at: datetime = Field(..., description="Lease start time")
    expires_at: datetime = Field(..., description="Lease expiry time")
    duration_days: int = Field(..., ge=1, le=30, description="Duration in days (max 30)")
    renewal_type: Literal[RenewalType.PERISH] = Field(
        default=RenewalType.PERISH, description="Always PERISH — no auto-renew"
    )


class LeaseBounds(BaseModel):
    """
    Risk constraints — INV-LEASE-CEILING: can only tighten strategy defaults.

    Design Decision D8: OR logic for bounds (any breach = halt)
    """

    max_drawdown_pct: float = Field(..., description="Auto-halt if exceeded")
    max_consecutive_losses: int = Field(..., description="Auto-halt if exceeded")
    allowed_pairs: list[str] = Field(..., description="Subset of strategy pairs")
    allowed_pairs_mode: AllowedMode = Field(..., description="ALL or SUBSET")
    allowed_sessions: list[str] = Field(
        default_factory=list, description="Subset of strategy sessions"
    )
    allowed_sessions_mode: AllowedMode = Field(default=AllowedMode.ALL, description="ALL or SUBSET")
    position_size_cap: float | None = Field(
        default=None, description="Must be <= strategy.per_trade_pct"
    )
    daily_loss_limit_pct: float | None = Field(default=None, description="Daily loss limit %")
    priority_weight: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Margin contention priority"
    )


class LeaseGovernance(BaseModel):
    """Ceremony and attestation requirements."""

    weekly_review_required: bool = Field(
        default=True, description="Weekly review required (immutable)"
    )
    attestation_required: bool = Field(default=True, description="Attestation required for renewal")
    last_review_at: datetime | None = Field(default=None, description="Last review timestamp")
    last_attestation_bead: str | None = Field(default=None, description="Last attestation bead ID")
    next_review_due: datetime | None = Field(
        default=None, description="Calculated from last attestation"
    )
    reviewer: str | None = Field(default=None, description="Designated reviewer(s)")
    state_lock_hash: str | None = Field(
        default=None, description="Hash of prior state for race protection"
    )


class HaltIntegration(BaseModel):
    """
    How lease interacts with halt system.

    INV-HALT-OVERRIDES-LEASE: Halt always wins (<50ms)
    """

    auto_halt_on_drawdown: bool = Field(default=True, description="Auto-halt on drawdown breach")
    auto_halt_on_streak: bool = Field(default=True, description="Auto-halt on losing streak breach")
    halt_overrides_lease: Literal[True] = Field(
        default=True, description="INV-HALT-OVERRIDES-LEASE — immutable"
    )
    halt_latency_ms: int = Field(default=50, le=50, description="Max halt latency (INV-HALT-1)")
    governance_buffer_seconds: int = Field(
        default=60, description="Software halt N seconds BEFORE legal expiry (INV-EXPIRY-BUFFER)"
    )
    expiry_behavior: ExpiryBehavior = Field(
        default=ExpiryBehavior.MARKET_CLOSE, description="What happens to open positions on expiry"
    )


class LeaseStatus(BaseModel):
    """Current lease state and timestamps."""

    current: LeaseState = Field(default=LeaseState.DRAFT, description="Current state")
    activated_at: datetime | None = Field(default=None, description="When lease became ACTIVE")
    revoked_at: datetime | None = Field(default=None, description="When lease was revoked")
    revocation_reason: str | None = Field(default=None, description="Reason for revocation")
    halted_at: datetime | None = Field(default=None, description="When lease was halted")
    halt_trigger: str | None = Field(default=None, description="What triggered the halt")


class Lease(BaseModel):
    """
    Complete lease instance — governance wrapper.

    Design Principles:
      P1_PERISH_BY_DEFAULT: No auto-renew ever
      P2_HALT_OVERRIDES: Halt wins over lease (<50ms)
      P3_BOUNDS_ONLY_TIGHTEN: Can constrain, never loosen
      P4_CEREMONY_REQUIRED: Weekly review = attestation bead
      P5_FORENSIC_TRAIL: All lease actions = beads
      P6_STATE_LOCKED: All transitions hash-verified
    """

    identity: LeaseIdentity
    subject: LeaseSubject
    duration: LeaseDuration
    bounds: LeaseBounds
    governance: LeaseGovernance = Field(default_factory=LeaseGovernance)
    halt_integration: HaltIntegration = Field(default_factory=HaltIntegration)
    status: LeaseStatus = Field(default_factory=LeaseStatus)

    def compute_state_hash(self) -> str:
        """
        Compute hash of current state for INV-STATE-LOCK.

        Used to prevent race conditions in state transitions.
        """
        state_data = {
            "lease_id": self.identity.lease_id,
            "current_state": self.status.current.value,
            "activated_at": self.status.activated_at.isoformat()
            if self.status.activated_at
            else None,
            "revoked_at": self.status.revoked_at.isoformat() if self.status.revoked_at else None,
            "halted_at": self.status.halted_at.isoformat() if self.status.halted_at else None,
        }
        normalized = json.dumps(state_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    @model_validator(mode="after")
    def validate_bounds_ceiling(self) -> Lease:
        """
        Validate INV-LEASE-CEILING: bounds can only tighten, never loosen.

        Note: Full validation requires cartridge context, done at insertion time.
        """
        # Basic validation: position_size_cap should be reasonable
        if self.bounds.position_size_cap is not None and self.bounds.position_size_cap <= 0:
            raise ValueError("position_size_cap must be positive")
        return self


# =============================================================================
# BEAD TYPES — Section 8 of Design Spec
# =============================================================================


class CartridgeInsertionBead(BaseModel):
    """Bead emitted when cartridge is slotted."""

    bead_type: Literal["CARTRIDGE_INSERTION_BEAD"] = "CARTRIDGE_INSERTION_BEAD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cartridge_ref: str
    methodology_hash: str
    linter_result: dict[str, Any] = Field(default_factory=dict)


class CartridgeRemovalBead(BaseModel):
    """Bead emitted when cartridge is removed."""

    bead_type: Literal["CARTRIDGE_REMOVAL_BEAD"] = "CARTRIDGE_REMOVAL_BEAD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cartridge_ref: str
    removed_by: str
    reason: str


class CalibrationBead(BaseModel):
    """
    Bead emitted after auto-shadow calibration.

    INV-BEAD-COMPLETENESS: Must link to lease_id immutably.
    """

    bead_type: Literal["CALIBRATION_BEAD"] = "CALIBRATION_BEAD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cartridge_ref: str
    lease_id: str
    drift_pct: float
    verdict: Literal["PASS", "WARN", "BLOCK"]


class LeaseActivationBead(BaseModel):
    """Bead emitted when lease becomes ACTIVE."""

    bead_type: Literal["LEASE_ACTIVATION_BEAD"] = "LEASE_ACTIVATION_BEAD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lease_id: str
    strategy_ref: str
    bounds_snapshot: dict[str, Any]


class LeaseExpiryBead(BaseModel):
    """Bead emitted when lease expires (automatic)."""

    bead_type: Literal["LEASE_EXPIRY_BEAD"] = "LEASE_EXPIRY_BEAD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lease_id: str
    final_stats: dict[str, Any] = Field(default_factory=dict)


class LeaseRevocationBead(BaseModel):
    """Bead emitted when human revokes lease."""

    bead_type: Literal["LEASE_REVOCATION_BEAD"] = "LEASE_REVOCATION_BEAD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lease_id: str
    revoked_by: str
    reason: str


class LeaseHaltBead(BaseModel):
    """Bead emitted when lease auto-halts from bounds breach."""

    bead_type: Literal["LEASE_HALT_BEAD"] = "LEASE_HALT_BEAD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lease_id: str
    trigger: str
    bound_exceeded: str
    value: float | int


class AttestationBead(BaseModel):
    """Bead emitted at weekly ceremony."""

    bead_type: Literal["ATTESTATION_BEAD"] = "ATTESTATION_BEAD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lease_id: str
    decision: Literal["RENEW", "MODIFY", "REVOKE"]
    new_lease_id: str | None = None


class StateLockBead(BaseModel):
    """
    Bead emitted on any state transition attempt.

    INV-STATE-LOCK: Race protection via hash verification.
    """

    bead_type: Literal["STATE_LOCK_BEAD"] = "STATE_LOCK_BEAD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lease_id: str
    prior_state: LeaseState
    prior_state_hash: str
    requested_transition: str
    transition_result: TransitionResult


class EmergencyEjectBead(BaseModel):
    """Bead emitted when G uses sovereign override."""

    bead_type: Literal["EMERGENCY_EJECT_BEAD"] = "EMERGENCY_EJECT_BEAD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cartridge_ref: str
    ejected_by: str
    reason: str


# =============================================================================
# TYPE ALIASES
# =============================================================================

BeadType = (
    CartridgeInsertionBead
    | CartridgeRemovalBead
    | CalibrationBead
    | LeaseActivationBead
    | LeaseExpiryBead
    | LeaseRevocationBead
    | LeaseHaltBead
    | AttestationBead
    | StateLockBead
    | EmergencyEjectBead
)
