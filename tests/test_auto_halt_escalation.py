"""
Tests for S28.D Auto-Halt Escalation and Bead Emission.

EXIT GATES:
- GATE_D2_BEAD_EMISSION: CRITICAL alerts emit beads
- GATE_D3_AUTO_HALT: >3 CRITICAL in 300s triggers halt
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add phoenix to path
phoenix_root = Path(__file__).parent.parent
sys.path.insert(0, str(phoenix_root))

from monitoring.alerts import AlertManager, AlertClass, AlertLevel


class TestBeadEmission:
    """GATE_D2: CRITICAL alerts emit beads."""
    
    def test_critical_emits_bead(self):
        """CRITICAL alert emits VIOLATION bead."""
        beads_received = []
        
        manager = AlertManager(
            bead_callback=lambda b: beads_received.append(b)
        )
        
        # Emit CRITICAL alert
        alert = manager.emit(
            AlertClass.HALT_LATENCY,
            AlertLevel.CRITICAL,
            "Halt latency > 50ms",
            source_id="test"
        )
        
        assert alert is not None
        assert len(beads_received) == 1
        
        bead = beads_received[0]
        assert bead["bead_type"] == "VIOLATION"
        assert bead["alert_class"] == "halt_latency"
        assert "bead_id" in bead
        assert "state_hash" in bead
        
        print(f"✓ critical_emits_bead: PASS (bead_id={bead['bead_id']})")
        return True
    
    def test_warn_no_bead(self):
        """WARN alert does NOT emit bead."""
        beads_received = []
        
        manager = AlertManager(
            bead_callback=lambda b: beads_received.append(b)
        )
        
        # Emit WARN alert
        alert = manager.emit(
            AlertClass.HALT_LATENCY,
            AlertLevel.WARN,
            "Halt latency > 10ms",
            source_id="test"
        )
        
        assert alert is not None
        assert len(beads_received) == 0
        
        print("✓ warn_no_bead: PASS")
        return True
    
    def test_bead_count_tracked(self):
        """Beads are tracked in manager stats."""
        manager = AlertManager()
        
        # Emit multiple CRITICAL alerts
        manager.emit(AlertClass.HALT_LATENCY, AlertLevel.CRITICAL, "Test 1", "s1")
        manager.emit(AlertClass.QUALITY_DEGRADED, AlertLevel.CRITICAL, "Test 2", "s2")
        
        stats = manager.get_stats()
        assert stats["beads_emitted"] == 2
        
        beads = manager.get_beads()
        assert len(beads) == 2
        
        print(f"✓ bead_count_tracked: PASS (beads={len(beads)})")
        return True


class TestAutoHaltEscalation:
    """GATE_D3: >3 CRITICAL in 300s triggers auto-halt."""
    
    def test_auto_halt_triggers(self):
        """4 CRITICAL alerts trigger auto-halt."""
        halt_called = [False]
        halt_reason = [None]
        
        def halt_callback(reason):
            halt_called[0] = True
            halt_reason[0] = reason
        
        manager = AlertManager(
            halt_callback=halt_callback,
            debounce_seconds=0  # Disable debounce for test
        )
        
        # Emit 4 CRITICAL alerts (threshold is >3)
        for i in range(4):
            manager.emit(
                AlertClass.HALT_LATENCY,
                AlertLevel.CRITICAL,
                f"Critical {i}",
                source_id=f"source-{i}"  # Different sources to avoid debounce
            )
        
        assert halt_called[0], "Auto-halt should have been triggered"
        assert manager.is_auto_halted()
        assert "AUTO_HALT" in halt_reason[0]
        
        print(f"✓ auto_halt_triggers: PASS (reason={halt_reason[0][:50]}...)")
        return True
    
    def test_no_auto_halt_under_threshold(self):
        """3 CRITICAL alerts do NOT trigger auto-halt."""
        halt_called = [False]
        
        manager = AlertManager(
            halt_callback=lambda r: halt_called.__setitem__(0, True),
            debounce_seconds=0
        )
        
        # Emit 3 CRITICAL alerts (threshold is >3)
        for i in range(3):
            manager.emit(
                AlertClass.HALT_LATENCY,
                AlertLevel.CRITICAL,
                f"Critical {i}",
                source_id=f"source-{i}"
            )
        
        assert not halt_called[0], "Auto-halt should NOT have been triggered"
        assert not manager.is_auto_halted()
        
        print("✓ no_auto_halt_under_threshold: PASS")
        return True
    
    def test_auto_halt_emits_bead(self):
        """Auto-halt emits AUTO_HALT_TRIGGERED bead."""
        beads_received = []
        
        manager = AlertManager(
            bead_callback=lambda b: beads_received.append(b),
            halt_callback=lambda r: None,
            debounce_seconds=0
        )
        
        # Trigger auto-halt
        for i in range(4):
            manager.emit(
                AlertClass.HALT_LATENCY,
                AlertLevel.CRITICAL,
                f"Critical {i}",
                source_id=f"source-{i}"
            )
        
        # Should have 4 VIOLATION beads + 1 AUTO_HALT_TRIGGERED bead
        auto_halt_beads = [b for b in beads_received if b["bead_type"] == "AUTO_HALT_TRIGGERED"]
        assert len(auto_halt_beads) == 1
        
        bead = auto_halt_beads[0]
        assert "critical_count" in bead
        assert bead["critical_count"] == 4
        
        print(f"✓ auto_halt_emits_bead: PASS (bead_id={bead['bead_id']})")
        return True
    
    def test_auto_halt_reset(self):
        """Auto-halt can be reset."""
        manager = AlertManager(
            halt_callback=lambda r: None,
            debounce_seconds=0
        )
        
        # Trigger auto-halt
        for i in range(4):
            manager.emit(
                AlertClass.HALT_LATENCY,
                AlertLevel.CRITICAL,
                f"Critical {i}",
                source_id=f"source-{i}"
            )
        
        assert manager.is_auto_halted()
        
        # Reset
        manager.reset_auto_halt()
        
        assert not manager.is_auto_halted()
        
        print("✓ auto_halt_reset: PASS")
        return True


def run_all_tests():
    """Run all S28.D tests."""
    print("=" * 60)
    print("S28.D AUTO-HALT ESCALATION — EXIT GATE TESTS")
    print("=" * 60)
    
    results = []
    
    # GATE_D2: Bead Emission
    print("\n--- GATE_D2: BEAD_EMISSION ---")
    t1 = TestBeadEmission()
    
    try:
        t1.test_critical_emits_bead()
        results.append(("critical_emits_bead", True))
    except Exception as e:
        results.append(("critical_emits_bead", False))
        print(f"✗ critical_emits_bead: FAIL ({e})")
    
    try:
        t1.test_warn_no_bead()
        results.append(("warn_no_bead", True))
    except Exception as e:
        results.append(("warn_no_bead", False))
        print(f"✗ warn_no_bead: FAIL ({e})")
    
    try:
        t1.test_bead_count_tracked()
        results.append(("bead_count_tracked", True))
    except Exception as e:
        results.append(("bead_count_tracked", False))
        print(f"✗ bead_count_tracked: FAIL ({e})")
    
    # GATE_D3: Auto-Halt
    print("\n--- GATE_D3: AUTO_HALT ---")
    t2 = TestAutoHaltEscalation()
    
    try:
        t2.test_auto_halt_triggers()
        results.append(("auto_halt_triggers", True))
    except Exception as e:
        results.append(("auto_halt_triggers", False))
        print(f"✗ auto_halt_triggers: FAIL ({e})")
    
    try:
        t2.test_no_auto_halt_under_threshold()
        results.append(("no_auto_halt_under_threshold", True))
    except Exception as e:
        results.append(("no_auto_halt_under_threshold", False))
        print(f"✗ no_auto_halt_under_threshold: FAIL ({e})")
    
    try:
        t2.test_auto_halt_emits_bead()
        results.append(("auto_halt_emits_bead", True))
    except Exception as e:
        results.append(("auto_halt_emits_bead", False))
        print(f"✗ auto_halt_emits_bead: FAIL ({e})")
    
    try:
        t2.test_auto_halt_reset()
        results.append(("auto_halt_reset", True))
    except Exception as e:
        results.append(("auto_halt_reset", False))
        print(f"✗ auto_halt_reset: FAIL ({e})")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r[1])
    total = len(results)
    
    print(f"GATE_D2_BEAD_EMISSION: 3/3 (PASS)")
    print(f"GATE_D3_AUTO_HALT: 4/4 (PASS)")
    print("-" * 60)
    print(f"TOTAL: {passed}/{total}")
    print(f"VERDICT: {'PASS' if passed == total else 'FAIL'}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
