"""
Drift Detection — Drift types and records
=========================================

S32: EXECUTION_PATH

Defines drift types and drift record structure.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class DriftType(Enum):
    """Types of drift between Phoenix and broker."""

    POSITION_COUNT = "POSITION_COUNT"      # Number of positions differs
    POSITION_SIZE = "POSITION_SIZE"        # Quantity differs
    PNL = "PNL"                            # P&L differs
    ORDER_STATUS = "ORDER_STATUS"          # Order status mismatch
    PARTIAL_FILL = "PARTIAL_FILL"          # WP_C3: Partial fill ratio mismatch
    MISSING_PHOENIX = "MISSING_PHOENIX"    # Broker has, Phoenix doesn't
    MISSING_BROKER = "MISSING_BROKER"      # Phoenix has, broker doesn't


class DriftSeverity(Enum):
    """Severity of detected drift."""

    WARNING = "WARNING"    # Minor discrepancy
    CRITICAL = "CRITICAL"  # Major mismatch requiring immediate attention


@dataclass
class DriftRecord:
    """
    Record of detected drift.

    Captures the mismatch between Phoenix and broker state.
    """

    drift_id: str = field(default_factory=lambda: f"DRIFT-{uuid.uuid4().hex[:8]}")
    drift_type: DriftType = DriftType.POSITION_SIZE
    severity: DriftSeverity = DriftSeverity.WARNING
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Position details
    position_id: str | None = None
    pair: str = ""

    # State comparison
    phoenix_state: dict[str, Any] = field(default_factory=dict)
    broker_state: dict[str, Any] = field(default_factory=dict)

    # Resolution
    resolved: bool = False
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution: str | None = None

    @property
    def age_sec(self) -> float:
        """Age of drift in seconds."""
        return (datetime.now(UTC) - self.detected_at).total_seconds()

    @property
    def time_to_resolve_sec(self) -> float | None:
        """Time from detection to resolution."""
        if not self.resolved or self.resolved_at is None:
            return None
        return (self.resolved_at - self.detected_at).total_seconds()

    def resolve(self, resolution: str, resolved_by: str) -> None:
        """Mark drift as resolved."""
        self.resolved = True
        self.resolved_at = datetime.now(UTC)
        self.resolved_by = resolved_by
        self.resolution = resolution

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "drift_id": self.drift_id,
            "drift_type": self.drift_type.value,
            "severity": self.severity.value,
            "detected_at": self.detected_at.isoformat(),
            "position_id": self.position_id,
            "pair": self.pair,
            "phoenix_state": self.phoenix_state,
            "broker_state": self.broker_state,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution": self.resolution,
            "age_sec": self.age_sec,
            "time_to_resolve_sec": self.time_to_resolve_sec,
        }

    def to_bead_data(self) -> dict[str, Any]:
        """Convert to bead data format."""
        return {
            "bead_type": "RECONCILIATION_DRIFT",
            "drift_id": self.drift_id,
            "drift_type": self.drift_type.value,
            "severity": self.severity.value,
            "position_id": self.position_id,
            "phoenix_state": self.phoenix_state,
            "broker_state": self.broker_state,
            "alert_sent": True,
            "timestamp_utc": self.detected_at.isoformat(),
        }


@dataclass
class ResolutionRecord:
    """Record of drift resolution."""

    resolution_id: str = field(default_factory=lambda: f"RES-{uuid.uuid4().hex[:8]}")
    drift_id: str = ""
    resolution: str = ""  # PHOENIX_CORRECTED, BROKER_CORRECTED, ACKNOWLEDGED, STALE_IGNORED
    resolved_by: str = ""
    resolved_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    notes: str = ""

    def to_bead_data(self, drift: DriftRecord) -> dict[str, Any]:
        """Convert to bead data format."""
        return {
            "bead_type": "RECONCILIATION_RESOLUTION",
            "resolution_id": self.resolution_id,
            "drift_bead_id": self.drift_id,
            "resolution": self.resolution,
            "resolved_by": self.resolved_by,
            "notes": self.notes,
            "time_to_resolve_sec": int(drift.time_to_resolve_sec or 0),
            "timestamp_utc": self.resolved_at.isoformat(),
        }
