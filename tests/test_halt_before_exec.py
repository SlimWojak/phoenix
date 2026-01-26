"""
Test Halt Before Exec — Verify INV-GOV-HALT-BEFORE-ACTION.

SPRINT: S27.0
EXIT_GATE: halt_first_proven
INVARIANT: INV-GOV-HALT-BEFORE-ACTION
"""

import pytest
import sys
from pathlib import Path

PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class TestHaltBeforeExec:
    """Test halt-first pattern enforcement."""
    
    def test_action_without_check_raises(self):
        """
        Action without halt check raises HaltGateViolation.
        
        EXIT_GATE: halt_first_proven
        """
        from execution import HaltGate, HaltGateViolation
        
        gate = HaltGate(halt_signal_fn=lambda: False)
        
        # Try to verify without checking first
        with pytest.raises(HaltGateViolation) as exc:
            gate.verify_checked('submit_order')
        
        assert exc.value.action == 'submit_order'
        assert 'INV-GOV-HALT-BEFORE-ACTION' in str(exc.value)
    
    def test_check_before_allows_action(self):
        """Check before action allows proceeding."""
        from execution import HaltGate
        
        gate = HaltGate(halt_signal_fn=lambda: False)
        
        # Check first
        result = gate.check_before('submit_order')
        
        assert result.checked is True
        assert result.halted is False
        
        # Now verify passes
        gate.verify_checked('submit_order')  # Should not raise
    
    def test_halted_blocks_action(self):
        """Active halt blocks action."""
        from execution import HaltGate, HaltBlockedError
        
        gate = HaltGate(halt_signal_fn=lambda: True)  # HALTED
        
        with pytest.raises(HaltBlockedError) as exc:
            gate.check_before('submit_order')
        
        assert exc.value.action == 'submit_order'
    
    def test_wrong_action_fails_verify(self):
        """Checking one action then verifying different fails."""
        from execution import HaltGate, HaltGateViolation
        
        gate = HaltGate(halt_signal_fn=lambda: False)
        
        # Check for action A
        gate.check_before('action_a')
        
        # Verify for action B (different)
        with pytest.raises(HaltGateViolation):
            gate.verify_checked('action_b')
    
    def test_check_time_measured(self):
        """Check time is measured."""
        from execution import HaltGate
        
        gate = HaltGate(halt_signal_fn=lambda: False)
        result = gate.check_before('test_action')
        
        assert result.check_time_ms >= 0
        assert result.check_time_ms < 50  # Should be <50ms


class TestExecutionGateCoordinator:
    """Test execution gate coordinator."""
    
    def test_intent_passes_when_not_halted(self):
        """Intent passes when halt signal clear."""
        from execution import (
            ExecutionGateCoordinator,
            IntentFactory,
            Direction
        )
        
        coordinator = ExecutionGateCoordinator(halt_signal_fn=lambda: False)
        factory = IntentFactory(source_module='test')
        
        intent = factory.create_entry_intent(
            symbol='EURUSD',
            direction=Direction.LONG,
            size=0.01,
            state_hash='abc123'
        )
        
        result = coordinator.gate_intent(intent)
        
        assert result is True
        assert coordinator.get_passed_count() == 1
        assert coordinator.get_blocked_count() == 0
    
    def test_intent_blocked_when_halted(self):
        """Intent blocked when halt signal active."""
        from execution import (
            ExecutionGateCoordinator,
            IntentFactory,
            Direction
        )
        
        coordinator = ExecutionGateCoordinator(halt_signal_fn=lambda: True)
        factory = IntentFactory(source_module='test')
        
        intent = factory.create_entry_intent(
            symbol='EURUSD',
            direction=Direction.LONG,
            size=0.01,
            state_hash='abc123'
        )
        
        result = coordinator.gate_intent(intent)
        
        assert result is False
        assert coordinator.get_passed_count() == 0
        assert coordinator.get_blocked_count() == 1


class TestHaltGatedDecorator:
    """Test halt_gated decorator."""
    
    def test_decorator_enforces_check(self):
        """Decorator enforces halt check."""
        from execution import HaltGate, halt_gated, HaltBlockedError
        
        gate = HaltGate(halt_signal_fn=lambda: True)  # HALTED
        
        @halt_gated(gate)
        def test_action():
            return "should not reach here"
        
        with pytest.raises(HaltBlockedError):
            test_action()
    
    def test_decorator_allows_when_clear(self):
        """Decorator allows action when halt clear."""
        from execution import HaltGate, halt_gated
        
        gate = HaltGate(halt_signal_fn=lambda: False)
        
        @halt_gated(gate)
        def test_action():
            return "success"
        
        result = test_action()
        assert result == "success"
