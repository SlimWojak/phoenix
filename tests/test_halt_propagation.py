#!/usr/bin/env python3
"""
TEST: HALT PROPAGATION
SPRINT: 26.TRACK_B
EXIT_GATE: cascade completes, no orphan halts

PURPOSE:
  Prove halt cascades correctly through dependency graph.
  Validates get_dependents() wiring.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

PHOENIX_ROOT = Path.home() / "phoenix"
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import (
    HaltManager,
    HaltMesh,
    AckReceipt,
    LifecycleState,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

def create_test_topology():
    """
    Create test topology:
    
    River → Enrichment → CSO → Execution
    
    Halt at River should cascade to all.
    """
    river = HaltManager(module_id="river")
    enrichment = HaltManager(module_id="enrichment")
    cso = HaltManager(module_id="cso")
    execution = HaltManager(module_id="execution")
    
    # Wire dependencies
    river.register_dependent(
        "enrichment",
        lambda halt_id: enrichment.acknowledge_halt(halt_id)
    )
    enrichment.register_dependent(
        "cso",
        lambda halt_id: cso.acknowledge_halt(halt_id)
    )
    cso.register_dependent(
        "execution",
        lambda halt_id: execution.acknowledge_halt(halt_id)
    )
    
    return {
        'river': river,
        'enrichment': enrichment,
        'cso': cso,
        'execution': execution
    }


# =============================================================================
# TESTS
# =============================================================================

def test_halt_propagation_cascade():
    """Test halt cascades through dependency chain."""
    modules = create_test_topology()
    
    # Trigger halt at river
    result = modules['river'].request_halt()
    assert result.success is True
    
    # Propagate
    cascade = modules['river'].propagate_halt(result.halt_id)
    
    print("\nHalt Propagation Cascade:")
    print(f"  halt_id: {cascade.halt_id}")
    print(f"  propagated_to: {cascade.propagated_to}")
    print(f"  acks_received: {len(cascade.acks_received)}")
    print(f"  acks_failed: {cascade.acks_failed}")
    print(f"  latency: {cascade.total_latency_ms:.3f} ms")
    
    # Verify enrichment was notified
    assert "enrichment" in cascade.propagated_to
    assert len(cascade.acks_received) == 1
    
    # Now propagate from enrichment
    cascade2 = modules['enrichment'].propagate_halt(result.halt_id)
    assert "cso" in cascade2.propagated_to
    
    # And from CSO
    cascade3 = modules['cso'].propagate_halt(result.halt_id)
    assert "execution" in cascade3.propagated_to
    
    print("  cascade_complete: TRUE")


def test_no_orphan_halts():
    """Verify all modules receive halt (no orphans)."""
    modules = create_test_topology()
    
    # Full cascade from river
    result = modules['river'].request_halt()
    modules['river'].propagate_halt(result.halt_id)
    modules['enrichment'].propagate_halt(result.halt_id)
    modules['cso'].propagate_halt(result.halt_id)
    
    # All should be halted
    for name, manager in modules.items():
        assert manager.signal.is_set(), f"{name} not halted (orphan)"
        assert manager.lifecycle_state == LifecycleState.STOPPING
    
    print("\nNo Orphan Halts: VERIFIED")
    print("  All 4 modules received halt signal")


def test_halt_cascade_latency_slo():
    """Test halt cascade completes within SLO (500ms)."""
    modules = create_test_topology()
    
    # Time full cascade
    import time
    start = time.perf_counter_ns()
    
    result = modules['river'].request_halt()
    modules['river'].propagate_halt(result.halt_id)
    modules['enrichment'].propagate_halt(result.halt_id)
    modules['cso'].propagate_halt(result.halt_id)
    
    end = time.perf_counter_ns()
    total_ms = (end - start) / 1_000_000
    
    print(f"\nCascade Latency: {total_ms:.3f} ms")
    print(f"  SLO: 500 ms")
    
    # SLO check (not hard invariant)
    assert total_ms < 500, f"Cascade latency {total_ms:.3f}ms exceeds SLO"


def test_get_dependents_returns_correct_list():
    """Test get_dependents() returns correct modules."""
    modules = create_test_topology()
    
    assert modules['river'].get_dependents() == ['enrichment']
    assert modules['enrichment'].get_dependents() == ['cso']
    assert modules['cso'].get_dependents() == ['execution']
    assert modules['execution'].get_dependents() == []
    
    print("\nget_dependents() Validation: PASS")


def test_ack_receipt_structure():
    """Test AckReceipt contains required fields."""
    modules = create_test_topology()
    
    result = modules['river'].request_halt()
    cascade = modules['river'].propagate_halt(result.halt_id)
    
    assert len(cascade.acks_received) > 0
    ack = cascade.acks_received[0]
    
    # Verify structure
    assert hasattr(ack, 'module_id')
    assert hasattr(ack, 'ack')
    assert hasattr(ack, 'module_state')
    assert hasattr(ack, 'timestamp')
    
    assert ack.ack is True
    assert ack.module_state == LifecycleState.STOPPING
    
    print("\nAckReceipt Structure: VALID")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HALT PROPAGATION TEST")
    print("=" * 60)
    
    try:
        test_halt_propagation_cascade()
        test_no_orphan_halts()
        test_halt_cascade_latency_slo()
        test_get_dependents_returns_correct_list()
        test_ack_receipt_structure()
        
        print("\n" + "=" * 60)
        print("VERDICT: PASS")
        print("  - Cascade completes through all modules")
        print("  - No orphan halts")
        print("  - Latency within SLO")
        print("=" * 60)
        
        sys.exit(0)
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print("VERDICT: FAIL")
        print(f"  {e}")
        print("=" * 60)
        sys.exit(1)
