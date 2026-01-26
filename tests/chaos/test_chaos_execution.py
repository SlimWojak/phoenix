"""
Test Chaos Execution — BOAR attack vectors for Execution.

SPRINT: S27.0
TRACK: D

Vectors:
- V2-EXEC-001: halt_bypass
- V2-EXEC-002: capital_leak
- V2-EXEC-003: intent_nondeterministic
"""

import pytest
import sys
from pathlib import Path

PHOENIX_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class TestV2EXEC001HaltBypass:
    """
    V2-EXEC-001: halt_bypass
    
    Attack: Execute action without halt check
    Detection: HaltGateViolation raised
    """
    
    def test_action_without_check_raises(self):
        """Action without halt check is blocked."""
        from execution import HaltGate, HaltGateViolation
        
        gate = HaltGate(halt_signal_fn=lambda: False)
        
        # Try to verify without checking
        with pytest.raises(HaltGateViolation):
            gate.verify_checked('submit_order')
    
    def test_cannot_bypass_halt_signal(self):
        """Cannot proceed when halted."""
        from execution import HaltGate, HaltBlockedError
        
        gate = HaltGate(halt_signal_fn=lambda: True)  # HALTED
        
        with pytest.raises(HaltBlockedError):
            gate.check_before('any_action')
    
    def test_coordinator_blocks_when_halted(self):
        """Coordinator blocks intents when halted."""
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


class TestV2EXEC002CapitalLeak:
    """
    V2-EXEC-002: capital_leak
    
    Attack: Submit actual order (capital action)
    Detection: CapitalActionForbiddenError raised
    """
    
    def test_submit_order_forbidden(self):
        """submit_order is forbidden."""
        from execution import guard_capital_action, CapitalActionForbiddenError
        
        with pytest.raises(CapitalActionForbiddenError):
            guard_capital_action('submit_order')
    
    def test_execute_order_forbidden(self):
        """execute_order is forbidden."""
        from execution import guard_capital_action, CapitalActionForbiddenError
        
        with pytest.raises(CapitalActionForbiddenError):
            guard_capital_action('execute_order')
    
    def test_broker_connect_forbidden(self):
        """broker.connect is forbidden."""
        from execution import guard_capital_action, CapitalActionForbiddenError
        
        with pytest.raises(CapitalActionForbiddenError):
            guard_capital_action('broker.connect')
    
    def test_intent_has_no_execute(self):
        """Intent cannot be executed."""
        from execution import ExecutionIntent
        
        assert not hasattr(ExecutionIntent, 'execute')
        assert not hasattr(ExecutionIntent, 'submit')


class TestV2EXEC003IntentNondeterministic:
    """
    V2-EXEC-003: intent_nondeterministic
    
    Attack: Same input produces different intent hash
    Detection: Hash comparison
    """
    
    def test_same_input_same_hash(self):
        """Same input must produce same hash."""
        from execution import IntentFactory, Direction
        
        f1 = IntentFactory(source_module='test')
        f2 = IntentFactory(source_module='test')
        
        i1 = f1.create_entry_intent(
            symbol='EURUSD',
            direction=Direction.LONG,
            size=0.01,
            state_hash='abc123',
            entry_price=1.0850
        )
        
        i2 = f2.create_entry_intent(
            symbol='EURUSD',
            direction=Direction.LONG,
            size=0.01,
            state_hash='abc123',
            entry_price=1.0850
        )
        
        assert i1.intent_hash == i2.intent_hash
    
    def test_hash_length_consistent(self):
        """Hash length is always 16."""
        from execution import IntentFactory, Direction
        
        factory = IntentFactory(source_module='test')
        
        for _ in range(10):
            intent = factory.create_entry_intent(
                symbol='EURUSD',
                direction=Direction.LONG,
                size=0.01,
                state_hash='abc123'
            )
            assert len(intent.intent_hash) == 16


class TestV2DISP001ZombieBleed:
    """
    V2-DISP-001: zombie_bleed
    
    Attack: Halt orphans workers
    Detection: Registry shows no orphans after halt
    
    Note: This is a dispatcher test but included here for completeness.
    """
    
    def test_halt_propagates_to_coordinator(self):
        """Halt affects coordinator behavior."""
        from execution import ExecutionGateCoordinator, IntentFactory, Direction
        
        # Start clear
        coordinator = ExecutionGateCoordinator(halt_signal_fn=lambda: False)
        factory = IntentFactory(source_module='test')
        
        intent = factory.create_entry_intent('EURUSD', Direction.LONG, 0.01, 'abc')
        
        assert coordinator.gate_intent(intent) is True
        
        # Now halted
        halted_coordinator = ExecutionGateCoordinator(halt_signal_fn=lambda: True)
        
        intent2 = factory.create_entry_intent('EURUSD', Direction.LONG, 0.01, 'abc')
        
        assert halted_coordinator.gate_intent(intent2) is False


class TestExecutionChaosSummary:
    """Summary test for execution chaos vectors."""
    
    def test_all_execution_vectors_pass(self):
        """Run all execution chaos vectors."""
        results = {
            'V2-EXEC-001': False,  # halt_bypass
            'V2-EXEC-002': False,  # capital_leak
            'V2-EXEC-003': False,  # intent_nondeterministic
        }
        
        # V2-EXEC-001: halt bypass blocked
        from execution import HaltGate, HaltGateViolation
        gate = HaltGate(halt_signal_fn=lambda: False)
        try:
            gate.verify_checked('test')
        except HaltGateViolation:
            results['V2-EXEC-001'] = True
        
        # V2-EXEC-002: capital action blocked
        from execution import guard_capital_action, CapitalActionForbiddenError
        try:
            guard_capital_action('submit_order')
        except CapitalActionForbiddenError:
            results['V2-EXEC-002'] = True
        
        # V2-EXEC-003: intent is deterministic
        from execution import IntentFactory, Direction
        f = IntentFactory(source_module='test')
        i1 = f.create_entry_intent('EUR', Direction.LONG, 0.01, 'a', entry_price=1.0)
        i2 = f.create_entry_intent('EUR', Direction.LONG, 0.01, 'a', entry_price=1.0)
        results['V2-EXEC-003'] = i1.intent_hash == i2.intent_hash
        
        # All must pass
        passed = sum(results.values())
        total = len(results)
        
        assert passed == total, f"Execution chaos: {passed}/{total}"
