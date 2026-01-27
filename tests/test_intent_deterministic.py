"""
Test Intent Deterministic — Verify INV-CONTRACT-1.

SPRINT: S27.0
EXIT_GATE: intent_deterministic
INVARIANT: INV-CONTRACT-1
"""

import sys
from pathlib import Path

import pytest

PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class TestIntentDeterministic:
    """Test intent hash is deterministic."""

    def test_same_input_same_hash(self):
        """
        Same input produces same intent hash.

        EXIT_GATE: intent_deterministic
        INV-CONTRACT-1
        """
        from execution import Direction, IntentFactory

        factory1 = IntentFactory(source_module="test")
        factory2 = IntentFactory(source_module="test")

        # Create with same parameters
        intent1 = factory1.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.LONG,
            size=0.01,
            state_hash="abc123",
            entry_price=1.0850,
            stop_loss=1.0800,
            take_profit=1.0950,
        )

        intent2 = factory2.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.LONG,
            size=0.01,
            state_hash="abc123",
            entry_price=1.0850,
            stop_loss=1.0800,
            take_profit=1.0950,
        )

        # Hashes should be identical
        assert intent1.intent_hash == intent2.intent_hash

    def test_different_symbol_different_hash(self):
        """Different symbol produces different hash."""
        from execution import Direction, IntentFactory

        factory = IntentFactory(source_module="test")

        intent1 = factory.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.LONG,
            size=0.01,
            state_hash="abc123",
        )

        intent2 = factory.create_entry_intent(
            symbol="GBPUSD",  # Different symbol
            direction=Direction.LONG,
            size=0.01,
            state_hash="abc123",
        )

        assert intent1.intent_hash != intent2.intent_hash

    def test_different_direction_different_hash(self):
        """Different direction produces different hash."""
        from execution import Direction, IntentFactory

        factory = IntentFactory(source_module="test")

        intent1 = factory.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.LONG,
            size=0.01,
            state_hash="abc123",
        )

        intent2 = factory.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.SHORT,  # Different direction
            size=0.01,
            state_hash="abc123",
        )

        assert intent1.intent_hash != intent2.intent_hash

    def test_different_size_different_hash(self):
        """Different size produces different hash."""
        from execution import Direction, IntentFactory

        factory = IntentFactory(source_module="test")

        intent1 = factory.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.LONG,
            size=0.01,
            state_hash="abc123",
        )

        intent2 = factory.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.LONG,
            size=0.02,  # Different size
            state_hash="abc123",
        )

        assert intent1.intent_hash != intent2.intent_hash

    def test_hash_length_consistent(self):
        """Hash length is consistent (16 chars)."""
        from execution import Direction, IntentFactory

        factory = IntentFactory(source_module="test")

        intent = factory.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.LONG,
            size=0.01,
            state_hash="abc123",
        )

        assert len(intent.intent_hash) == 16


class TestIntentImmutability:
    """Test intent immutability."""

    def test_cannot_modify_symbol(self):
        """Cannot modify symbol after creation."""
        from execution import Direction, IntentFactory, IntentMutationError

        factory = IntentFactory(source_module="test")
        intent = factory.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.LONG,
            size=0.01,
            state_hash="abc123",
        )

        with pytest.raises(IntentMutationError):
            intent.symbol = "GBPUSD"

    def test_cannot_modify_size(self):
        """Cannot modify size after creation."""
        from execution import Direction, IntentFactory, IntentMutationError

        factory = IntentFactory(source_module="test")
        intent = factory.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.LONG,
            size=0.01,
            state_hash="abc123",
        )

        with pytest.raises(IntentMutationError):
            intent.size = 0.05

    def test_status_update_creates_new_intent(self):
        """Status update creates new intent (preserves hash)."""
        from execution import Direction, IntentFactory, IntentStatus

        factory = IntentFactory(source_module="test")
        intent1 = factory.create_entry_intent(
            symbol="EURUSD",
            direction=Direction.LONG,
            size=0.01,
            state_hash="abc123",
        )

        intent2 = intent1.update_status(IntentStatus.APPROVED)

        # Different objects
        assert intent1 is not intent2

        # Status changed
        assert intent1.status == IntentStatus.PENDING
        assert intent2.status == IntentStatus.APPROVED

        # Hash preserved
        assert intent1.intent_hash == intent2.intent_hash
