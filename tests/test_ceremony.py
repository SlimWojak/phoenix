"""
Tests for Ceremony Engine — full attestation lifecycle (S60 T1).

INVARIANTS:
  INV-CEREMONY-BLOCKS-ACTIVE (S59)
  INV-CEREMONY-ATTESTATION-DURABLE
  INV-CEREMONY-BOUNDS-MONOTONIC
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.bead_emitter import DurableBeadEmitter
from governance.ceremony import (
    AttestationDecision,
    CeremonyEngine,
    CeremonyEvidence,
)
from governance.halt import HaltSignalResult
from governance.lease import LeaseStateMachine, NullBeadEmitter
from governance.lease_types import (
    Lease,
    LeaseBounds,
    LeaseDuration,
    LeaseIdentity,
    LeaseState,
    LeaseSubject,
)


@pytest.fixture()
def bead_dir(tmp_path: Path) -> Path:
    d = tmp_path / "ceremony_beads"
    d.mkdir()
    return d


def _make_active_sm(bead_dir: Path | None = None) -> LeaseStateMachine:
    emitter = DurableBeadEmitter(bead_dir) if bead_dir else NullBeadEmitter()
    lease = Lease(
        identity=LeaseIdentity(
            lease_id="lease_ceremony_001",
            created_at=datetime.now(UTC),
            created_by="TEST",
        ),
        subject=LeaseSubject(strategy_ref="CEREMONY_v1.0.0", strategy_hash="cer"),
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
            position_size_cap=2.0,
        ),
    )
    sm = LeaseStateMachine(lease=lease, bead_emitter=emitter)
    no_halt = HaltSignalResult(halted=False)
    with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
        sm.activate()
    return sm


class TestCeremonyScheduling:
    """Lease activated → next_review_due set."""

    def test_schedule_sets_next_review(self) -> None:
        sm = _make_active_sm()
        engine = CeremonyEngine(interval_days=7)
        due = engine.schedule_review(sm)
        assert sm.lease.governance.next_review_due is not None
        assert due > datetime.now(UTC)
        assert due < datetime.now(UTC) + timedelta(days=8)

    def test_schedule_interval_configurable(self) -> None:
        sm = _make_active_sm()
        engine = CeremonyEngine(interval_days=14)
        due = engine.schedule_review(sm)
        diff = (due - datetime.now(UTC)).days
        assert 13 <= diff <= 14


class TestCeremonyAttestation:
    """CeremonyAttestationBead lifecycle."""

    def test_renewed_emits_bead_on_disk(self, bead_dir: Path) -> None:
        sm = _make_active_sm(bead_dir)
        emitter = DurableBeadEmitter(bead_dir)
        engine = CeremonyEngine(emitter=emitter, interval_days=7)
        engine.schedule_review(sm)

        evidence = CeremonyEvidence(total_trades=10, wins=7, losses=3)
        bead = engine.attest(sm, "G", AttestationDecision.RENEWED, evidence)

        assert bead.attestation == "RENEWED"
        assert bead.lease_id == "lease_ceremony_001"

        jsonl = bead_dir / "CEREMONY_ATTESTATION_BEAD.jsonl"
        assert jsonl.exists()

    def test_renewed_advances_next_review_due(self, bead_dir: Path) -> None:
        sm = _make_active_sm(bead_dir)
        emitter = DurableBeadEmitter(bead_dir)
        engine = CeremonyEngine(emitter=emitter, interval_days=7)
        engine.schedule_review(sm)

        old_due = sm.lease.governance.next_review_due

        evidence = CeremonyEvidence()
        engine.attest(sm, "Olya", AttestationDecision.RENEWED, evidence)

        new_due = sm.lease.governance.next_review_due
        assert new_due is not None
        assert old_due is not None
        assert new_due > old_due

    def test_renewed_lease_stays_active(self) -> None:
        sm = _make_active_sm()
        engine = CeremonyEngine(interval_days=7)
        evidence = CeremonyEvidence()
        engine.attest(sm, "G", AttestationDecision.RENEWED, evidence)
        assert sm.state == LeaseState.ACTIVE

    def test_tightened_updates_bounds(self) -> None:
        sm = _make_active_sm()
        engine = CeremonyEngine(interval_days=7)
        evidence = CeremonyEvidence()

        engine.attest(
            sm,
            "G",
            AttestationDecision.TIGHTENED,
            evidence,
            bounds_changes={"max_drawdown_pct": 3.0},
        )

        assert sm.lease.bounds.max_drawdown_pct == 3.0

    def test_tightened_rejects_loosen(self) -> None:
        """INV-CEREMONY-BOUNDS-MONOTONIC: Cannot loosen."""
        sm = _make_active_sm()
        engine = CeremonyEngine(interval_days=7)
        evidence = CeremonyEvidence()

        with pytest.raises(ValueError, match="MONOTONIC"):
            engine.attest(
                sm,
                "G",
                AttestationDecision.TIGHTENED,
                evidence,
                bounds_changes={"max_drawdown_pct": 10.0},
            )

    def test_revoked_transitions_lease(self) -> None:
        sm = _make_active_sm()
        engine = CeremonyEngine(interval_days=7)
        evidence = CeremonyEvidence()

        engine.attest(sm, "G", AttestationDecision.REVOKED, evidence)
        assert sm.state == LeaseState.REVOKED

    def test_missed_ceremony_stays_halted(self) -> None:
        """S59 stub behavior preserved: overdue → sovereign gate blocks."""
        sm = _make_active_sm()
        sm.lease.governance.next_review_due = datetime.now(UTC) - timedelta(hours=1)

        from governance.lease import LeaseManager
        from governance.sovereign_gate import CeremonyOverdueError, check_sovereign_gate

        LeaseManager._instance = None
        manager = LeaseManager()
        manager._active_lease = sm

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            with pytest.raises(CeremonyOverdueError):
                check_sovereign_gate(
                    require_active_lease=True,
                    lease_manager_fn=lambda: manager,
                )

    def test_attestation_bead_fails_to_persist_no_advance(self, bead_dir: Path) -> None:
        """INV-CEREMONY-ATTESTATION-DURABLE: If bead fails to persist, ceremony NOT recorded."""
        sm = _make_active_sm()
        emitter = DurableBeadEmitter(bead_dir)
        engine = CeremonyEngine(emitter=emitter, interval_days=7)
        engine.schedule_review(sm)

        old_due = sm.lease.governance.next_review_due

        with patch.object(emitter, "emit", side_effect=OSError("disk full")):
            with pytest.raises(OSError):
                evidence = CeremonyEvidence()
                engine.attest(sm, "G", AttestationDecision.RENEWED, evidence)

        assert sm.lease.governance.next_review_due == old_due

    def test_evidence_hash_deterministic(self) -> None:
        """Same inputs → same evidence hash."""
        e1 = CeremonyEvidence(total_trades=10, wins=7, losses=3, pnl_total=150.0)
        e2 = CeremonyEvidence(total_trades=10, wins=7, losses=3, pnl_total=150.0)
        assert e1.compute_hash() == e2.compute_hash()

    def test_evidence_no_scalar_grades(self) -> None:
        """Evidence contains no scalar grades — facts only."""
        e = CeremonyEvidence(total_trades=10, wins=7, losses=3)
        evidence_fields = vars(e)
        forbidden = {"score", "grade", "confidence", "quality", "rating", "rank"}
        for field_name in evidence_fields:
            assert field_name not in forbidden, f"Evidence contains forbidden field: {field_name}"
