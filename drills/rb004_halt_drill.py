#!/usr/bin/env python3
"""
RB-004 Emergency Halt Drill Script

PURPOSE: Full cycle drill - trigger → verify → lift → verify
INVARIANT: INV-HALT-1 (halt_local < 50ms)

USAGE:
    python drills/rb004_halt_drill.py

This script demonstrates the Python equivalents for:
    ./phoenix kill-flag set --reason="Drill - RB-004"
    ./phoenix kill-flag status
    ./phoenix kill-flag lift --reason="Drill complete"
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from governance.halt import HaltManager, HaltMesh
from governance.types import LifecycleState


def print_status(manager: HaltManager, label: str) -> None:
    """Print current halt status."""
    print(f"\n{'='*60}")
    print(f"STATUS: {label}")
    print(f"{'='*60}")
    print(f"  signal.is_set():   {manager.signal.is_set()}")
    print(f"  signal.halt_id:    {manager.signal.halt_id}")
    print(f"  lifecycle_state:   {manager.lifecycle_state.value}")


def run_drill() -> bool:
    """
    Execute full RB-004 drill cycle.
    
    Returns:
        True if drill passed, False otherwise
    """
    print("\n" + "="*60)
    print("RB-004 EMERGENCY HALT DRILL")
    print("="*60)
    
    # Create a test HaltManager
    manager = HaltManager(module_id="drill_test")
    
    # ==========================================================================
    # PHASE 1: INITIAL STATE
    # ==========================================================================
    print_status(manager, "INITIAL STATE")
    
    assert not manager.signal.is_set(), "Signal should start unset"
    assert manager.lifecycle_state == LifecycleState.RUNNING, "Should start RUNNING"
    print("  ✓ Initial state correct")
    
    # ==========================================================================
    # PHASE 2: TRIGGER HALT
    # ==========================================================================
    print("\n" + "-"*60)
    print("PHASE 2: TRIGGER HALT")
    print("-"*60)
    print("  Equivalent: ./phoenix kill-flag set --reason='Drill - RB-004'")
    
    result = manager.request_halt()
    
    print("\n  HaltSignalSetResult:")
    print(f"    success:    {result.success}")
    print(f"    halt_id:    {result.halt_id}")
    print(f"    latency_ms: {result.latency_ms:.6f}")
    print(f"    timestamp:  {result.timestamp}")
    
    # Verify INV-HALT-1
    if result.latency_ms < 50.0:
        print(f"\n  ✓ INV-HALT-1 PROVEN: {result.latency_ms:.3f}ms < 50ms")
    else:
        print(f"\n  ✗ INV-HALT-1 VIOLATED: {result.latency_ms:.3f}ms >= 50ms")
        return False
    
    print_status(manager, "AFTER HALT TRIGGER")
    
    assert manager.signal.is_set(), "Signal should be set"
    assert manager.lifecycle_state == LifecycleState.STOPPING, "Should be STOPPING"
    print("  ✓ Halt state correct")
    
    # ==========================================================================
    # PHASE 3: VERIFY FAIL-CLOSED
    # ==========================================================================
    print("\n" + "-"*60)
    print("PHASE 3: VERIFY FAIL-CLOSED")
    print("-"*60)
    
    from governance.errors import HaltError
    
    try:
        manager.check_halt()
        print("  ✗ check_halt() should have raised HaltError")
        return False
    except HaltError as e:
        print(f"  ✓ check_halt() raises HaltError: {e}")
    
    # ==========================================================================
    # PHASE 4: LIFT HALT
    # ==========================================================================
    print("\n" + "-"*60)
    print("PHASE 4: LIFT HALT")
    print("-"*60)
    print("  Equivalent: ./phoenix kill-flag lift --reason='Drill complete'")
    
    manager.clear_halt()
    
    print_status(manager, "AFTER HALT LIFT")
    
    assert not manager.signal.is_set(), "Signal should be cleared"
    assert manager.lifecycle_state == LifecycleState.RUNNING, "Should be RUNNING"
    print("  ✓ Lift state correct")
    
    # ==========================================================================
    # PHASE 5: VERIFY OPERATIONS RESUME
    # ==========================================================================
    print("\n" + "-"*60)
    print("PHASE 5: VERIFY OPERATIONS RESUME")
    print("-"*60)
    
    try:
        manager.check_halt()  # Should NOT raise
        print("  ✓ check_halt() passes (operations can resume)")
    except HaltError:
        print("  ✗ check_halt() still raising after lift")
        return False
    
    # ==========================================================================
    # DRILL COMPLETE
    # ==========================================================================
    print("\n" + "="*60)
    print("RB-004 DRILL: PASS ✓")
    print("="*60)
    print("\nSUMMARY:")
    print(f"  - Halt trigger latency: {result.latency_ms:.6f}ms")
    print(f"  - INV-HALT-1 proven: {result.latency_ms:.3f}ms < 50ms")
    print("  - Fail-closed behavior verified")
    print("  - Lift mechanism verified")
    print("  - Operations resume verified")
    
    return True


def run_mesh_drill() -> bool:
    """
    Test HaltMesh global halt/clear functionality.
    """
    print("\n" + "="*60)
    print("HALT MESH DRILL (Multi-module)")
    print("="*60)
    
    # Get singleton mesh
    mesh = HaltMesh()
    
    # Create and register multiple managers
    managers = [
        HaltManager(module_id="ibkr_connector"),
        HaltManager(module_id="position_manager"),
        HaltManager(module_id="signalman"),
    ]
    
    for m in managers:
        mesh.register(m)
    
    print(f"\n  Registered {len(managers)} modules in mesh")
    
    # Global halt
    print("\n  Triggering global_halt()...")
    results = mesh.global_halt()
    
    for module_id, result in results.items():
        print(f"    {module_id}: {result.latency_ms:.3f}ms")
    
    # Verify all halted
    for m in managers:
        assert m.signal.is_set(), f"{m.module_id} should be halted"
        assert m.lifecycle_state == LifecycleState.STOPPING
    print("  ✓ All modules halted")
    
    # Clear all
    print("\n  Triggering clear_all()...")
    mesh.clear_all()
    
    # Verify all cleared
    for m in managers:
        assert not m.signal.is_set(), f"{m.module_id} should be cleared"
        assert m.lifecycle_state == LifecycleState.RUNNING
    print("  ✓ All modules cleared")
    
    # Cleanup - deregister
    for m in managers:
        mesh.deregister(m.module_id)
    
    print("\n" + "="*60)
    print("HALT MESH DRILL: PASS ✓")
    print("="*60)
    
    return True


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# RB-004 EMERGENCY HALT DRILL")
    print("# Date: 2026-01-28")
    print("# Sprint: S33 Phase 1 (Track F)")
    print("#"*60)
    
    # Run single manager drill
    single_passed = run_drill()
    
    # Run mesh drill
    mesh_passed = run_mesh_drill()
    
    # Final result
    print("\n" + "#"*60)
    if single_passed and mesh_passed:
        print("# FINAL RESULT: ALL DRILLS PASS ✓")
        print("#"*60)
        sys.exit(0)
    else:
        print("# FINAL RESULT: DRILL FAILED ✗")
        print("#"*60)
        sys.exit(1)
