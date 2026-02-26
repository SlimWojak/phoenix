"""
Tests for DurableBeadEmitter and boot recovery (S59 T2).

INVARIANTS:
  INV-GOVERNANCE-MUTATION-ATOMIC: State mutates only after durable bead write succeeds
  INV-GOV-BEAD-IDEMPOTENT: Deterministic bead ID prevents retry duplicates
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.bead_emitter import DurableBeadEmitter, check_orphaned_leases
from governance.halt import HaltSignalResult
from governance.lease import LeaseStateMachine
from governance.lease_types import (
    CartridgeInsertionBead,
    Lease,
    LeaseActivationBead,
    LeaseBounds,
    LeaseDuration,
    LeaseIdentity,
    LeaseSubject,
)


@pytest.fixture()
def bead_dir(tmp_path: Path) -> Path:
    d = tmp_path / "governance_beads"
    d.mkdir()
    return d


def _make_lease() -> Lease:
    return Lease(
        identity=LeaseIdentity(
            lease_id="lease_test_001",
            created_at=datetime.now(UTC),
            created_by="TEST",
        ),
        subject=LeaseSubject(
            strategy_ref="TEST_STRAT_v1.0.0",
            strategy_hash="abc123",
        ),
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


class TestDurableBeadEmitter:
    """INV-GOVERNANCE-MUTATION-ATOMIC"""

    def test_insertion_bead_persists_to_disk(self, bead_dir: Path) -> None:
        emitter = DurableBeadEmitter(bead_dir)
        bead = CartridgeInsertionBead(
            cartridge_ref="TEST_v1.0.0",
            methodology_hash="deadbeef",
            linter_result={"passed": True},
        )
        emitter.emit(bead)

        jsonl = bead_dir / "CARTRIDGE_INSERTION_BEAD.jsonl"
        assert jsonl.exists()
        lines = jsonl.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["cartridge_ref"] == "TEST_v1.0.0"
        assert "_bead_id" in data
        assert "_persisted_at" in data

    def test_activation_bead_persists_to_disk(self, bead_dir: Path) -> None:
        emitter = DurableBeadEmitter(bead_dir)
        bead = LeaseActivationBead(
            lease_id="lease_test_001",
            strategy_ref="TEST_STRAT_v1.0.0",
            bounds_snapshot={"max_drawdown_pct": 5.0},
        )
        emitter.emit(bead)

        jsonl = bead_dir / "LEASE_ACTIVATION_BEAD.jsonl"
        assert jsonl.exists()
        data = json.loads(jsonl.read_text().strip())
        assert data["lease_id"] == "lease_test_001"

    def test_state_transition_bead_on_disk_before_state_change(self, bead_dir: Path) -> None:
        emitter = DurableBeadEmitter(bead_dir)
        lease = _make_lease()
        sm = LeaseStateMachine(lease=lease, bead_emitter=emitter)

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            result = sm.activate()

        from governance.lease_types import TransitionResult

        assert result == TransitionResult.SUCCESS

        state_lock_file = bead_dir / "STATE_LOCK_BEAD.jsonl"
        activation_file = bead_dir / "LEASE_ACTIVATION_BEAD.jsonl"
        assert state_lock_file.exists()
        assert activation_file.exists()

    def test_bead_file_corrupt_detected(self, bead_dir: Path) -> None:
        """Corrupt JSONL entries are skipped with warning, not crash."""
        emitter = DurableBeadEmitter(bead_dir)

        corrupt_path = bead_dir / "LEASE_ACTIVATION_BEAD.jsonl"
        corrupt_path.write_text("{not valid json\n")

        beads = emitter.read_beads("LEASE_ACTIVATION_BEAD")
        assert beads == []


class TestIdempotency:
    """INV-GOV-BEAD-IDEMPOTENT"""

    def test_duplicate_write_does_not_double_persist(self, bead_dir: Path) -> None:
        emitter = DurableBeadEmitter(bead_dir)
        bead = LeaseActivationBead(
            lease_id="lease_idem_001",
            strategy_ref="IDEM_STRAT_v1.0.0",
            bounds_snapshot={"max_drawdown_pct": 5.0},
        )

        emitter.emit(bead)
        emitter.emit(bead)

        jsonl = bead_dir / "LEASE_ACTIVATION_BEAD.jsonl"
        lines = [line for line in jsonl.read_text().strip().split("\n") if line]
        assert len(lines) == 1, f"Expected 1 line (idempotent), got {len(lines)}"


class TestOrphanDetection:
    """Boot recovery: orphaned lease detection."""

    def test_clean_boot_no_orphans(self, bead_dir: Path) -> None:
        orphans = check_orphaned_leases(bead_dir)
        assert orphans == []

    def test_activation_without_terminal_is_orphan(self, bead_dir: Path) -> None:
        emitter = DurableBeadEmitter(bead_dir)
        bead = LeaseActivationBead(
            lease_id="lease_orphan_001",
            strategy_ref="ORPHAN_v1.0.0",
            bounds_snapshot={},
        )
        emitter.emit(bead)

        orphans = check_orphaned_leases(bead_dir)
        assert len(orphans) == 1
        assert orphans[0]["lease_id"] == "lease_orphan_001"

    def test_activation_with_expiry_not_orphan(self, bead_dir: Path) -> None:
        emitter = DurableBeadEmitter(bead_dir)
        from governance.lease_types import LeaseExpiryBead

        act = LeaseActivationBead(
            lease_id="lease_clean_001",
            strategy_ref="CLEAN_v1.0.0",
            bounds_snapshot={},
        )
        exp = LeaseExpiryBead(
            lease_id="lease_clean_001",
            final_stats={},
        )
        emitter.emit(act)
        emitter.emit(exp)

        orphans = check_orphaned_leases(bead_dir)
        assert len(orphans) == 0

    def test_activation_with_revocation_not_orphan(self, bead_dir: Path) -> None:
        emitter = DurableBeadEmitter(bead_dir)
        from governance.lease_types import LeaseRevocationBead

        act = LeaseActivationBead(
            lease_id="lease_revoked_001",
            strategy_ref="REVOKED_v1.0.0",
            bounds_snapshot={},
        )
        rev = LeaseRevocationBead(
            lease_id="lease_revoked_001",
            revoked_by="G",
            reason="done",
        )
        emitter.emit(act)
        emitter.emit(rev)

        orphans = check_orphaned_leases(bead_dir)
        assert len(orphans) == 0

    def test_disk_full_during_write_raises(self, bead_dir: Path) -> None:
        """CV6: Disk full → write fails loudly, not silent success."""
        emitter = DurableBeadEmitter(bead_dir)
        bead = LeaseActivationBead(
            lease_id="lease_diskfull",
            strategy_ref="DISK_v1.0.0",
            bounds_snapshot={},
        )

        with patch("os.open", side_effect=OSError("No space left on device")):
            with pytest.raises(OSError, match="No space"):
                emitter.emit(bead)
