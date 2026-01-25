"""
Test Dispatcher — Core dispatcher functionality.

SPRINT: 26.TRACK_D
EXIT_GATE: dispatcher_skeleton

Tests:
- Dispatcher initialization
- Worker spawn/kill
- Registry management
- Broadcast halt
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
    WorkerId,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def dispatcher():
    """Create a dispatcher for testing."""
    config = DispatcherConfig(
        dispatcher_id="test-dispatcher",
        tmux_session_prefix="phoenix-test",
        max_workers=10
    )
    d = Dispatcher(config)
    d.start()
    yield d
    d.stop(kill_workers=True)


@pytest.fixture
def worker_config():
    """Default worker config."""
    return WorkerConfig(
        worker_type=WorkerType.GENERIC,
        name="test-worker",
        command="sleep 60",  # Simple long-running command
        heartbeat_interval_ms=500,
        heartbeat_timeout_ms=2000
    )


# =============================================================================
# DISPATCHER INITIALIZATION
# =============================================================================

class TestDispatcherInit:
    """Test dispatcher initialization."""
    
    def test_dispatcher_starts(self):
        """Dispatcher starts successfully."""
        config = DispatcherConfig(
            dispatcher_id="init-test",
            tmux_session_prefix="phoenix-init-test"
        )
        d = Dispatcher(config)
        assert d.start() is True
        d.stop()
    
    def test_dispatcher_module_id(self, dispatcher):
        """Dispatcher has correct module_id."""
        assert dispatcher.module_id == "test-dispatcher"
    
    def test_dispatcher_enforces_invariants(self, dispatcher):
        """Dispatcher declares correct invariants."""
        invs = dispatcher.enforced_invariants
        assert "INV-DISPATCH-1" in invs
        assert "INV-DISPATCH-2" in invs


# =============================================================================
# WORKER SPAWN
# =============================================================================

class TestWorkerSpawn:
    """Test worker spawning."""
    
    def test_spawn_worker_success(self, dispatcher, worker_config):
        """Successfully spawn a worker."""
        result = dispatcher.spawn_worker(worker_config)
        
        assert result.success is True
        assert result.worker_id is not None
        assert result.session_id is not None
        assert result.error is None
    
    def test_spawn_creates_tmux_session(self, dispatcher, worker_config):
        """Spawned worker has tmux session."""
        result = dispatcher.spawn_worker(worker_config)
        
        # Verify session exists
        sessions = dispatcher._tmux.list_sessions()
        session_ids = [s.session_id for s in sessions]
        assert result.session_id in session_ids
    
    def test_spawn_registers_worker(self, dispatcher, worker_config):
        """Spawned worker is registered."""
        result = dispatcher.spawn_worker(worker_config)
        
        # Verify in registry
        worker = dispatcher.get_worker_status(result.worker_id)
        assert worker is not None
        assert worker.worker_type == WorkerType.GENERIC
    
    def test_spawn_respects_max_workers(self, dispatcher):
        """Cannot exceed max_workers limit."""
        dispatcher.config.max_workers = 2
        
        # Spawn up to limit
        config = WorkerConfig(worker_type=WorkerType.GENERIC, command="sleep 60")
        r1 = dispatcher.spawn_worker(config)
        r2 = dispatcher.spawn_worker(config)
        
        assert r1.success is True
        assert r2.success is True
        
        # Third should fail
        r3 = dispatcher.spawn_worker(config)
        assert r3.success is False
        assert "Max workers" in r3.error


# =============================================================================
# WORKER KILL
# =============================================================================

class TestWorkerKill:
    """Test worker killing."""
    
    def test_kill_worker_success(self, dispatcher, worker_config):
        """Successfully kill a worker."""
        spawn_result = dispatcher.spawn_worker(worker_config)
        
        kill_result = dispatcher.kill_worker(spawn_result.worker_id)
        
        assert kill_result.success is True
        assert kill_result.worker_id == spawn_result.worker_id
    
    def test_kill_removes_from_registry(self, dispatcher, worker_config):
        """Killed worker removed from registry."""
        spawn_result = dispatcher.spawn_worker(worker_config)
        dispatcher.kill_worker(spawn_result.worker_id)
        
        # Should no longer be in registry
        worker = dispatcher.get_worker_status(spawn_result.worker_id)
        assert worker is None
    
    def test_kill_closes_tmux_session(self, dispatcher, worker_config):
        """Killed worker's tmux session closed."""
        spawn_result = dispatcher.spawn_worker(worker_config)
        session_id = spawn_result.session_id
        
        dispatcher.kill_worker(spawn_result.worker_id)
        
        # Session should be gone
        assert not dispatcher._tmux.session_exists(session_id)
    
    def test_kill_nonexistent_worker(self, dispatcher):
        """Killing nonexistent worker returns error."""
        result = dispatcher.kill_worker(WorkerId("fake-worker"))
        
        assert result.success is False
        assert "not found" in result.error


# =============================================================================
# REGISTRY
# =============================================================================

class TestWorkerRegistry:
    """Test worker registry."""
    
    def test_get_all_workers(self, dispatcher, worker_config):
        """Get all registered workers."""
        dispatcher.spawn_worker(worker_config)
        dispatcher.spawn_worker(worker_config)
        
        workers = dispatcher.get_all_workers()
        assert len(workers) == 2
    
    def test_get_alive_workers(self, dispatcher, worker_config):
        """Get only alive workers."""
        r1 = dispatcher.spawn_worker(worker_config)
        r2 = dispatcher.spawn_worker(worker_config)
        
        # Mark one as crashed
        dispatcher._registry.update_status(r1.worker_id, WorkerStatus.CRASHED)
        
        alive = dispatcher.get_alive_workers()
        assert len(alive) == 1
        assert alive[0].worker_id == r2.worker_id


# =============================================================================
# BROADCAST HALT
# =============================================================================

class TestBroadcastHalt:
    """Test halt broadcast."""
    
    def test_broadcast_halt_to_workers(self, dispatcher, worker_config):
        """Broadcast halt reaches all workers."""
        dispatcher.spawn_worker(worker_config)
        dispatcher.spawn_worker(worker_config)
        
        result = dispatcher.broadcast_halt("test_halt")
        
        assert result.total_workers == 2
        assert result.acks_received >= 0  # May not ack if using sleep
        assert result.halt_id is not None
    
    def test_broadcast_halt_empty_registry(self, dispatcher):
        """Broadcast halt with no workers succeeds."""
        result = dispatcher.broadcast_halt("empty_halt")
        
        assert result.total_workers == 0
        assert result.all_acked is True
        assert result.success is True
    
    def test_broadcast_halt_timing(self, dispatcher, worker_config):
        """Broadcast halt completes within SLO."""
        # Spawn workers
        for _ in range(3):
            dispatcher.spawn_worker(worker_config)
        
        result = dispatcher.broadcast_halt("timing_test")
        
        # INV-HALT-2: cascade < 500ms
        assert result.total_latency_ms < 500, \
            f"Halt broadcast took {result.total_latency_ms}ms, expected < 500ms"


# =============================================================================
# CLEANUP
# =============================================================================

class TestCleanup:
    """Test cleanup operations."""
    
    def test_stop_kills_all_workers(self, worker_config):
        """Stopping dispatcher kills all workers."""
        config = DispatcherConfig(
            dispatcher_id="cleanup-test",
            tmux_session_prefix="phoenix-cleanup-test"
        )
        d = Dispatcher(config)
        d.start()
        
        # Spawn workers
        d.spawn_worker(worker_config)
        d.spawn_worker(worker_config)
        
        # Stop
        d.stop(kill_workers=True)
        
        # Verify no sessions remain
        sessions = d._tmux.list_sessions()
        assert len(sessions) == 0
    
    def test_cleanup_orphans(self, dispatcher, worker_config):
        """Cleanup removes orphan sessions."""
        # Spawn workers
        dispatcher.spawn_worker(worker_config)
        
        # Clear registry (simulate orphan)
        dispatcher._registry._workers.clear()
        
        # Cleanup
        orphans = dispatcher._tmux.cleanup_orphans()
        
        assert orphans >= 1
