"""
Test Halt Propagation Multiprocess — Proves halt crosses process boundaries.

SPRINT: 26.TRACK_D
EXIT_GATE: halt_propagation

Tests:
- Halt propagates to all workers via tmux
- Halt cascade completes within INV-HALT-2 (500ms) SLO
- No orphan workers after halt

TEST SCENARIO:
1. Dispatcher spawns 3 mock workers (tmux sessions)
2. Workers are running (sleep commands)
3. Dispatcher.broadcast_halt() triggered
4. Measure: all workers signaled within SLO
"""

import pytest
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# Add phoenix to path
PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

from dispatcher import (
    Dispatcher,
    DispatcherConfig,
    WorkerConfig,
    WorkerType,
    WorkerStatus,
)


# =============================================================================
# CONSTANTS
# =============================================================================

# INV-HALT-2: halt cascade < 500ms
HALT_CASCADE_SLO_MS = 500

# Number of workers to spawn
NUM_WORKERS = 3


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def dispatcher():
    """Create dispatcher for halt propagation tests."""
    config = DispatcherConfig(
        dispatcher_id="halt-prop-test",
        tmux_session_prefix="phoenix-halt-test",
        halt_timeout_ms=HALT_CASCADE_SLO_MS
    )
    d = Dispatcher(config)
    d.start()
    yield d
    # Cleanup regardless of test outcome
    d._tmux.cleanup_orphans()
    d.stop(kill_workers=True)


@pytest.fixture
def worker_config():
    """Worker config for mock workers."""
    return WorkerConfig(
        worker_type=WorkerType.GENERIC,
        name="halt-test-worker",
        command="sleep 300",  # Long-running to ensure it's there
        heartbeat_interval_ms=500,
        heartbeat_timeout_ms=2000
    )


# =============================================================================
# HALT PROPAGATION TESTS
# =============================================================================

class TestHaltPropagation:
    """
    Test halt propagation across process boundaries.
    
    EXIT GATE: halt_propagation
    INVARIANT: INV-HALT-2 (cascade < 500ms)
    """
    
    def test_halt_reaches_all_workers(self, dispatcher, worker_config):
        """
        SCENARIO: Halt reaches all workers
        
        1. Spawn 3 workers
        2. Broadcast halt
        3. Verify all workers signaled
        """
        # Spawn workers
        workers = []
        for i in range(NUM_WORKERS):
            result = dispatcher.spawn_worker(worker_config)
            assert result.success, f"Failed to spawn worker {i}: {result.error}"
            workers.append(result.worker_id)
        
        # Verify all spawned
        assert len(dispatcher.get_all_workers()) == NUM_WORKERS
        
        # Broadcast halt
        halt_result = dispatcher.broadcast_halt("test_halt_propagation")
        
        # Verify halt reached all
        assert halt_result.total_workers == NUM_WORKERS
        assert halt_result.acks_received == NUM_WORKERS, \
            f"Only {halt_result.acks_received}/{NUM_WORKERS} workers acked"
        assert halt_result.all_acked is True
    
    def test_halt_cascade_within_slo(self, dispatcher, worker_config):
        """
        SCENARIO: Halt cascade completes within 500ms
        
        INV-HALT-2: halt_cascade_latency < 500ms
        
        This is the KEY PROOF for Track D.
        """
        # Spawn workers
        for i in range(NUM_WORKERS):
            result = dispatcher.spawn_worker(worker_config)
            assert result.success
        
        # Time the halt broadcast
        start = time.perf_counter()
        halt_result = dispatcher.broadcast_halt("slo_test")
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # PROOF: INV-HALT-2
        assert halt_result.total_latency_ms < HALT_CASCADE_SLO_MS, \
            f"Halt cascade took {halt_result.total_latency_ms:.2f}ms, " \
            f"INV-HALT-2 requires < {HALT_CASCADE_SLO_MS}ms"
        
        # Double-check with wall clock
        assert elapsed_ms < HALT_CASCADE_SLO_MS, \
            f"Wall clock elapsed {elapsed_ms:.2f}ms, expected < {HALT_CASCADE_SLO_MS}ms"
        
        print(f"\nHALT PROPAGATION PROOF:")
        print(f"  Workers: {halt_result.total_workers}")
        print(f"  Cascade latency: {halt_result.total_latency_ms:.2f}ms")
        print(f"  SLO: {HALT_CASCADE_SLO_MS}ms")
        print(f"  STATUS: PASS (INV-HALT-2 satisfied)")
    
    def test_no_orphan_workers_after_halt(self, dispatcher, worker_config):
        """
        SCENARIO: No orphan workers remain after halt + cleanup
        
        INV-DISPATCH-4: no orphan tmux sessions
        """
        # Spawn workers
        for i in range(NUM_WORKERS):
            dispatcher.spawn_worker(worker_config)
        
        # Broadcast halt
        dispatcher.broadcast_halt("orphan_test")
        
        # Kill all workers
        for worker in dispatcher.get_all_workers():
            dispatcher.kill_worker(worker.worker_id)
        
        # Verify no workers in registry
        assert len(dispatcher.get_all_workers()) == 0
        
        # Verify no tmux sessions
        sessions = dispatcher._tmux.list_sessions()
        assert len(sessions) == 0, \
            f"Orphan sessions found: {[s.session_id for s in sessions]}"
    
    def test_halt_with_mixed_worker_states(self, dispatcher, worker_config):
        """
        SCENARIO: Halt works with workers in various states
        
        - Some workers running
        - Some workers degraded (simulated)
        """
        # Spawn workers
        r1 = dispatcher.spawn_worker(worker_config)
        r2 = dispatcher.spawn_worker(worker_config)
        r3 = dispatcher.spawn_worker(worker_config)
        
        # Mark one as degraded
        dispatcher._registry.update_status(r2.worker_id, WorkerStatus.DEGRADED)
        
        # Broadcast halt
        halt_result = dispatcher.broadcast_halt("mixed_state_test")
        
        # Should still reach all
        assert halt_result.total_workers == NUM_WORKERS
    
    def test_halt_per_worker_latency(self, dispatcher, worker_config):
        """
        SCENARIO: Measure per-worker halt latency
        
        Each worker should be signaled quickly.
        """
        # Spawn workers
        for i in range(NUM_WORKERS):
            dispatcher.spawn_worker(worker_config)
        
        # Broadcast halt
        halt_result = dispatcher.broadcast_halt("per_worker_test")
        
        # Check each worker's latency
        for ack in halt_result.worker_acks:
            assert ack.latency_ms < 100, \
                f"Worker {ack.worker_id} ack took {ack.latency_ms:.2f}ms"
            print(f"  {ack.worker_id}: {ack.latency_ms:.2f}ms")


# =============================================================================
# STRESS TESTS
# =============================================================================

class TestHaltStress:
    """Stress tests for halt propagation."""
    
    def test_halt_propagation_many_workers(self, dispatcher):
        """
        SCENARIO: Halt propagation with many workers
        
        Test scaling behavior.
        """
        NUM_STRESS_WORKERS = 5  # Keep reasonable for CI
        
        config = WorkerConfig(
            worker_type=WorkerType.GENERIC,
            command="sleep 300"
        )
        
        # Spawn many workers
        for i in range(NUM_STRESS_WORKERS):
            result = dispatcher.spawn_worker(config)
            assert result.success, f"Failed at worker {i}"
        
        # Broadcast halt
        halt_result = dispatcher.broadcast_halt("stress_test")
        
        # Should complete within SLO even with more workers
        assert halt_result.total_latency_ms < HALT_CASCADE_SLO_MS, \
            f"Stress test failed: {halt_result.total_latency_ms}ms with {NUM_STRESS_WORKERS} workers"
        
        print(f"\nSTRESS TEST:")
        print(f"  Workers: {NUM_STRESS_WORKERS}")
        print(f"  Total latency: {halt_result.total_latency_ms:.2f}ms")
    
    def test_repeated_halt_broadcasts(self, dispatcher, worker_config):
        """
        SCENARIO: Multiple halt broadcasts
        
        Ensure halt mechanism is reusable.
        """
        # Spawn workers
        for i in range(2):
            dispatcher.spawn_worker(worker_config)
        
        # Multiple halts
        for i in range(3):
            result = dispatcher.broadcast_halt(f"repeat_{i}")
            assert result.total_latency_ms < HALT_CASCADE_SLO_MS


# =============================================================================
# INVARIANT PROOF SUMMARY
# =============================================================================

class TestInvariantProof:
    """
    Consolidated invariant proofs for Track D.
    """
    
    def test_inv_halt_2_proof(self, dispatcher, worker_config):
        """
        INV-HALT-2: halt_cascade_latency < 500ms
        
        MECHANICAL PROOF via timing measurement.
        """
        # Setup
        for i in range(NUM_WORKERS):
            dispatcher.spawn_worker(worker_config)
        
        # Measure 10 iterations
        latencies = []
        for i in range(10):
            # Need to respawn workers each time since they get killed
            if dispatcher._registry.count() < NUM_WORKERS:
                for _ in range(NUM_WORKERS - dispatcher._registry.count()):
                    dispatcher.spawn_worker(worker_config)
            
            result = dispatcher.broadcast_halt(f"proof_{i}")
            latencies.append(result.total_latency_ms)
        
        # Statistical proof
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        print(f"\nINV-HALT-2 PROOF:")
        print(f"  Iterations: {len(latencies)}")
        print(f"  Avg latency: {avg_latency:.2f}ms")
        print(f"  Max latency: {max_latency:.2f}ms")
        print(f"  SLO: {HALT_CASCADE_SLO_MS}ms")
        print(f"  VERDICT: {'PASS' if max_latency < HALT_CASCADE_SLO_MS else 'FAIL'}")
        
        assert max_latency < HALT_CASCADE_SLO_MS, \
            f"INV-HALT-2 violated: max={max_latency}ms"
    
    def test_inv_dispatch_2_proof(self, dispatcher, worker_config):
        """
        INV-DISPATCH-2: broadcast_halt reaches 100% of registered workers
        
        MECHANICAL PROOF via ack counting.
        """
        # Spawn workers
        for i in range(NUM_WORKERS):
            dispatcher.spawn_worker(worker_config)
        
        total_workers = dispatcher._registry.count()
        
        # Broadcast halt
        result = dispatcher.broadcast_halt("inv_dispatch_2_proof")
        
        print(f"\nINV-DISPATCH-2 PROOF:")
        print(f"  Registered workers: {total_workers}")
        print(f"  Workers reached: {result.acks_received}")
        print(f"  Reach rate: {100 * result.acks_received / total_workers:.1f}%")
        print(f"  VERDICT: {'PASS' if result.all_acked else 'FAIL'}")
        
        assert result.all_acked, \
            f"INV-DISPATCH-2 violated: only {result.acks_received}/{total_workers} reached"
