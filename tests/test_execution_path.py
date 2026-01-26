"""
Tests for S28.C Execution Path — T0/T1/T2 Wiring (Mocked).

EXIT GATES:
- GATE_C1_PAPER_TRADES: signal → order → position → P&L cycle complete
- GATE_C2_DETERMINISTIC: same replay = same result (hash match)
- GATE_C3_HALT_RESPECTED: halt stops all execution
- GATE_C4_LIFECYCLE_VALID: only valid state transitions

CONSTRAINTS:
- PAPER_ONLY (no real capital)
- MOCK_SIGNALS (synthetic patterns, NOT Olya methodology)
- Simplified P&L v0 (no fees, no slippage)
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add phoenix to path
phoenix_root = Path(__file__).parent.parent
sys.path.insert(0, str(phoenix_root))

from execution.intent import (
    ExecutionIntent, IntentFactory, IntentType, IntentStatus, Direction
)
from execution.position import (
    Position, PositionState, PositionRegistry, 
    InvalidTransitionError, VALID_TRANSITIONS, validate_transition
)
from execution.broker_stub import (
    PaperBrokerStub, OrderResult, FillType, BrokerHaltedError, PnLCalculator
)
from execution.replay import (
    ReplayHarness, ReplayResult, ReplayState,
    MockSignal, MockSignalGenerator, DeterminismVerifier
)


# =============================================================================
# GATE_C1: PAPER_TRADES — Complete Cycle Test
# =============================================================================

class TestGateC1PaperTrades:
    """
    GATE_C1: Complete cycle: signal → order → position → P&L.
    """
    
    def test_signal_to_order(self):
        """Signal creates intent and submits order."""
        halt_fn = lambda: False
        broker = PaperBrokerStub(halt_check_fn=halt_fn)
        factory = IntentFactory("TEST")
        
        # Create intent from signal
        intent = factory.create_entry_intent(
            symbol="EUR/USD",
            direction=Direction.LONG,
            size=1.0,
            state_hash="TEST-001",
            entry_price=1.1000,
        )
        
        # Submit order
        result = broker.submit_order(intent)
        
        assert result.success, f"Order failed: {result.error}"
        assert result.position_id is not None
        assert result.fill_price == 1.1000
        assert result.fill_size == 1.0
        print("✓ signal_to_order: PASS")
    
    def test_order_to_position(self):
        """Order creates position in correct state."""
        halt_fn = lambda: False
        broker = PaperBrokerStub(halt_check_fn=halt_fn)
        factory = IntentFactory("TEST")
        
        intent = factory.create_entry_intent(
            symbol="EUR/USD",
            direction=Direction.LONG,
            size=1.0,
            state_hash="TEST-002",
            entry_price=1.1000,
        )
        
        result = broker.submit_order(intent)
        position = broker.get_position(result.position_id)
        
        assert position is not None
        assert position.state == PositionState.OPEN
        assert position.entry_price == 1.1000
        assert position.filled_size == 1.0
        print("✓ order_to_position: PASS")
    
    def test_position_to_pnl(self):
        """Position exit calculates P&L correctly."""
        halt_fn = lambda: False
        broker = PaperBrokerStub(halt_check_fn=halt_fn)
        factory = IntentFactory("TEST")
        
        # Entry
        intent = factory.create_entry_intent(
            symbol="EUR/USD",
            direction=Direction.LONG,
            size=1.0,
            state_hash="TEST-003",
            entry_price=1.1000,
        )
        result = broker.submit_order(intent)
        
        # Exit (10 pip profit)
        exit_result = broker.exit_position(
            position_id=result.position_id,
            exit_price=1.1010,
            reason="take_profit"
        )
        
        assert exit_result.success
        # P&L = (1.1010 - 1.1000) * 1.0 * 1 = 0.001
        assert abs(exit_result.realized_pnl - 0.001) < 0.0001
        print(f"✓ position_to_pnl: PASS (P&L={exit_result.realized_pnl})")
    
    def test_full_cycle(self):
        """Complete signal → order → position → P&L cycle."""
        halt_fn = lambda: False
        broker = PaperBrokerStub(halt_check_fn=halt_fn)
        factory = IntentFactory("TEST")
        
        # Simulate trading cycle
        trades = [
            {"direction": Direction.LONG, "entry": 1.1000, "exit": 1.1020},
            {"direction": Direction.SHORT, "entry": 1.1020, "exit": 1.1000},
            {"direction": Direction.LONG, "entry": 1.1000, "exit": 1.0990},  # Loss
        ]
        
        for i, trade in enumerate(trades):
            intent = factory.create_entry_intent(
                symbol="EUR/USD",
                direction=trade["direction"],
                size=1.0,
                state_hash=f"CYCLE-{i}",
                entry_price=trade["entry"],
            )
            
            order_result = broker.submit_order(intent)
            assert order_result.success
            
            exit_result = broker.exit_position(
                position_id=order_result.position_id,
                exit_price=trade["exit"]
            )
            assert exit_result.success
        
        # Verify total P&L
        pnl = broker.get_total_pnl()
        # Trade 1: +0.002, Trade 2: +0.002, Trade 3: -0.001
        expected_pnl = 0.002 + 0.002 + (-0.001)
        assert abs(pnl['total'] - expected_pnl) < 0.0001
        
        print(f"✓ full_cycle: PASS (Total P&L={pnl['total']:.5f})")
        return True


# =============================================================================
# GATE_C2: DETERMINISTIC — Same Replay = Same Result
# =============================================================================

class TestGateC2Deterministic:
    """
    GATE_C2: Same replay = same result.
    Proven via hash comparison.
    """
    
    def test_deterministic_replay(self):
        """Run replay twice, verify identical state hash."""
        signals = [
            MockSignal("S1", datetime.now(timezone.utc), "ENTRY_LONG", "TEST/USD", 1.0, 1.0),
            MockSignal("S2", datetime.now(timezone.utc), "EXIT", "TEST/USD", 1.01),
            MockSignal("S3", datetime.now(timezone.utc), "ENTRY_SHORT", "TEST/USD", 1.01, 1.0),
            MockSignal("S4", datetime.now(timezone.utc), "EXIT", "TEST/USD", 0.99),
        ]
        
        # Run 1
        harness1 = ReplayHarness()
        result1 = harness1.run(signals)
        
        # Run 2
        harness2 = ReplayHarness()
        result2 = harness2.run(signals)
        
        # Compare hashes
        assert result1.state_hash == result2.state_hash, \
            f"Non-deterministic: {result1.state_hash} != {result2.state_hash}"
        
        # Compare P&L
        assert abs(result1.total_pnl - result2.total_pnl) < 0.0001
        
        print(f"✓ deterministic_replay: PASS (hash={result1.state_hash})")
        return True
    
    def test_determinism_verifier(self):
        """Use DeterminismVerifier across multiple runs."""
        signals = MockSignalGenerator().generate_fixed_pattern(count=5)
        
        def harness_factory():
            return ReplayHarness()
        
        verification = DeterminismVerifier.verify(
            harness_factory=harness_factory,
            signals=signals,
            runs=3
        )
        
        assert verification['deterministic'], \
            f"Non-deterministic: {verification['unique_hashes']}"
        
        print(f"✓ determinism_verifier: PASS ({len(verification['runs'])} runs, 1 hash)")
        return True
    
    def test_intent_hash_deterministic(self):
        """Same intent parameters = same hash."""
        factory = IntentFactory("TEST")
        
        intent1 = factory.create_entry_intent(
            symbol="EUR/USD",
            direction=Direction.LONG,
            size=1.0,
            state_hash="FIXED-HASH",
            entry_price=1.1000,
        )
        
        factory2 = IntentFactory("TEST")
        factory2._counter = 0  # Reset counter
        
        intent2 = factory2.create_entry_intent(
            symbol="EUR/USD",
            direction=Direction.LONG,
            size=1.0,
            state_hash="FIXED-HASH",
            entry_price=1.1000,
        )
        
        # Intent hash should be same (excludes timestamp and ID)
        assert intent1.intent_hash == intent2.intent_hash
        print(f"✓ intent_hash_deterministic: PASS (hash={intent1.intent_hash})")
        return True


# =============================================================================
# GATE_C3: HALT_RESPECTED — Halt Stops Execution
# =============================================================================

class TestGateC3HaltRespected:
    """
    GATE_C3: Halt stops all execution.
    """
    
    def test_halt_blocks_orders(self):
        """Halt prevents new orders."""
        halted = [False]
        halt_fn = lambda: halted[0]
        
        broker = PaperBrokerStub(halt_check_fn=halt_fn)
        factory = IntentFactory("TEST")
        
        # First order succeeds
        intent1 = factory.create_entry_intent(
            symbol="EUR/USD",
            direction=Direction.LONG,
            size=1.0,
            state_hash="TEST-001",
            entry_price=1.1000,
        )
        result1 = broker.submit_order(intent1)
        assert result1.success
        
        # Trigger halt
        halted[0] = True
        
        # Second order should fail
        intent2 = factory.create_entry_intent(
            symbol="EUR/USD",
            direction=Direction.LONG,
            size=1.0,
            state_hash="TEST-002",
            entry_price=1.1000,
        )
        
        try:
            broker.submit_order(intent2)
            assert False, "Order should have been blocked"
        except BrokerHaltedError:
            pass  # Expected
        
        print("✓ halt_blocks_orders: PASS")
        return True
    
    def test_halt_stops_replay(self):
        """Halt stops replay cleanly."""
        signals = MockSignalGenerator().generate_fixed_pattern(count=10)
        
        # Inject halt at signal 5
        harness = ReplayHarness()
        result = harness.run(signals, halt_at_signal=5)
        
        assert result.state == ReplayState.HALTED
        assert result.halted_at_signal == 5
        assert result.signals_processed <= 5
        
        print(f"✓ halt_stops_replay: PASS (halted at signal {result.halted_at_signal})")
        return True
    
    def test_halt_halts_positions(self):
        """Halt transitions active positions to HALTED."""
        halt_fn = lambda: False
        broker = PaperBrokerStub(halt_check_fn=halt_fn)
        factory = IntentFactory("TEST")
        
        # Open position
        intent = factory.create_entry_intent(
            symbol="EUR/USD",
            direction=Direction.LONG,
            size=1.0,
            state_hash="TEST-001",
            entry_price=1.1000,
        )
        result = broker.submit_order(intent)
        position = broker.get_position(result.position_id)
        assert position.state == PositionState.OPEN
        
        # Trigger halt
        count = broker.on_halt("MANUAL-HALT-001")
        
        # Position should be HALTED
        assert count == 1
        assert position.state == PositionState.HALTED
        
        print(f"✓ halt_halts_positions: PASS ({count} position halted)")
        return True
    
    def test_halt_blocks_exits(self):
        """Halt prevents position exits."""
        halted = [False]
        halt_fn = lambda: halted[0]
        
        broker = PaperBrokerStub(halt_check_fn=halt_fn)
        factory = IntentFactory("TEST")
        
        # Open position
        intent = factory.create_entry_intent(
            symbol="EUR/USD",
            direction=Direction.LONG,
            size=1.0,
            state_hash="TEST-001",
            entry_price=1.1000,
        )
        result = broker.submit_order(intent)
        
        # Trigger halt
        halted[0] = True
        
        # Exit should fail
        try:
            broker.exit_position(result.position_id, exit_price=1.1010)
            assert False, "Exit should have been blocked"
        except BrokerHaltedError:
            pass  # Expected
        
        print("✓ halt_blocks_exits: PASS")
        return True


# =============================================================================
# GATE_C4: LIFECYCLE_VALID — Valid Transitions Only
# =============================================================================

class TestGateC4LifecycleValid:
    """
    GATE_C4: Only valid state transitions allowed.
    INV-EXEC-LIFECYCLE-1 enforced.
    """
    
    def test_valid_transitions_defined(self):
        """All states have defined transitions."""
        for state in PositionState:
            assert state in VALID_TRANSITIONS
        print("✓ valid_transitions_defined: PASS")
    
    def test_terminal_states_no_transitions(self):
        """Terminal states (CLOSED, HALTED) have no outgoing transitions."""
        assert VALID_TRANSITIONS[PositionState.CLOSED] == set()
        assert VALID_TRANSITIONS[PositionState.HALTED] == set()
        print("✓ terminal_states_no_transitions: PASS")
    
    def test_valid_transition_pending_to_open(self):
        """PENDING → OPEN is valid."""
        assert validate_transition(PositionState.PENDING, PositionState.OPEN)
        print("✓ valid_transition_pending_to_open: PASS")
    
    def test_invalid_transition_closed_to_open(self):
        """CLOSED → OPEN is invalid."""
        assert not validate_transition(PositionState.CLOSED, PositionState.OPEN)
        print("✓ invalid_transition_closed_to_open: PASS")
    
    def test_position_rejects_invalid_transition(self):
        """Position raises on invalid transition."""
        position = Position(
            position_id="TEST-001",
            intent_id="INT-001",
            state=PositionState.CLOSED,
            symbol="EUR/USD",
            direction="LONG",
        )
        
        try:
            position.transition_to(PositionState.OPEN, "invalid")
            assert False, "Should have raised InvalidTransitionError"
        except InvalidTransitionError as e:
            assert e.from_state == PositionState.CLOSED
            assert e.to_state == PositionState.OPEN
        
        print("✓ position_rejects_invalid_transition: PASS")
    
    def test_full_lifecycle(self):
        """Test complete lifecycle: PENDING → OPEN → CLOSED."""
        position = Position(
            position_id="TEST-001",
            intent_id="INT-001",
            state=PositionState.PENDING,
            symbol="EUR/USD",
            direction="LONG",
            size=1.0,
        )
        
        # Fill to OPEN
        position.fill(1.1000, 1.0)
        assert position.state == PositionState.OPEN
        
        # Close
        position.close(1.1010, "take_profit")
        assert position.state == PositionState.CLOSED
        assert position.realized_pnl > 0
        
        print(f"✓ full_lifecycle: PASS (P&L={position.realized_pnl})")
        return True
    
    def test_halt_from_any_active_state(self):
        """Halt is valid from any non-terminal state."""
        for state in [PositionState.PENDING, PositionState.OPEN, PositionState.PARTIAL]:
            assert PositionState.HALTED in VALID_TRANSITIONS[state]
        print("✓ halt_from_any_active_state: PASS")


# =============================================================================
# P&L CALCULATOR TESTS (Simplified v0)
# =============================================================================

class TestPnLCalculator:
    """
    Test P&L calculation (simplified v0).
    GPT_LINT L28-C1 compliance: documented as simplified.
    """
    
    def test_long_profit(self):
        """Long position profit calculation."""
        pnl = PnLCalculator.calculate_pnl(
            entry_price=1.1000,
            exit_price=1.1020,
            size=1.0,
            direction="LONG"
        )
        assert abs(pnl - 0.002) < 0.0001
        print(f"✓ long_profit: PASS (P&L={pnl})")
    
    def test_long_loss(self):
        """Long position loss calculation."""
        pnl = PnLCalculator.calculate_pnl(
            entry_price=1.1000,
            exit_price=1.0980,
            size=1.0,
            direction="LONG"
        )
        assert abs(pnl - (-0.002)) < 0.0001
        print(f"✓ long_loss: PASS (P&L={pnl})")
    
    def test_short_profit(self):
        """Short position profit calculation."""
        pnl = PnLCalculator.calculate_pnl(
            entry_price=1.1000,
            exit_price=1.0980,
            size=1.0,
            direction="SHORT"
        )
        assert abs(pnl - 0.002) < 0.0001
        print(f"✓ short_profit: PASS (P&L={pnl})")
    
    def test_short_loss(self):
        """Short position loss calculation."""
        pnl = PnLCalculator.calculate_pnl(
            entry_price=1.1000,
            exit_price=1.1020,
            size=1.0,
            direction="SHORT"
        )
        assert abs(pnl - (-0.002)) < 0.0001
        print(f"✓ short_loss: PASS (P&L={pnl})")
    
    def test_pnl_percent(self):
        """P&L percentage calculation."""
        pct = PnLCalculator.calculate_pnl_percent(
            entry_price=1.1000,
            exit_price=1.1110,  # 1% move
            direction="LONG"
        )
        assert abs(pct - 1.0) < 0.1
        print(f"✓ pnl_percent: PASS ({pct:.2f}%)")


# =============================================================================
# MAIN
# =============================================================================

def run_all_tests() -> dict:
    """Run all exit gate tests."""
    results = {
        'C1_paper_trades': [],
        'C2_deterministic': [],
        'C3_halt_respected': [],
        'C4_lifecycle_valid': [],
        'pnl_calculator': [],
    }
    
    print("=" * 60)
    print("S28.C EXECUTION PATH — EXIT GATE TESTS")
    print("=" * 60)
    
    # GATE C1: Paper Trades
    print("\n--- GATE_C1: PAPER_TRADES ---")
    c1 = TestGateC1PaperTrades()
    try:
        c1.test_signal_to_order()
        results['C1_paper_trades'].append(('signal_to_order', True))
    except Exception as e:
        results['C1_paper_trades'].append(('signal_to_order', False, str(e)))
        print(f"✗ signal_to_order: FAIL ({e})")
    
    try:
        c1.test_order_to_position()
        results['C1_paper_trades'].append(('order_to_position', True))
    except Exception as e:
        results['C1_paper_trades'].append(('order_to_position', False, str(e)))
        print(f"✗ order_to_position: FAIL ({e})")
    
    try:
        c1.test_position_to_pnl()
        results['C1_paper_trades'].append(('position_to_pnl', True))
    except Exception as e:
        results['C1_paper_trades'].append(('position_to_pnl', False, str(e)))
        print(f"✗ position_to_pnl: FAIL ({e})")
    
    try:
        c1.test_full_cycle()
        results['C1_paper_trades'].append(('full_cycle', True))
    except Exception as e:
        results['C1_paper_trades'].append(('full_cycle', False, str(e)))
        print(f"✗ full_cycle: FAIL ({e})")
    
    # GATE C2: Deterministic
    print("\n--- GATE_C2: DETERMINISTIC ---")
    c2 = TestGateC2Deterministic()
    try:
        c2.test_deterministic_replay()
        results['C2_deterministic'].append(('deterministic_replay', True))
    except Exception as e:
        results['C2_deterministic'].append(('deterministic_replay', False, str(e)))
        print(f"✗ deterministic_replay: FAIL ({e})")
    
    try:
        c2.test_determinism_verifier()
        results['C2_deterministic'].append(('determinism_verifier', True))
    except Exception as e:
        results['C2_deterministic'].append(('determinism_verifier', False, str(e)))
        print(f"✗ determinism_verifier: FAIL ({e})")
    
    try:
        c2.test_intent_hash_deterministic()
        results['C2_deterministic'].append(('intent_hash_deterministic', True))
    except Exception as e:
        results['C2_deterministic'].append(('intent_hash_deterministic', False, str(e)))
        print(f"✗ intent_hash_deterministic: FAIL ({e})")
    
    # GATE C3: Halt Respected
    print("\n--- GATE_C3: HALT_RESPECTED ---")
    c3 = TestGateC3HaltRespected()
    try:
        c3.test_halt_blocks_orders()
        results['C3_halt_respected'].append(('halt_blocks_orders', True))
    except Exception as e:
        results['C3_halt_respected'].append(('halt_blocks_orders', False, str(e)))
        print(f"✗ halt_blocks_orders: FAIL ({e})")
    
    try:
        c3.test_halt_stops_replay()
        results['C3_halt_respected'].append(('halt_stops_replay', True))
    except Exception as e:
        results['C3_halt_respected'].append(('halt_stops_replay', False, str(e)))
        print(f"✗ halt_stops_replay: FAIL ({e})")
    
    try:
        c3.test_halt_halts_positions()
        results['C3_halt_respected'].append(('halt_halts_positions', True))
    except Exception as e:
        results['C3_halt_respected'].append(('halt_halts_positions', False, str(e)))
        print(f"✗ halt_halts_positions: FAIL ({e})")
    
    try:
        c3.test_halt_blocks_exits()
        results['C3_halt_respected'].append(('halt_blocks_exits', True))
    except Exception as e:
        results['C3_halt_respected'].append(('halt_blocks_exits', False, str(e)))
        print(f"✗ halt_blocks_exits: FAIL ({e})")
    
    # GATE C4: Lifecycle Valid
    print("\n--- GATE_C4: LIFECYCLE_VALID ---")
    c4 = TestGateC4LifecycleValid()
    try:
        c4.test_valid_transitions_defined()
        results['C4_lifecycle_valid'].append(('valid_transitions_defined', True))
    except Exception as e:
        results['C4_lifecycle_valid'].append(('valid_transitions_defined', False, str(e)))
        print(f"✗ valid_transitions_defined: FAIL ({e})")
    
    try:
        c4.test_terminal_states_no_transitions()
        results['C4_lifecycle_valid'].append(('terminal_states_no_transitions', True))
    except Exception as e:
        results['C4_lifecycle_valid'].append(('terminal_states_no_transitions', False, str(e)))
        print(f"✗ terminal_states_no_transitions: FAIL ({e})")
    
    try:
        c4.test_valid_transition_pending_to_open()
        results['C4_lifecycle_valid'].append(('valid_transition_pending_to_open', True))
    except Exception as e:
        results['C4_lifecycle_valid'].append(('valid_transition_pending_to_open', False, str(e)))
        print(f"✗ valid_transition_pending_to_open: FAIL ({e})")
    
    try:
        c4.test_invalid_transition_closed_to_open()
        results['C4_lifecycle_valid'].append(('invalid_transition_closed_to_open', True))
    except Exception as e:
        results['C4_lifecycle_valid'].append(('invalid_transition_closed_to_open', False, str(e)))
        print(f"✗ invalid_transition_closed_to_open: FAIL ({e})")
    
    try:
        c4.test_position_rejects_invalid_transition()
        results['C4_lifecycle_valid'].append(('position_rejects_invalid_transition', True))
    except Exception as e:
        results['C4_lifecycle_valid'].append(('position_rejects_invalid_transition', False, str(e)))
        print(f"✗ position_rejects_invalid_transition: FAIL ({e})")
    
    try:
        c4.test_full_lifecycle()
        results['C4_lifecycle_valid'].append(('full_lifecycle', True))
    except Exception as e:
        results['C4_lifecycle_valid'].append(('full_lifecycle', False, str(e)))
        print(f"✗ full_lifecycle: FAIL ({e})")
    
    try:
        c4.test_halt_from_any_active_state()
        results['C4_lifecycle_valid'].append(('halt_from_any_active_state', True))
    except Exception as e:
        results['C4_lifecycle_valid'].append(('halt_from_any_active_state', False, str(e)))
        print(f"✗ halt_from_any_active_state: FAIL ({e})")
    
    # P&L Calculator
    print("\n--- P&L CALCULATOR (v0 SIMPLIFIED) ---")
    pnl = TestPnLCalculator()
    try:
        pnl.test_long_profit()
        results['pnl_calculator'].append(('long_profit', True))
    except Exception as e:
        results['pnl_calculator'].append(('long_profit', False, str(e)))
        print(f"✗ long_profit: FAIL ({e})")
    
    try:
        pnl.test_long_loss()
        results['pnl_calculator'].append(('long_loss', True))
    except Exception as e:
        results['pnl_calculator'].append(('long_loss', False, str(e)))
        print(f"✗ long_loss: FAIL ({e})")
    
    try:
        pnl.test_short_profit()
        results['pnl_calculator'].append(('short_profit', True))
    except Exception as e:
        results['pnl_calculator'].append(('short_profit', False, str(e)))
        print(f"✗ short_profit: FAIL ({e})")
    
    try:
        pnl.test_short_loss()
        results['pnl_calculator'].append(('short_loss', True))
    except Exception as e:
        results['pnl_calculator'].append(('short_loss', False, str(e)))
        print(f"✗ short_loss: FAIL ({e})")
    
    try:
        pnl.test_pnl_percent()
        results['pnl_calculator'].append(('pnl_percent', True))
    except Exception as e:
        results['pnl_calculator'].append(('pnl_percent', False, str(e)))
        print(f"✗ pnl_percent: FAIL ({e})")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    total_pass = 0
    total_fail = 0
    
    for gate, tests in results.items():
        passed = sum(1 for t in tests if t[1])
        failed = len(tests) - passed
        total_pass += passed
        total_fail += failed
        status = "PASS" if failed == 0 else "FAIL"
        print(f"{gate}: {passed}/{len(tests)} ({status})")
    
    print("-" * 60)
    print(f"TOTAL: {total_pass}/{total_pass + total_fail}")
    print(f"VERDICT: {'PASS' if total_fail == 0 else 'FAIL'}")
    
    return results


if __name__ == "__main__":
    run_all_tests()
