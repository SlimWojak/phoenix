"""
Orientation Validator — Corruption Detection + Cross-Check
===========================================================

S34: D3 ORIENTATION_BEAD_CHECKSUM

Validates orientation beads and detects corruption.

INVARIANTS:
- INV-D3-CROSS-CHECK-1: Every field verifiable against source
- INV-D3-CORRUPTION-1: Corruption → STATE_CONFLICT

THE KILL TEST: 5 corruption variants must all trigger STATE_CONFLICT:
1. Hash wrong
2. Fields invalid (enum out of range)
3. Stale timestamp (>1 hour old)
4. Mode mismatch (bead says LIVE, system says PAPER)
5. Position count mismatch
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from .generator import (
    ExecutionPhase,
    HaltManagerProvider,
    HeartbeatProvider,
    HeartbeatStatusEnum,
    ModeEnum,
    OrientationBead,
    PositionTrackerProvider,
)

# =============================================================================
# CONFLICT CODES
# =============================================================================


class ConflictCode(str, Enum):
    """STATE_CONFLICT codes for corruption detection."""

    # Hash corruption
    STATE_CONFLICT_HASH = "STATE_CONFLICT_HASH"

    # Enum corruption
    STATE_CONFLICT_INVALID_ENUM = "STATE_CONFLICT_INVALID_ENUM"

    # Timestamp corruption
    STATE_CONFLICT_STALE = "STATE_CONFLICT_STALE"

    # Mode mismatch
    STATE_CONFLICT_MODE = "STATE_CONFLICT_MODE"

    # Position count mismatch
    STATE_CONFLICT_POSITIONS = "STATE_CONFLICT_POSITIONS"

    # Kill flags mismatch
    STATE_CONFLICT_KILL_FLAGS = "STATE_CONFLICT_KILL_FLAGS"

    # Heartbeat mismatch
    STATE_CONFLICT_HEARTBEAT = "STATE_CONFLICT_HEARTBEAT"

    # General validation failure
    STATE_CONFLICT_VALIDATION = "STATE_CONFLICT_VALIDATION"


class Severity(str, Enum):
    """Conflict severity."""

    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# =============================================================================
# VALIDATION RESULT
# =============================================================================


@dataclass
class Conflict:
    """Single validation conflict."""

    code: ConflictCode
    severity: Severity
    message: str
    expected: Any = None
    actual: Any = None


@dataclass
class ValidationResult:
    """
    Complete validation result.

    INV-D3-CORRUPTION-1: Any conflict = STATE_CONFLICT
    """

    valid: bool
    conflicts: list[Conflict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def state_conflict(self) -> bool:
        """Check if any critical conflicts exist."""
        return any(c.severity == Severity.CRITICAL for c in self.conflicts)

    @property
    def conflict_codes(self) -> list[ConflictCode]:
        """Get list of conflict codes."""
        return [c.code for c in self.conflicts]

    def add_conflict(
        self,
        code: ConflictCode,
        severity: Severity,
        message: str,
        expected: Any = None,
        actual: Any = None,
    ) -> None:
        """Add a conflict."""
        self.conflicts.append(
            Conflict(
                code=code,
                severity=severity,
                message=message,
                expected=expected,
                actual=actual,
            )
        )
        if severity == Severity.CRITICAL:
            self.valid = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "state_conflict": self.state_conflict,
            "timestamp": self.timestamp.isoformat(),
            "conflicts": [
                {
                    "code": c.code.value,
                    "severity": c.severity.value,
                    "message": c.message,
                    "expected": c.expected,
                    "actual": c.actual,
                }
                for c in self.conflicts
            ],
        }


# =============================================================================
# ORIENTATION VALIDATOR
# =============================================================================


class OrientationValidator:
    """
    Validates ORIENTATION_BEAD against system state.

    INV-D3-CROSS-CHECK-1: Every field verifiable against source.
    INV-D3-CORRUPTION-1: Corruption → STATE_CONFLICT.

    THE KILL TEST - Must detect 5 corruption variants:
    1. Hash wrong
    2. Fields invalid (enum out of range)
    3. Stale timestamp (>1 hour old)
    4. Mode mismatch
    5. Position count mismatch
    """

    # Stale threshold
    STALE_THRESHOLD_SEC = 3600  # 1 hour

    def __init__(
        self,
        halt_provider: HaltManagerProvider | None = None,
        position_provider: PositionTrackerProvider | None = None,
        heartbeat_provider: HeartbeatProvider | None = None,
    ) -> None:
        """
        Initialize validator with system state providers.

        Args:
            halt_provider: Halt manager for kill flags verification
            position_provider: Position tracker for position count verification
            heartbeat_provider: Heartbeat daemon for status verification
        """
        self._halt_provider = halt_provider
        self._position_provider = position_provider
        self._heartbeat_provider = heartbeat_provider

    def validate(self, bead: OrientationBead) -> ValidationResult:
        """
        Validate orientation bead.

        INV-D3-CORRUPTION-1: Any corruption → STATE_CONFLICT

        Args:
            bead: OrientationBead to validate

        Returns:
            ValidationResult with conflicts
        """
        result = ValidationResult(valid=True)

        # 1. HASH INTEGRITY (THE KILL TEST - Variant 1)
        self._check_hash_integrity(bead, result)

        # 2. ENUM VALIDITY (THE KILL TEST - Variant 2)
        self._check_enum_validity(bead, result)

        # 3. TIMESTAMP FRESHNESS (THE KILL TEST - Variant 3)
        self._check_timestamp_freshness(bead, result)

        # 4. MODE CONSISTENCY (THE KILL TEST - Variant 4)
        self._check_mode_consistency(bead, result)

        # 5. POSITION COUNT (THE KILL TEST - Variant 5)
        self._check_position_count(bead, result)

        # Additional cross-checks
        self._check_kill_flags(bead, result)
        self._check_heartbeat_status(bead, result)

        return result

    def validate_from_dict(self, data: dict[str, Any]) -> ValidationResult:
        """
        Validate orientation bead from dictionary.

        Args:
            data: Bead data dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        # Try to parse into OrientationBead
        try:
            bead = OrientationBead.from_dict(data)
            return self.validate(bead)
        except (KeyError, ValueError, TypeError) as e:
            result.add_conflict(
                ConflictCode.STATE_CONFLICT_VALIDATION,
                Severity.CRITICAL,
                f"Failed to parse orientation bead: {e}",
            )
            return result

    def validate_from_file(self, path: Path) -> ValidationResult:
        """
        Validate orientation bead from YAML file.

        Args:
            path: Path to orientation.yaml

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        if not path.exists():
            result.add_conflict(
                ConflictCode.STATE_CONFLICT_VALIDATION,
                Severity.CRITICAL,
                f"Orientation file not found: {path}",
            )
            return result

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            return self.validate_from_dict(data)
        except Exception as e:
            result.add_conflict(
                ConflictCode.STATE_CONFLICT_VALIDATION,
                Severity.CRITICAL,
                f"Failed to read orientation file: {e}",
            )
            return result

    # =========================================================================
    # VALIDATION CHECKS (THE KILL TEST - 5 Variants)
    # =========================================================================

    def _check_hash_integrity(self, bead: OrientationBead, result: ValidationResult) -> None:
        """
        KILL TEST VARIANT 1: Hash integrity.

        INV-D3-CORRUPTION-1: Hash mismatch → STATE_CONFLICT_HASH
        """
        computed = bead.compute_hash()
        if bead.bead_hash != computed:
            result.add_conflict(
                ConflictCode.STATE_CONFLICT_HASH,
                Severity.CRITICAL,
                "Bead hash does not match computed hash",
                expected=computed[:16] + "...",
                actual=bead.bead_hash[:16] + "..." if bead.bead_hash else "empty",
            )

    def _check_enum_validity(self, bead: OrientationBead, result: ValidationResult) -> None:
        """
        KILL TEST VARIANT 2: Enum validity.

        INV-D3-CORRUPTION-1: Invalid enum → STATE_CONFLICT_INVALID_ENUM
        """
        # Check execution_phase
        valid_phases = [p.value for p in ExecutionPhase]
        if bead.execution_phase.value not in valid_phases:
            result.add_conflict(
                ConflictCode.STATE_CONFLICT_INVALID_ENUM,
                Severity.CRITICAL,
                f"Invalid execution_phase: {bead.execution_phase.value}",
                expected=valid_phases,
                actual=bead.execution_phase.value,
            )

        # Check mode
        valid_modes = [m.value for m in ModeEnum]
        if bead.mode.value not in valid_modes:
            result.add_conflict(
                ConflictCode.STATE_CONFLICT_INVALID_ENUM,
                Severity.CRITICAL,
                f"Invalid mode: {bead.mode.value}",
                expected=valid_modes,
                actual=bead.mode.value,
            )

        # Check heartbeat_status
        valid_statuses = [s.value for s in HeartbeatStatusEnum]
        if bead.heartbeat_status.value not in valid_statuses:
            result.add_conflict(
                ConflictCode.STATE_CONFLICT_INVALID_ENUM,
                Severity.CRITICAL,
                f"Invalid heartbeat_status: {bead.heartbeat_status.value}",
                expected=valid_statuses,
                actual=bead.heartbeat_status.value,
            )

    def _check_timestamp_freshness(self, bead: OrientationBead, result: ValidationResult) -> None:
        """
        KILL TEST VARIANT 3: Timestamp freshness.

        INV-D3-CORRUPTION-1: >1 hour old → STATE_CONFLICT_STALE
        """
        now = datetime.now(UTC)
        age = (now - bead.generated_at).total_seconds()

        if age > self.STALE_THRESHOLD_SEC:
            result.add_conflict(
                ConflictCode.STATE_CONFLICT_STALE,
                Severity.CRITICAL,  # Make critical for kill test
                f"Orientation bead is {age:.0f}s old (threshold: {self.STALE_THRESHOLD_SEC}s)",
                expected=f"<{self.STALE_THRESHOLD_SEC}s",
                actual=f"{age:.0f}s",
            )

    def _check_mode_consistency(self, bead: OrientationBead, result: ValidationResult) -> None:
        """
        KILL TEST VARIANT 4: Mode consistency.

        INV-D3-CROSS-CHECK-1: Mode must match IBKR_MODE env var.
        """
        env_mode = os.environ.get("IBKR_MODE", "PAPER").upper()

        # Normalize for comparison
        try:
            system_mode = ModeEnum(env_mode)
        except ValueError:
            system_mode = ModeEnum.PAPER

        if bead.mode != system_mode:
            result.add_conflict(
                ConflictCode.STATE_CONFLICT_MODE,
                Severity.CRITICAL,
                f"Mode mismatch: bead says {bead.mode.value}, system says {system_mode.value}",
                expected=system_mode.value,
                actual=bead.mode.value,
            )

    def _check_position_count(self, bead: OrientationBead, result: ValidationResult) -> None:
        """
        KILL TEST VARIANT 5: Position count consistency.

        INV-D3-CROSS-CHECK-1: positions_open must match position tracker.
        """
        if self._position_provider:
            actual_count = self._position_provider.get_open_positions_count()
            if bead.positions_open != actual_count:
                result.add_conflict(
                    ConflictCode.STATE_CONFLICT_POSITIONS,
                    Severity.CRITICAL,
                    f"Position count mismatch: bead={bead.positions_open}, tracker={actual_count}",
                    expected=actual_count,
                    actual=bead.positions_open,
                )

    def _check_kill_flags(self, bead: OrientationBead, result: ValidationResult) -> None:
        """
        Cross-check kill flags count.

        INV-D3-CROSS-CHECK-1: kill_flags_active must match halt manager.
        """
        if self._halt_provider:
            actual_count = self._halt_provider.get_active_kill_flags_count()
            if bead.kill_flags_active != actual_count:
                result.add_conflict(
                    ConflictCode.STATE_CONFLICT_KILL_FLAGS,
                    Severity.CRITICAL,
                    f"Kill flags mismatch: bead={bead.kill_flags_active}, halt={actual_count}",
                    expected=actual_count,
                    actual=bead.kill_flags_active,
                )

    def _check_heartbeat_status(self, bead: OrientationBead, result: ValidationResult) -> None:
        """
        Cross-check heartbeat status.

        INV-D3-CROSS-CHECK-1: heartbeat_status must match heartbeat daemon.
        """
        if self._heartbeat_provider:
            actual_status = self._heartbeat_provider.get_status()
            try:
                actual_enum = HeartbeatStatusEnum(actual_status.upper())
            except ValueError:
                actual_enum = HeartbeatStatusEnum.UNKNOWN

            if bead.heartbeat_status != actual_enum:
                msg = (
                    f"Heartbeat mismatch: bead={bead.heartbeat_status.value}, "
                    f"actual={actual_enum.value}"
                )
                result.add_conflict(
                    ConflictCode.STATE_CONFLICT_HEARTBEAT,
                    Severity.CRITICAL,
                    msg,
                    expected=actual_enum.value,
                    actual=bead.heartbeat_status.value,
                )


# =============================================================================
# HELPER: Create corrupted beads for testing
# =============================================================================


def create_corrupted_bead(
    corruption_type: str,
    base_bead: OrientationBead | None = None,
) -> OrientationBead:
    """
    Create corrupted bead for testing.

    KILL TEST: Each corruption type must trigger STATE_CONFLICT.

    Args:
        corruption_type: One of "hash", "enum", "stale", "mode", "positions"
        base_bead: Base bead to corrupt (creates new if None)

    Returns:
        Corrupted OrientationBead
    """
    if base_bead is None:
        base_bead = OrientationBead()

    # Copy fields
    bead = OrientationBead(
        bead_id=base_bead.bead_id,
        generated_at=base_bead.generated_at,
        execution_phase=base_bead.execution_phase,
        mode=base_bead.mode,
        active_invariants_count=base_bead.active_invariants_count,
        kill_flags_active=base_bead.kill_flags_active,
        unresolved_drift_count=base_bead.unresolved_drift_count,
        positions_open=base_bead.positions_open,
        heartbeat_status=base_bead.heartbeat_status,
        last_human_action_bead_id=base_bead.last_human_action_bead_id,
        last_alert_id=base_bead.last_alert_id,
        bead_hash=base_bead.bead_hash,
    )

    if corruption_type == "hash":
        # VARIANT 1: Wrong hash
        bead.bead_hash = "deadbeef" * 8

    elif corruption_type == "enum":
        # VARIANT 2: Invalid enum (can't set invalid directly, but we can test parsing)
        # For testing, we return a valid bead but tests will inject bad values
        pass

    elif corruption_type == "stale":
        # VARIANT 3: Stale timestamp (>1 hour old)
        bead.generated_at = datetime.now(UTC) - timedelta(hours=2)
        # Recompute hash with stale timestamp
        bead.bead_hash = bead.compute_hash()

    elif corruption_type == "mode":
        # VARIANT 4: Mode mismatch (say LIVE when system is PAPER)
        bead.mode = ModeEnum.LIVE_LOCKED
        # Recompute hash with wrong mode
        bead.bead_hash = bead.compute_hash()

    elif corruption_type == "positions":
        # VARIANT 5: Position count wrong
        bead.positions_open = 999
        # Recompute hash with wrong count
        bead.bead_hash = bead.compute_hash()

    return bead
