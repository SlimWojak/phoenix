"""
Orientation Generator — ORIENTATION_BEAD Factory
=================================================

S34: D3 ORIENTATION_BEAD_CHECKSUM

Aggregates system state into machine-verifiable orientation bead.

INVARIANTS:
- INV-D3-CHECKSUM-1: All fields machine-verifiable, no prose
- INV-D3-NO-DERIVED-1: No interpreted/summary fields

FORBIDDEN:
- system_stable, risk_level, narrative_state, summary, recommendation
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

# =============================================================================
# ENUMS (Frozen — No "latest" or open-ended values)
# =============================================================================


class ExecutionPhase(str, Enum):
    """Execution phase enum (frozen list)."""

    S29_FOUNDATION = "S29_FOUNDATION"
    S30_BASELINE = "S30_BASELINE"
    S31_HARDENING = "S31_HARDENING"
    S32_EXECUTION_PATH = "S32_EXECUTION_PATH"
    S33_P1_INFRASTRUCTURE = "S33_P1_INFRASTRUCTURE"
    S33_P2_LIVE = "S33_P2_LIVE"
    S34_OPERATIONAL = "S34_OPERATIONAL"
    S35_PILOT_STRATEGIST = "S35_PILOT_STRATEGIST"


class ModeEnum(str, Enum):
    """Execution mode enum."""

    MOCK = "MOCK"
    PAPER = "PAPER"
    LIVE_LOCKED = "LIVE_LOCKED"


class HeartbeatStatusEnum(str, Enum):
    """Heartbeat status enum."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    MISSED = "MISSED"
    UNKNOWN = "UNKNOWN"


# =============================================================================
# PROVIDERS (Protocols for data sources)
# =============================================================================


class HaltManagerProvider(Protocol):
    """Protocol for halt manager data."""

    def get_active_kill_flags_count(self) -> int:
        """Get count of active kill flags."""
        ...


class PositionTrackerProvider(Protocol):
    """Protocol for position tracker data."""

    def get_open_positions_count(self) -> int:
        """Get count of open positions."""
        ...


class BeadStoreProvider(Protocol):
    """Protocol for bead store queries."""

    def get_unresolved_drift_count(self) -> int:
        """Get count of unresolved drift beads."""
        ...

    def get_last_human_action_bead_id(self) -> str | None:
        """Get most recent human-signed bead ID."""
        ...


class HeartbeatProvider(Protocol):
    """Protocol for heartbeat data."""

    def get_status(self) -> str:
        """Get heartbeat status."""
        ...


class AlertStoreProvider(Protocol):
    """Protocol for alert store data."""

    def get_last_alert_id(self) -> str | None:
        """Get most recent alert ID."""
        ...


# =============================================================================
# ORIENTATION BEAD DATA
# =============================================================================


@dataclass
class OrientationBead:
    """
    ORIENTATION_BEAD — Machine-verifiable system state checksum.

    INV-D3-CHECKSUM-1: All fields machine-verifiable, no prose.
    INV-D3-NO-DERIVED-1: No interpreted/summary fields.
    """

    # Identity
    bead_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Phase & Mode
    execution_phase: ExecutionPhase = ExecutionPhase.S34_OPERATIONAL
    mode: ModeEnum = ModeEnum.PAPER

    # Counts (machine-verifiable integers)
    active_invariants_count: int = 0
    kill_flags_active: int = 0
    unresolved_drift_count: int = 0
    positions_open: int = 0

    # Health
    heartbeat_status: HeartbeatStatusEnum = HeartbeatStatusEnum.UNKNOWN

    # Audit trail
    last_human_action_bead_id: str | None = None
    last_alert_id: str | None = None

    # Checksum (computed)
    bead_hash: str = ""

    def __post_init__(self) -> None:
        """Compute hash if not provided."""
        if not self.bead_hash:
            self.bead_hash = self.compute_hash()

    def compute_hash(self) -> str:
        """
        Compute SHA256 hash of all fields (except bead_hash itself).

        INV-D3-CHECKSUM-1: Deterministic, machine-verifiable.
        """
        fields = {
            "bead_id": self.bead_id,
            "generated_at": self.generated_at.isoformat(),
            "execution_phase": self.execution_phase.value,
            "mode": self.mode.value,
            "active_invariants_count": self.active_invariants_count,
            "kill_flags_active": self.kill_flags_active,
            "unresolved_drift_count": self.unresolved_drift_count,
            "positions_open": self.positions_open,
            "heartbeat_status": self.heartbeat_status.value,
            "last_human_action_bead_id": self.last_human_action_bead_id,
            "last_alert_id": self.last_alert_id,
        }

        json_str = json.dumps(fields, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def verify_hash(self) -> bool:
        """Verify stored hash matches computed hash."""
        return self.bead_hash == self.compute_hash()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bead_id": self.bead_id,
            "generated_at": self.generated_at.isoformat(),
            "execution_phase": self.execution_phase.value,
            "mode": self.mode.value,
            "active_invariants_count": self.active_invariants_count,
            "kill_flags_active": self.kill_flags_active,
            "unresolved_drift_count": self.unresolved_drift_count,
            "positions_open": self.positions_open,
            "heartbeat_status": self.heartbeat_status.value,
            "last_human_action_bead_id": self.last_human_action_bead_id,
            "last_alert_id": self.last_alert_id,
            "bead_hash": self.bead_hash,
        }

    def to_yaml_compact(self) -> str:
        """
        Convert to compact YAML (≤1000 tokens).

        Format optimized for machine parsing.
        """
        import yaml

        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrientationBead:
        """Create from dictionary."""
        return cls(
            bead_id=data.get("bead_id", str(uuid.uuid4())),
            generated_at=datetime.fromisoformat(data["generated_at"])
            if "generated_at" in data
            else datetime.now(UTC),
            execution_phase=ExecutionPhase(data.get("execution_phase", "S34_OPERATIONAL")),
            mode=ModeEnum(data.get("mode", "PAPER")),
            active_invariants_count=data.get("active_invariants_count", 0),
            kill_flags_active=data.get("kill_flags_active", 0),
            unresolved_drift_count=data.get("unresolved_drift_count", 0),
            positions_open=data.get("positions_open", 0),
            heartbeat_status=HeartbeatStatusEnum(data.get("heartbeat_status", "UNKNOWN")),
            last_human_action_bead_id=data.get("last_human_action_bead_id"),
            last_alert_id=data.get("last_alert_id"),
            bead_hash=data.get("bead_hash", ""),
        )


# =============================================================================
# ORIENTATION GENERATOR
# =============================================================================


class OrientationGenerator:
    """
    Generates ORIENTATION_BEAD from system state.

    INV-D3-CHECKSUM-1: Aggregates only machine-verifiable data.
    INV-D3-NO-DERIVED-1: No interpretation, no summaries.
    """

    # Default invariant count (from beads.yaml and known invariants)
    DEFAULT_INVARIANT_COUNT = 71  # S29-S33 cumulative

    def __init__(
        self,
        halt_provider: HaltManagerProvider | None = None,
        position_provider: PositionTrackerProvider | None = None,
        bead_provider: BeadStoreProvider | None = None,
        heartbeat_provider: HeartbeatProvider | None = None,
        alert_provider: AlertStoreProvider | None = None,
        state_dir: Path | None = None,
    ) -> None:
        """
        Initialize generator.

        Args:
            halt_provider: Halt manager data source
            position_provider: Position tracker data source
            bead_provider: Bead store data source
            heartbeat_provider: Heartbeat data source
            alert_provider: Alert store data source
            state_dir: Directory to write orientation.yaml
        """
        self._halt_provider = halt_provider
        self._position_provider = position_provider
        self._bead_provider = bead_provider
        self._heartbeat_provider = heartbeat_provider
        self._alert_provider = alert_provider
        self._state_dir = state_dir or Path(__file__).parent.parent / "state"

        # Ensure state dir exists
        self._state_dir.mkdir(parents=True, exist_ok=True)

    def generate(self) -> OrientationBead:
        """
        Generate ORIENTATION_BEAD from current system state.

        INV-D3-CHECKSUM-1: Machine-verifiable only.
        INV-D3-NO-DERIVED-1: No interpretation.

        Returns:
            OrientationBead with computed hash
        """
        return OrientationBead(
            execution_phase=self._get_execution_phase(),
            mode=self._get_mode(),
            active_invariants_count=self._get_invariants_count(),
            kill_flags_active=self._get_kill_flags_count(),
            unresolved_drift_count=self._get_unresolved_drift_count(),
            positions_open=self._get_positions_count(),
            heartbeat_status=self._get_heartbeat_status(),
            last_human_action_bead_id=self._get_last_human_bead_id(),
            last_alert_id=self._get_last_alert_id(),
        )

    def generate_and_write(self) -> tuple[OrientationBead, Path]:
        """
        Generate and write to state/orientation.yaml.

        Returns:
            (OrientationBead, path to written file)
        """
        bead = self.generate()
        path = self.write_to_file(bead)
        return bead, path

    def write_to_file(self, bead: OrientationBead) -> Path:
        """
        Write orientation bead to file seam.

        Args:
            bead: OrientationBead to write

        Returns:
            Path to written file
        """
        output_path = self._state_dir / "orientation.yaml"
        output_path.write_text(bead.to_yaml_compact())
        return output_path

    # =========================================================================
    # DATA AGGREGATION (No interpretation — direct queries only)
    # =========================================================================

    def _get_execution_phase(self) -> ExecutionPhase:
        """Get current execution phase from config."""
        # Read from config or default to S34
        return ExecutionPhase.S34_OPERATIONAL

    def _get_mode(self) -> ModeEnum:
        """Get current mode from environment."""
        mode_str = os.environ.get("IBKR_MODE", "PAPER").upper()
        try:
            return ModeEnum(mode_str)
        except ValueError:
            return ModeEnum.PAPER

    def _get_invariants_count(self) -> int:
        """Get count of active invariants."""
        # Could query invariant registry in future
        # For now, return known count from beads.yaml + S29-S34
        return self.DEFAULT_INVARIANT_COUNT

    def _get_kill_flags_count(self) -> int:
        """Get count of active kill flags."""
        if self._halt_provider:
            return self._halt_provider.get_active_kill_flags_count()
        return 0

    def _get_unresolved_drift_count(self) -> int:
        """Get count of unresolved reconciliation drift."""
        if self._bead_provider:
            return self._bead_provider.get_unresolved_drift_count()
        return 0

    def _get_positions_count(self) -> int:
        """Get count of open positions."""
        if self._position_provider:
            return self._position_provider.get_open_positions_count()
        return 0

    def _get_heartbeat_status(self) -> HeartbeatStatusEnum:
        """Get current heartbeat status."""
        if self._heartbeat_provider:
            status_str = self._heartbeat_provider.get_status()
            try:
                return HeartbeatStatusEnum(status_str.upper())
            except ValueError:
                return HeartbeatStatusEnum.UNKNOWN
        return HeartbeatStatusEnum.UNKNOWN

    def _get_last_human_bead_id(self) -> str | None:
        """Get most recent human-signed bead ID."""
        if self._bead_provider:
            return self._bead_provider.get_last_human_action_bead_id()
        return None

    def _get_last_alert_id(self) -> str | None:
        """Get most recent alert ID."""
        if self._alert_provider:
            return self._alert_provider.get_last_alert_id()
        return None
