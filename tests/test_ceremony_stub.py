"""
Tests for ceremony stub enforcement (S59 T5).

INV-CEREMONY-BLOCKS-ACTIVE: Overdue review halts lease execution.

The ceremony check is integrated into sovereign_gate.py (CHECK 3).
This test file provides the dedicated exit gate per the S59 brief.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.halt import HaltSignalResult
from governance.lease import LeaseManager, LeaseStateMachine, NullBeadEmitter
from governance.lease_types import (
    Lease,
    LeaseBounds,
    LeaseDuration,
    LeaseIdentity,
    LeaseSubject,
)
from governance.sovereign_gate import (
    CeremonyOverdueError,
    check_sovereign_gate,
)


@pytest.fixture()
def swarm_dir(tmp_path: Path) -> Path:
    swarm = tmp_path / "phoenix-swarm"
    swarm.mkdir()
    return swarm


def _make_active_manager(swarm_dir: Path) -> LeaseManager:
    LeaseManager._instance = None
    manager = LeaseManager()

    lease = Lease(
        identity=LeaseIdentity(created_at=datetime.now(UTC), created_by="TEST"),
        subject=LeaseSubject(strategy_ref="CEREMONY_v1.0.0", strategy_hash="cer123"),
        duration=LeaseDuration(
            starts_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
            duration_days=7,
        ),
        bounds=LeaseBounds(
            max_drawdown_pct=5.0,
            max_consecutive_losses=3,
            allowed_pairs=["EURUSD"],
            allowed_pairs_mode="ALL",
        ),
    )

    sm = LeaseStateMachine(lease=lease, bead_emitter=NullBeadEmitter())
    no_halt = HaltSignalResult(halted=False)
    with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
        sm.activate()
    manager._active_lease = sm
    return manager


class TestCeremonyStubEnforcement:
    """INV-CEREMONY-BLOCKS-ACTIVE: Overdue ceremony halts execution."""

    def test_future_review_proceeds(self, swarm_dir: Path) -> None:
        manager = _make_active_manager(swarm_dir)
        sm = manager._active_lease
        assert sm is not None
        sm.lease.governance.next_review_due = datetime.now(UTC) + timedelta(days=5)

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            check_sovereign_gate(
                require_active_lease=True,
                swarm_path=swarm_dir,
                lease_manager_fn=lambda: manager,
            )

    def test_past_review_blocks(self, swarm_dir: Path) -> None:
        manager = _make_active_manager(swarm_dir)
        sm = manager._active_lease
        assert sm is not None
        sm.lease.governance.next_review_due = datetime.now(UTC) - timedelta(hours=2)

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            with pytest.raises(CeremonyOverdueError):
                check_sovereign_gate(
                    require_active_lease=True,
                    swarm_path=swarm_dir,
                    lease_manager_fn=lambda: manager,
                )

    def test_no_review_set_proceeds(self, swarm_dir: Path) -> None:
        manager = _make_active_manager(swarm_dir)
        sm = manager._active_lease
        assert sm is not None
        sm.lease.governance.next_review_due = None

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            check_sovereign_gate(
                require_active_lease=True,
                swarm_path=swarm_dir,
                lease_manager_fn=lambda: manager,
            )

    def test_overdue_transitions_concept_not_expired(self, swarm_dir: Path) -> None:
        """Overdue ceremony → HALTED (not EXPIRED, not REVOKED)."""
        manager = _make_active_manager(swarm_dir)
        sm = manager._active_lease
        assert sm is not None
        sm.lease.governance.next_review_due = datetime.now(UTC) - timedelta(days=1)

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            with pytest.raises(CeremonyOverdueError) as exc:
                check_sovereign_gate(
                    require_active_lease=True,
                    swarm_path=swarm_dir,
                    lease_manager_fn=lambda: manager,
                )
            assert "CEREMONY" in exc.value.invariant
