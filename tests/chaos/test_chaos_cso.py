"""
Test Chaos CSO — BOAR attack vectors for CSO.

SPRINT: S27.0
TRACK: D

Vectors:
- V2-CSO-001: heresy_hallucination
- V2-CSO-002: cso_exec_write
- V2-CSO-003: bead_mutation
"""

import sys
from pathlib import Path

import pytest

PHOENIX_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class TestV2CSO001HeresyHallucination:
    """
    V2-CSO-001: heresy_hallucination

    Attack: CSO drafts bead from hallucinated comprehension
    Detection: comprehension_hash mismatch
    """

    def test_comprehension_hash_detects_mismatch(self):
        """Bead hash changes if content changes."""
        from cso import BeadFactory

        factory = BeadFactory(source_module="test")

        # Same parameters should produce same hash
        bead1 = factory.create_decision_bead(
            symbol="EURUSD",
            direction="LONG",
            confidence=0.8,
            gate_result={"q1": True},
            state_hash="abc123",
        )

        bead2 = factory.create_decision_bead(
            symbol="EURUSD",
            direction="LONG",
            confidence=0.8,
            gate_result={"q1": True},
            state_hash="abc123",
        )

        # Hashes should match for same input
        assert bead1.comprehension_hash == bead2.comprehension_hash

        # Different content = different hash
        bead3 = factory.create_decision_bead(
            symbol="EURUSD",
            direction="SHORT",  # Different
            confidence=0.8,
            gate_result={"q1": True},
            state_hash="abc123",
        )

        assert bead1.comprehension_hash != bead3.comprehension_hash

    def test_comprehension_hash_exists(self):
        """All beads have comprehension hash."""
        from cso import BeadFactory

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="LONG", confidence=0.8, gate_result={}, state_hash="abc123"
        )

        assert bead.comprehension_hash
        assert len(bead.comprehension_hash) == 16


class TestV2CSO002CSOExecWrite:
    """
    V2-CSO-002: cso_exec_write

    Attack: CSO attempts to write execution_state
    Detection: CSOWriteViolation raised
    """

    def test_cso_cannot_write_execution_state(self):
        """CSO blocked from execution_state."""
        from cso import CSOObserver, CSOWriteViolation

        observer = CSOObserver()

        with pytest.raises(CSOWriteViolation):
            observer._guard_write("execution_state", "modify")

    def test_cso_cannot_write_orders(self):
        """CSO blocked from orders."""
        from cso import CSOObserver, CSOWriteViolation

        observer = CSOObserver()

        with pytest.raises(CSOWriteViolation):
            observer._guard_write("orders", "submit")

    def test_cso_cannot_write_positions(self):
        """CSO blocked from positions."""
        from cso import CSOObserver, CSOWriteViolation

        observer = CSOObserver()

        with pytest.raises(CSOWriteViolation):
            observer._guard_write("positions", "open")


class TestV2CSO003BeadMutation:
    """
    V2-CSO-003: bead_mutation

    Attack: Mutate bead after creation
    Detection: ImmutabilityViolation raised
    """

    def test_bead_id_immutable(self):
        """Cannot change bead_id."""
        from cso import BeadFactory, ImmutabilityViolation

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="LONG", confidence=0.8, gate_result={}, state_hash="abc123"
        )

        with pytest.raises(ImmutabilityViolation):
            bead.bead_id = "HACKED"

    def test_content_immutable(self):
        """Cannot change content."""
        from cso import BeadFactory, ImmutabilityViolation

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="LONG", confidence=0.8, gate_result={}, state_hash="abc123"
        )

        with pytest.raises(ImmutabilityViolation):
            bead.content = {"direction": "SHORT"}

    def test_status_immutable(self):
        """Cannot change status directly."""
        from cso import BeadFactory, BeadStatus, ImmutabilityViolation

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="LONG", confidence=0.8, gate_result={}, state_hash="abc123"
        )

        with pytest.raises(ImmutabilityViolation):
            bead.status = BeadStatus.CERTIFIED


class TestCSOChaosSummary:
    """Summary test for CSO chaos vectors."""

    def test_all_cso_vectors_pass(self):
        """Run all CSO chaos vectors."""
        results = {
            "V2-CSO-001": False,  # heresy_hallucination
            "V2-CSO-002": False,  # cso_exec_write
            "V2-CSO-003": False,  # bead_mutation
        }

        # V2-CSO-001: comprehension hash works
        from cso import BeadFactory

        factory = BeadFactory(source_module="test")
        b1 = factory.create_decision_bead("EUR", "LONG", 0.8, {}, "a")
        b2 = factory.create_decision_bead("EUR", "SHORT", 0.8, {}, "a")
        results["V2-CSO-001"] = b1.comprehension_hash != b2.comprehension_hash

        # V2-CSO-002: write blocked
        from cso import CSOObserver, CSOWriteViolation

        observer = CSOObserver()
        try:
            observer._guard_write("execution_state", "x")
        except CSOWriteViolation:
            results["V2-CSO-002"] = True

        # V2-CSO-003: mutation blocked
        from cso import ImmutabilityViolation

        b = factory.create_decision_bead("EUR", "LONG", 0.8, {}, "a")
        try:
            b.bead_id = "HACKED"
        except ImmutabilityViolation:
            results["V2-CSO-003"] = True

        # All must pass
        passed = sum(results.values())
        total = len(results)

        assert passed == total, f"CSO chaos: {passed}/{total}"
