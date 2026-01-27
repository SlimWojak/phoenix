"""
Reconciler — Phoenix/Broker state reconciliation
================================================

S32: EXECUTION_PATH

READ-ONLY reconciliation between Phoenix and broker state.
NEVER mutates lifecycle state. Only emits drift beads.

INVARIANTS:
- INV-RECONCILE-READONLY-1: NEVER mutates lifecycle state
- INV-RECONCILE-ALERT-1: Drift triggers immediate alert
- INV-RECONCILE-AUDIT-1: RECONCILIATION_DRIFT bead on detection
- INV-RECONCILE-AUDIT-2: RECONCILIATION_RESOLUTION bead on resolution

WATCHPOINTS:
- WP_C2: Reconciler NEVER mutates state
- WP_C3: partial_fill_ratio drift detection
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .drift import DriftRecord, DriftSeverity, DriftType, ResolutionRecord

if TYPE_CHECKING:
    from brokers.ibkr import IBKRConnector
    from execution.positions import Position, PositionTracker


# Constants
POSITION_SIZE_TOLERANCE = 0.01  # 1% tolerance
PNL_TOLERANCE = 0.50  # $0.50 tolerance
PARTIAL_FILL_TOLERANCE = 0.001  # 0.1% tolerance (WP_C3)
MAX_RECONCILE_PER_MINUTE = 12


class Reconciler:
    """
    Read-only reconciler between Phoenix and broker state.

    INVARIANT: INV-RECONCILE-READONLY-1
    This reconciler NEVER mutates position lifecycle state.
    It only detects drift and emits beads for human action.

    WATCHPOINT WP_C2:
    - Only emit DRIFT / RESOLUTION beads
    - Human action required to unblock
    - NO automatic state correction
    """

    def __init__(
        self,
        tracker: PositionTracker | None = None,
        connector: IBKRConnector | None = None,
        emit_bead: Callable[[dict[str, Any]], None] | None = None,
        emit_alert: Callable[[str, str], None] | None = None,
    ) -> None:
        """
        Initialize reconciler.

        Args:
            tracker: Position tracker (for Phoenix state)
            connector: IBKR connector (for broker state)
            emit_bead: Callback for bead emission
            emit_alert: Callback for alerts
        """
        self._tracker = tracker
        self._connector = connector
        self._emit_bead = emit_bead
        self._emit_alert = emit_alert

        # Drift tracking
        self._active_drifts: dict[str, DriftRecord] = {}
        self._resolved_drifts: list[DriftRecord] = []

        # Rate limiting
        self._last_reconcile: datetime | None = None
        self._reconcile_count_minute = 0

    @property
    def has_unresolved_drift(self) -> bool:
        """Check if there are unresolved drifts."""
        return len(self._active_drifts) > 0

    @property
    def unresolved_drift_count(self) -> int:
        """Count of unresolved drifts."""
        return len(self._active_drifts)

    def get_active_drifts(self) -> list[DriftRecord]:
        """Get all active (unresolved) drifts."""
        return list(self._active_drifts.values())

    # =========================================================================
    # RECONCILIATION (READ-ONLY)
    # =========================================================================

    def reconcile(self) -> list[DriftRecord]:
        """
        Perform reconciliation check.

        INVARIANT: INV-RECONCILE-READONLY-1
        This method NEVER mutates position state.

        Returns:
            List of newly detected drifts
        """
        if self._tracker is None or self._connector is None:
            return []

        # Rate limiting
        if not self._check_rate_limit():
            return []

        new_drifts: list[DriftRecord] = []

        # Get Phoenix positions (active only)
        phoenix_positions = self._tracker.get_active()

        # Get broker positions
        broker_snapshot = self._connector.get_positions()
        broker_positions = {p.symbol: p for p in broker_snapshot.positions}

        # Check each Phoenix position against broker
        for pos in phoenix_positions:
            broker_pos = broker_positions.get(pos.pair)

            if broker_pos is None:
                # Phoenix has position, broker doesn't
                drift = self._create_drift(
                    drift_type=DriftType.MISSING_BROKER,
                    severity=DriftSeverity.CRITICAL,
                    position_id=pos.position_id,
                    pair=pos.pair,
                    phoenix_state={"quantity": pos.filled_quantity},
                    broker_state={"quantity": 0},
                )
                new_drifts.append(drift)
                continue

            # Check position size
            size_drift = self._check_position_size(pos, broker_pos)
            if size_drift:
                new_drifts.append(size_drift)

            # Check partial fill ratio (WP_C3)
            fill_drift = self._check_partial_fill_ratio(pos, broker_pos)
            if fill_drift:
                new_drifts.append(fill_drift)

            # Remove from broker dict (to find orphans)
            del broker_positions[pos.pair]

        # Check for broker positions Phoenix doesn't know about
        for pair, broker_pos in broker_positions.items():
            if broker_pos.quantity != 0:
                drift = self._create_drift(
                    drift_type=DriftType.MISSING_PHOENIX,
                    severity=DriftSeverity.CRITICAL,
                    position_id=None,
                    pair=pair,
                    phoenix_state={"quantity": 0},
                    broker_state={"quantity": broker_pos.quantity},
                )
                new_drifts.append(drift)

        return new_drifts

    def _check_position_size(self, phoenix: Position, broker: Any) -> DriftRecord | None:
        """Check position size match."""
        phoenix_qty = abs(phoenix.filled_quantity)
        broker_qty = abs(broker.quantity)

        if phoenix_qty == 0 and broker_qty == 0:
            return None

        # Calculate difference
        if phoenix_qty == 0:
            diff_pct = 1.0
        else:
            diff_pct = abs(phoenix_qty - broker_qty) / phoenix_qty

        if diff_pct > POSITION_SIZE_TOLERANCE:
            return self._create_drift(
                drift_type=DriftType.POSITION_SIZE,
                severity=DriftSeverity.WARNING if diff_pct < 0.1 else DriftSeverity.CRITICAL,
                position_id=phoenix.position_id,
                pair=phoenix.pair,
                phoenix_state={"quantity": phoenix_qty},
                broker_state={"quantity": broker_qty},
            )

        return None

    def _check_partial_fill_ratio(self, phoenix: Position, broker: Any) -> DriftRecord | None:
        """
        Check partial fill ratio match.

        WATCHPOINT WP_C3:
        partial_fill_ratio accumulates monotonically.
        Reconcile against broker aggregate.
        Alert if Phoenix != Broker ratio.
        """
        if phoenix.requested_quantity <= 0:
            return None

        phoenix_ratio = phoenix.partial_fill_ratio
        broker_qty = abs(broker.quantity)
        req_qty = phoenix.requested_quantity
        broker_ratio = broker_qty / req_qty if req_qty > 0 else 0

        # Check for significant difference
        if abs(phoenix_ratio - broker_ratio) > PARTIAL_FILL_TOLERANCE:
            return self._create_drift(
                drift_type=DriftType.PARTIAL_FILL,
                severity=DriftSeverity.WARNING,
                position_id=phoenix.position_id,
                pair=phoenix.pair,
                phoenix_state={
                    "partial_fill_ratio": phoenix_ratio,
                    "filled_quantity": phoenix.filled_quantity,
                    "requested_quantity": phoenix.requested_quantity,
                },
                broker_state={
                    "partial_fill_ratio": broker_ratio,
                    "quantity": broker_qty,
                },
            )

        return None

    def _create_drift(
        self,
        drift_type: DriftType,
        severity: DriftSeverity,
        position_id: str | None,
        pair: str,
        phoenix_state: dict[str, Any],
        broker_state: dict[str, Any],
    ) -> DriftRecord:
        """
        Create and register a drift record.

        INVARIANT: INV-RECONCILE-AUDIT-1
        Emits RECONCILIATION_DRIFT bead.

        INVARIANT: INV-RECONCILE-ALERT-1
        Sends immediate alert.
        """
        drift = DriftRecord(
            drift_type=drift_type,
            severity=severity,
            position_id=position_id,
            pair=pair,
            phoenix_state=phoenix_state,
            broker_state=broker_state,
        )

        # Register drift
        self._active_drifts[drift.drift_id] = drift

        # Emit bead (INV-RECONCILE-AUDIT-1)
        self._emit_drift_bead(drift)

        # Send alert (INV-RECONCILE-ALERT-1)
        self._send_drift_alert(drift)

        return drift

    # =========================================================================
    # RESOLUTION (Human action required - WP_C2)
    # =========================================================================

    def resolve_drift(
        self,
        drift_id: str,
        resolution: str,
        resolved_by: str,
        notes: str = "",
    ) -> bool:
        """
        Resolve a drift record.

        INVARIANT: INV-RECONCILE-READONLY-1
        This does NOT modify position state.
        It only records that human has acknowledged/resolved the drift.

        INVARIANT: INV-RECONCILE-AUDIT-2
        Emits RECONCILIATION_RESOLUTION bead.

        Args:
            drift_id: Drift to resolve
            resolution: How resolved (PHOENIX_CORRECTED, BROKER_CORRECTED, etc.)
            resolved_by: Human identifier
            notes: Resolution notes

        Returns:
            True if resolved
        """
        drift = self._active_drifts.get(drift_id)
        if drift is None:
            return False

        # Mark drift resolved
        drift.resolve(resolution, resolved_by)

        # Move to resolved list
        del self._active_drifts[drift_id]
        self._resolved_drifts.append(drift)

        # Emit resolution bead (INV-RECONCILE-AUDIT-2)
        resolution_record = ResolutionRecord(
            drift_id=drift_id,
            resolution=resolution,
            resolved_by=resolved_by,
            notes=notes,
        )
        self._emit_resolution_bead(resolution_record, drift)

        return True

    # =========================================================================
    # BEAD EMISSION
    # =========================================================================

    def _emit_drift_bead(self, drift: DriftRecord) -> None:
        """Emit RECONCILIATION_DRIFT bead."""
        if self._emit_bead is None:
            return

        try:
            self._emit_bead(drift.to_bead_data())
        except Exception:  # noqa: S110
            pass  # Non-blocking

    def _emit_resolution_bead(self, resolution: ResolutionRecord, drift: DriftRecord) -> None:
        """Emit RECONCILIATION_RESOLUTION bead."""
        if self._emit_bead is None:
            return

        try:
            self._emit_bead(resolution.to_bead_data(drift))
        except Exception:  # noqa: S110
            pass  # Non-blocking

    def _send_drift_alert(self, drift: DriftRecord) -> None:
        """Send alert for detected drift."""
        if self._emit_alert is None:
            return

        level = "CRITICAL" if drift.severity == DriftSeverity.CRITICAL else "WARNING"
        message = (
            f"DRIFT DETECTED: {drift.drift_type.value} on {drift.pair}. "
            f"Phoenix: {drift.phoenix_state}, Broker: {drift.broker_state}"
        )

        try:
            self._emit_alert(message, level)
        except Exception:  # noqa: S110
            pass  # Non-blocking

    # =========================================================================
    # RATE LIMITING
    # =========================================================================

    def _check_rate_limit(self) -> bool:
        """Check if reconciliation is within rate limit."""
        now = datetime.now(UTC)

        if self._last_reconcile is None:
            self._last_reconcile = now
            self._reconcile_count_minute = 1
            return True

        # Reset counter if new minute
        elapsed = (now - self._last_reconcile).total_seconds()
        if elapsed > 60:
            self._last_reconcile = now
            self._reconcile_count_minute = 1
            return True

        # Check limit
        if self._reconcile_count_minute >= MAX_RECONCILE_PER_MINUTE:
            return False

        self._reconcile_count_minute += 1
        return True

    # =========================================================================
    # QUERIES
    # =========================================================================

    def get_stats(self) -> dict[str, Any]:
        """Get reconciliation statistics."""
        return {
            "active_drifts": len(self._active_drifts),
            "resolved_drifts": len(self._resolved_drifts),
            "has_unresolved": self.has_unresolved_drift,
            "last_reconcile": self._last_reconcile.isoformat() if self._last_reconcile else None,
            "reconcile_count_minute": self._reconcile_count_minute,
        }
