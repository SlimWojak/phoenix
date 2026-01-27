"""
Test Bead Immutability — Verify INV-DYNASTY-5.

SPRINT: S27.0
EXIT_GATE: bead_immutability
INVARIANT: INV-DYNASTY-5
"""

import sys
from pathlib import Path

import pytest

PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class TestBeadImmutability:
    """Test beads are immutable after creation."""

    def test_cannot_change_bead_id(self):
        """Cannot change bead_id after creation."""
        from cso import BeadFactory, ImmutabilityViolation

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="LONG", confidence=0.8, gate_result={}, state_hash="abc123"
        )

        original_id = bead.bead_id

        with pytest.raises(ImmutabilityViolation) as exc:
            bead.bead_id = "MODIFIED-ID"

        assert exc.value.bead_id == original_id
        assert exc.value.field == "bead_id"

    def test_cannot_change_status(self):
        """Cannot change status after creation."""
        from cso import BeadFactory, BeadStatus, ImmutabilityViolation

        factory = BeadFactory(source_module="test")
        bead = factory.create_observation_bead(
            symbol="EURUSD", observation_type="fvg", details={}, state_hash="abc123"
        )

        with pytest.raises(ImmutabilityViolation) as exc:
            bead.status = BeadStatus.CERTIFIED

        assert exc.value.field == "status"

    def test_cannot_change_content(self):
        """Cannot change content after creation."""
        from cso import BeadFactory, ImmutabilityViolation

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="SHORT", confidence=0.7, gate_result={}, state_hash="abc123"
        )

        with pytest.raises(ImmutabilityViolation) as exc:
            bead.content = {"direction": "LONG"}  # Try to flip direction

        assert exc.value.field == "content"

    def test_cannot_change_symbol(self):
        """Cannot change symbol after creation."""
        from cso import BeadFactory, ImmutabilityViolation

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="LONG", confidence=0.8, gate_result={}, state_hash="abc123"
        )

        with pytest.raises(ImmutabilityViolation):
            bead.symbol = "GBPUSD"

    def test_cannot_change_comprehension_hash(self):
        """Cannot change comprehension_hash after creation."""
        from cso import BeadFactory, ImmutabilityViolation

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="LONG", confidence=0.8, gate_result={}, state_hash="abc123"
        )

        with pytest.raises(ImmutabilityViolation):
            bead.comprehension_hash = "fake_hash_12345"

    def test_outcome_can_be_set_once(self):
        """Outcome CAN be set once (but not modified)."""
        from cso import BeadFactory

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="LONG", confidence=0.8, gate_result={}, state_hash="abc123"
        )

        # Should be None initially
        assert bead.outcome is None

        # Can set once
        bead.outcome = {"result": "WIN", "pips": 25}

        assert bead.outcome == {"result": "WIN", "pips": 25}
        assert bead.outcome_set_at is not None

    def test_outcome_cannot_be_modified(self):
        """Outcome cannot be modified after being set."""
        from cso import BeadFactory, ImmutabilityViolation

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="LONG", confidence=0.8, gate_result={}, state_hash="abc123"
        )

        # Set outcome
        bead.outcome = {"result": "WIN", "pips": 25}

        # Try to modify
        with pytest.raises(ImmutabilityViolation):
            bead.outcome = {"result": "LOSS", "pips": -10}


class TestBeadSerialization:
    """Test bead serialization."""

    def test_to_dict_produces_valid_dict(self):
        """to_dict produces valid dictionary."""
        from cso import BeadFactory

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD",
            direction="LONG",
            confidence=0.8,
            gate_result={"q1": True},
            state_hash="abc123",
        )

        d = bead.to_dict()

        assert isinstance(d, dict)
        assert d["bead_id"] == bead.bead_id
        assert d["status"] == "DRAFT"
        assert d["symbol"] == "EURUSD"

    def test_serialization_deterministic(self):
        """Same bead produces same serialization."""
        from cso import BeadFactory

        factory = BeadFactory(source_module="test")
        bead = factory.create_decision_bead(
            symbol="EURUSD", direction="LONG", confidence=0.8, gate_result={}, state_hash="abc123"
        )

        d1 = bead.to_dict()
        d2 = bead.to_dict()

        # Remove timestamps for comparison
        d1.pop("created_at")
        d2.pop("created_at")

        assert d1 == d2
