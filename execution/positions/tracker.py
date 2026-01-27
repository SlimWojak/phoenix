"""
Position Tracker — Active position management
=============================================

S32: EXECUTION_PATH

Tracks all positions and monitors for stale submissions.

INVARIANT: INV-POSITION-SUBMITTED-TTL-1
Monitors SUBMITTED positions and transitions to STALLED after 60s.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .lifecycle import Position, PositionLifecycle
from .states import PositionState


class PositionTracker:
    """
    Tracks all positions in the system.

    Provides:
    - Position lookup by ID
    - Active position queries
    - Stale submission monitoring (INV-POSITION-SUBMITTED-TTL-1)
    """

    def __init__(
        self,
        lifecycle: PositionLifecycle | None = None,
        emit_bead: Callable[[dict[str, Any]], None] | None = None,
        emit_alert: Callable[[str, str], None] | None = None,
    ) -> None:
        """
        Initialize tracker.

        Args:
            lifecycle: Lifecycle manager (created if not provided)
            emit_bead: Callback for bead emission
            emit_alert: Callback for alerts
        """
        self._positions: dict[str, Position] = {}
        self._lifecycle = lifecycle or PositionLifecycle(
            emit_bead=emit_bead,
            emit_alert=emit_alert,
        )
        self._emit_alert = emit_alert

    @property
    def lifecycle(self) -> PositionLifecycle:
        """Get lifecycle manager."""
        return self._lifecycle

    # =========================================================================
    # POSITION MANAGEMENT
    # =========================================================================

    def add(self, position: Position) -> None:
        """Add position to tracker."""
        self._positions[position.position_id] = position

    def get(self, position_id: str) -> Position | None:
        """Get position by ID."""
        return self._positions.get(position_id)

    def remove(self, position_id: str) -> Position | None:
        """Remove position from tracker."""
        return self._positions.pop(position_id, None)

    # =========================================================================
    # QUERIES
    # =========================================================================

    def get_all(self) -> list[Position]:
        """Get all positions."""
        return list(self._positions.values())

    def get_by_state(self, state: PositionState) -> list[Position]:
        """Get positions in specific state."""
        return [p for p in self._positions.values() if p.state == state]

    def get_active(self) -> list[Position]:
        """Get actively managed positions (FILLED, MANAGED)."""
        return [p for p in self._positions.values() if p.state.is_active]

    def get_pending(self) -> list[Position]:
        """Get pending positions (PROPOSED, APPROVED, SUBMITTED)."""
        pending_states = {
            PositionState.PROPOSED,
            PositionState.APPROVED,
            PositionState.SUBMITTED,
        }
        return [p for p in self._positions.values() if p.state in pending_states]

    def get_stalled(self) -> list[Position]:
        """Get STALLED positions requiring attention."""
        return self.get_by_state(PositionState.STALLED)

    def get_by_pair(self, pair: str) -> list[Position]:
        """Get positions for a specific pair."""
        return [p for p in self._positions.values() if p.pair == pair]

    def get_submitted(self) -> list[Position]:
        """Get positions in SUBMITTED state."""
        return self.get_by_state(PositionState.SUBMITTED)

    # =========================================================================
    # STALE MONITORING (INV-POSITION-SUBMITTED-TTL-1)
    # =========================================================================

    def check_stale_submissions(self) -> list[Position]:
        """
        Check for stale SUBMITTED positions and transition to STALLED.

        INVARIANT: INV-POSITION-SUBMITTED-TTL-1
        SUBMITTED > 60s → STALLED + alert

        WP_C1: NO automatic retry. Human must decide.

        Returns:
            List of positions that were transitioned to STALLED
        """
        stalled = []
        for position in self.get_submitted():
            if self._lifecycle.check_stale_submitted(position):
                stalled.append(position)

        return stalled

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_stats(self) -> dict[str, Any]:
        """Get tracker statistics."""
        positions = self.get_all()

        # Count by state
        by_state: dict[str, int] = {}
        for pos in positions:
            state = pos.state.value
            by_state[state] = by_state.get(state, 0) + 1

        # Count active and pending
        active = len(self.get_active())
        pending = len(self.get_pending())
        stalled = len(self.get_stalled())

        # Calculate total P&L from closed positions
        closed = self.get_by_state(PositionState.CLOSED)
        total_pnl = sum(p.realized_pnl or 0 for p in closed)

        return {
            "total": len(positions),
            "active": active,
            "pending": pending,
            "stalled": stalled,
            "by_state": by_state,
            "closed_count": len(closed),
            "total_pnl": total_pnl,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def cleanup_terminal(self, max_age_sec: int = 3600) -> int:
        """
        Remove old terminal positions from tracker.

        Args:
            max_age_sec: Remove positions older than this

        Returns:
            Number of positions removed
        """
        from datetime import timedelta

        cutoff = datetime.now(UTC) - timedelta(seconds=max_age_sec)
        removed = 0

        for pos_id, pos in list(self._positions.items()):
            if pos.is_terminal and pos.state_changed_at < cutoff:
                del self._positions[pos_id]
                removed += 1

        return removed
