"""
Heartbeat Bead — Health monitoring bead emission
=================================================

S33: FIRST_BLOOD

Emits HEARTBEAT beads for audit trail of system health.

STATUS:
- HEALTHY: All checks pass
- DEGRADED: Semantic issues, process alive
- MISSED: Heartbeat check failed
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable


class HealthStatus(Enum):
    """Health status for heartbeat."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    MISSED = "MISSED"


@dataclass
class HealthChecks:
    """Individual health check results."""

    process_alive: bool = True
    ibkr_connected: bool = True
    semantic_healthy: bool = True

    def to_dict(self) -> dict[str, bool]:
        """Convert to dictionary."""
        return {
            "process_alive": self.process_alive,
            "ibkr_connected": self.ibkr_connected,
            "semantic_healthy": self.semantic_healthy,
        }

    def all_pass(self) -> bool:
        """Check if all checks pass."""
        return self.process_alive and self.ibkr_connected and self.semantic_healthy

    def get_status(self) -> HealthStatus:
        """Determine status from checks."""
        if not self.process_alive:
            return HealthStatus.MISSED
        if not self.ibkr_connected or not self.semantic_healthy:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY


@dataclass
class HeartbeatBeadData:
    """
    HEARTBEAT bead data structure.

    Matches schema defined in beads.yaml.
    """

    bead_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bead_type: str = "HEARTBEAT"
    prev_bead_id: str | None = None
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    signer: str = "system"
    version: str = "1.0"

    # Heartbeat-specific fields
    status: HealthStatus = HealthStatus.HEALTHY
    checks: HealthChecks = field(default_factory=HealthChecks)
    details: dict[str, Any] | None = None
    miss_count: int = 0

    # Computed
    bead_hash: str = ""

    def __post_init__(self) -> None:
        """Compute hash after initialization."""
        if not self.bead_hash:
            self.bead_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA256 hash of bead content."""
        content = (
            f"{self.bead_type}|{self.status.value}|"
            f"{self.checks.process_alive}|{self.checks.ibkr_connected}|"
            f"{self.checks.semantic_healthy}|{self.miss_count}|"
            f"{self.timestamp_utc.isoformat()}|{self.prev_bead_id or 'null'}|{self.signer}"
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "bead_id": self.bead_id,
            "bead_type": self.bead_type,
            "prev_bead_id": self.prev_bead_id,
            "bead_hash": self.bead_hash,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "signer": self.signer,
            "version": self.version,
            "status": self.status.value,
            "checks": self.checks.to_dict(),
            "details": self.details,
            "miss_count": self.miss_count,
        }


# Type for bead emission callback
BeadEmitter = Callable[[HeartbeatBeadData], None]


class HeartbeatBeadEmitter:
    """
    Emits HEARTBEAT beads for health monitoring.

    Tracks chain for merkle-lite lineage.
    """

    def __init__(self, emitter: BeadEmitter | None = None) -> None:
        """
        Initialize emitter.

        Args:
            emitter: Callback to emit beads (e.g., BeadStore.append)
        """
        self._emitter = emitter
        self._last_bead_id: str | None = None
        self._consecutive_misses: int = 0

    def set_emitter(self, emitter: BeadEmitter) -> None:
        """Set bead emission callback."""
        self._emitter = emitter

    def emit_healthy(self, checks: HealthChecks | None = None) -> HeartbeatBeadData:
        """
        Emit HEALTHY heartbeat bead.

        Args:
            checks: Health check results

        Returns:
            Created bead data
        """
        self._consecutive_misses = 0

        bead = HeartbeatBeadData(
            status=HealthStatus.HEALTHY,
            checks=checks or HealthChecks(),
            miss_count=0,
            prev_bead_id=self._last_bead_id,
        )

        self._emit(bead)
        return bead

    def emit_degraded(
        self,
        checks: HealthChecks,
        details: dict[str, Any] | None = None,
    ) -> HeartbeatBeadData:
        """
        Emit DEGRADED heartbeat bead.

        Args:
            checks: Health check results
            details: Details about degradation

        Returns:
            Created bead data
        """
        bead = HeartbeatBeadData(
            status=HealthStatus.DEGRADED,
            checks=checks,
            details=details,
            miss_count=self._consecutive_misses,
            prev_bead_id=self._last_bead_id,
        )

        self._emit(bead)
        return bead

    def emit_missed(
        self,
        checks: HealthChecks | None = None,
        details: dict[str, Any] | None = None,
    ) -> HeartbeatBeadData:
        """
        Emit MISSED heartbeat bead.

        Args:
            checks: Health check results (if available)
            details: Details about missed heartbeat

        Returns:
            Created bead data
        """
        self._consecutive_misses += 1

        bead = HeartbeatBeadData(
            status=HealthStatus.MISSED,
            checks=checks or HealthChecks(process_alive=False),
            details=details,
            miss_count=self._consecutive_misses,
            prev_bead_id=self._last_bead_id,
        )

        self._emit(bead)
        return bead

    def emit_from_checks(
        self,
        checks: HealthChecks,
        details: dict[str, Any] | None = None,
    ) -> HeartbeatBeadData:
        """
        Emit bead based on check results.

        Args:
            checks: Health check results
            details: Additional details

        Returns:
            Created bead data
        """
        status = checks.get_status()

        if status == HealthStatus.HEALTHY:
            return self.emit_healthy(checks)
        elif status == HealthStatus.DEGRADED:
            return self.emit_degraded(checks, details)
        else:
            return self.emit_missed(checks, details)

    def _emit(self, bead: HeartbeatBeadData) -> None:
        """Emit bead and track chain."""
        self._last_bead_id = bead.bead_id

        if self._emitter:
            self._emitter(bead)

    def get_last_bead_id(self) -> str | None:
        """Get last emitted bead ID for chain tracking."""
        return self._last_bead_id

    def get_consecutive_misses(self) -> int:
        """Get consecutive miss count."""
        return self._consecutive_misses
