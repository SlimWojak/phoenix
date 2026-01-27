"""
Dispatcher — Central coordinator for Phoenix workers.

SPRINT: 26.TRACK_D
VERSION: 1.0

Orchestrates worker lifecycle: spawn, monitor, halt, kill.

INVARIANTS:
- INV-DISPATCH-1: All workers registered in WorkerRegistry
- INV-DISPATCH-2: broadcast_halt reaches 100% of registered workers
- INV-DISPATCH-3: Worker crash detected within heartbeat_timeout
- INV-DISPATCH-4: No orphan tmux sessions after dispatcher shutdown
"""

import logging
import sys
import threading
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

# Add phoenix root to path
PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import (
    DegradationAction,
    ErrorAction,
    ErrorCategory,
    ErrorClassification,
    FailureMode,
    GovernanceInterface,
    ModuleTier,
    StateInput,
    StateTransition,
)

from .heartbeat import HeartbeatTracker
from .tmux_control import TmuxController
from .types import (
    BroadcastHaltResult,
    DispatcherConfig,
    HaltAck,
    HeartbeatMessage,
    HeartbeatStatus,
    KillResult,
    SpawnResult,
    WorkerConfig,
    WorkerId,
    WorkerInfo,
    WorkerStatus,
    WorkerType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# WORKER REGISTRY
# =============================================================================


class WorkerRegistry:
    """
    Thread-safe registry of active workers.

    Tracks all spawned workers and their status.
    """

    def __init__(self):
        self._workers: dict[WorkerId, WorkerInfo] = {}
        self._lock = threading.RLock()

    def register(self, info: WorkerInfo) -> None:
        """Register a worker."""
        with self._lock:
            self._workers[info.worker_id] = info
            logger.info(f"Registered worker: {info.worker_id}")

    def deregister(self, worker_id: WorkerId) -> WorkerInfo | None:
        """Deregister a worker."""
        with self._lock:
            info = self._workers.pop(worker_id, None)
            if info:
                logger.info(f"Deregistered worker: {worker_id}")
            return info

    def get(self, worker_id: WorkerId) -> WorkerInfo | None:
        """Get worker info."""
        with self._lock:
            return self._workers.get(worker_id)

    def get_all(self) -> list[WorkerInfo]:
        """Get all workers."""
        with self._lock:
            return list(self._workers.values())

    def get_by_type(self, worker_type: WorkerType) -> list[WorkerInfo]:
        """Get workers of specific type."""
        with self._lock:
            return [w for w in self._workers.values() if w.worker_type == worker_type]

    def get_alive(self) -> list[WorkerInfo]:
        """Get all alive workers."""
        with self._lock:
            return [w for w in self._workers.values() if w.is_alive()]

    def update_status(self, worker_id: WorkerId, status: WorkerStatus) -> None:
        """Update worker status."""
        with self._lock:
            if worker_id in self._workers:
                self._workers[worker_id].status = status

    def update_heartbeat(
        self, worker_id: WorkerId, timestamp: datetime, sequence: int, hb_status: HeartbeatStatus
    ) -> None:
        """Update heartbeat info."""
        with self._lock:
            if worker_id in self._workers:
                self._workers[worker_id].last_heartbeat = timestamp
                self._workers[worker_id].heartbeat_sequence = sequence
                self._workers[worker_id].heartbeat_status = hb_status

    def count(self) -> int:
        """Count registered workers."""
        with self._lock:
            return len(self._workers)

    def is_empty(self) -> bool:
        """Check if registry is empty."""
        return self.count() == 0


# =============================================================================
# DISPATCHER
# =============================================================================


class Dispatcher(GovernanceInterface):
    """
    Central coordinator for Phoenix workers.

    Responsibilities:
    - Spawn workers (via tmux)
    - Track worker registry
    - Monitor heartbeats
    - Broadcast halt signals
    - Handle worker crashes

    TIER: T0 (infrastructure, no capital impact)
    """

    def __init__(self, config: DispatcherConfig | None = None):
        super().__init__()

        self.config = config or DispatcherConfig()
        self._registry = WorkerRegistry()
        self._tmux = TmuxController(session_prefix=self.config.tmux_session_prefix)

        # Heartbeat tracking
        self._heartbeat_tracker = HeartbeatTracker(
            check_interval_ms=self.config.heartbeat_check_interval_ms,
            on_status_change=self._on_heartbeat_status_change,
        )

        # Callbacks
        self._on_worker_crash: Callable[[WorkerId], None] | None = None

        # State
        self._running = False
        self._halt_broadcast_lock = threading.Lock()

    # =========================================================================
    # IDENTITY (GovernanceInterface)
    # =========================================================================

    @property
    def module_id(self) -> str:
        return self.config.dispatcher_id

    @property
    def module_tier(self) -> ModuleTier:
        return ModuleTier.T0  # Infrastructure

    @property
    def enforced_invariants(self) -> list[str]:
        return [
            "INV-DISPATCH-1",  # All workers registered
            "INV-DISPATCH-2",  # Halt reaches all workers
            "INV-DISPATCH-3",  # Crash detection
            "INV-DISPATCH-4",  # No orphans
            "INV-CONTRACT-1",  # Determinism
        ]

    @property
    def yield_points(self) -> list[str]:
        return ["broadcast_halt", "spawn_worker"]

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def start(self) -> bool:
        """Start the dispatcher."""
        try:
            # Initialize governance
            init_result = self.initialize({})
            if not init_result.success:
                logger.error("Dispatcher init failed")
                return False

            # Start heartbeat monitoring
            self._heartbeat_tracker.start_monitoring()

            self._running = True
            logger.info(f"Dispatcher {self.config.dispatcher_id} started")
            return True

        except Exception as e:
            logger.error(f"Dispatcher start failed: {e}")
            return False

    def stop(self, kill_workers: bool = True) -> bool:
        """
        Stop the dispatcher.

        Args:
            kill_workers: If True, kill all workers first
        """
        try:
            self._running = False

            if kill_workers:
                # Kill all workers
                for worker in self._registry.get_all():
                    self.kill_worker(worker.worker_id)

            # Stop heartbeat monitoring
            self._heartbeat_tracker.stop_monitoring()

            # Cleanup orphan tmux sessions
            orphans = self._tmux.cleanup_orphans()
            if orphans > 0:
                logger.warning(f"Cleaned up {orphans} orphan sessions")

            # Shutdown governance
            self.shutdown("dispatcher_stop")

            logger.info(f"Dispatcher {self.config.dispatcher_id} stopped")
            return True

        except Exception as e:
            logger.error(f"Dispatcher stop failed: {e}")
            return False

    # =========================================================================
    # WORKER SPAWN
    # =========================================================================

    def spawn_worker(self, config: WorkerConfig) -> SpawnResult:
        """
        Spawn a new worker.

        Creates tmux session and registers worker.

        Args:
            config: Worker configuration

        Returns:
            SpawnResult with worker_id and session_id
        """
        self.check_halt()  # Yield point

        # Check limits
        if self._registry.count() >= self.config.max_workers:
            return SpawnResult(
                success=False,
                worker_id=None,
                session_id=None,
                error=f"Max workers ({self.config.max_workers}) reached",
            )

        # Generate worker ID
        worker_id = WorkerId.generate(config.worker_type.value)

        try:
            # Create tmux session
            session_id = self._tmux.create_session(
                name=str(worker_id), command=config.command, working_dir=config.working_dir
            )

            # Create worker info
            now = datetime.now(UTC)
            worker_info = WorkerInfo(
                worker_id=worker_id,
                worker_type=config.worker_type,
                status=WorkerStatus.STARTING,
                session_id=session_id,
                pid=None,  # Will be set when worker reports
                spawned_at=now,
                last_heartbeat=None,
                heartbeat_status=HeartbeatStatus.HEALTHY,
                heartbeat_sequence=0,
                restart_count=0,
                config=config,
            )

            # Register
            self._registry.register(worker_info)

            # Register for heartbeat tracking
            self._heartbeat_tracker.register(
                worker_id,
                interval_ms=config.heartbeat_interval_ms,
                timeout_ms=config.heartbeat_timeout_ms,
            )

            logger.info(f"Spawned worker: {worker_id} in session {session_id}")

            return SpawnResult(success=True, worker_id=worker_id, session_id=session_id)

        except Exception as e:
            logger.error(f"Failed to spawn worker: {e}")
            return SpawnResult(success=False, worker_id=worker_id, session_id=None, error=str(e))

    # =========================================================================
    # WORKER KILL
    # =========================================================================

    def kill_worker(self, worker_id: WorkerId, force: bool = False) -> KillResult:
        """
        Kill a worker.

        Args:
            worker_id: Worker to kill
            force: If True, use SIGKILL instead of SIGTERM

        Returns:
            KillResult
        """
        worker = self._registry.get(worker_id)
        if not worker:
            return KillResult(
                success=False, worker_id=worker_id, clean_shutdown=False, error="Worker not found"
            )

        try:
            # Update status
            self._registry.update_status(worker_id, WorkerStatus.STOPPING)

            # Send interrupt first (graceful)
            if not force and worker.session_id:
                self._tmux.send_interrupt(worker.session_id)
                time.sleep(0.5)  # Brief wait for graceful shutdown

            # Kill tmux session
            clean = False
            if worker.session_id:
                clean = self._tmux.kill_session(worker.session_id)

            # Deregister
            self._registry.deregister(worker_id)
            self._heartbeat_tracker.deregister(worker_id)

            logger.info(f"Killed worker: {worker_id}")

            return KillResult(success=True, worker_id=worker_id, clean_shutdown=clean)

        except Exception as e:
            logger.error(f"Failed to kill worker {worker_id}: {e}")
            return KillResult(
                success=False, worker_id=worker_id, clean_shutdown=False, error=str(e)
            )

    # =========================================================================
    # HALT BROADCAST
    # =========================================================================

    def broadcast_halt(self, reason: str = "dispatcher_halt") -> BroadcastHaltResult:
        """
        Broadcast halt to all workers.

        Sends halt signal to all registered workers and collects acks.

        Args:
            reason: Reason for halt

        Returns:
            BroadcastHaltResult with timing and ack info
        """
        self.check_halt()  # Yield point

        halt_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        with self._halt_broadcast_lock:
            workers = self._registry.get_alive()
            total_workers = len(workers)
            worker_acks: list[HaltAck] = []

            if total_workers == 0:
                return BroadcastHaltResult(
                    halt_id=halt_id,
                    total_workers=0,
                    acks_received=0,
                    acks_failed=0,
                    total_latency_ms=0,
                    worker_acks=[],
                    all_acked=True,
                )

            # Send halt to each worker
            for worker in workers:
                ack_start = time.perf_counter()
                acked = False

                try:
                    if worker.session_id:
                        # Send HALT command via tmux
                        result = self._tmux.send_command(
                            worker.session_id, f"# HALT {halt_id} {reason}"
                        )

                        # Also send interrupt
                        self._tmux.send_interrupt(worker.session_id)
                        acked = result.success

                except Exception as e:
                    logger.error(f"Failed to halt {worker.worker_id}: {e}")

                ack_latency = (time.perf_counter() - ack_start) * 1000

                worker_acks.append(
                    HaltAck(
                        worker_id=worker.worker_id,
                        acked=acked,
                        latency_ms=ack_latency,
                        final_status=WorkerStatus.STOPPING if acked else worker.status,
                        timestamp=datetime.now(UTC),
                    )
                )

                # Update status
                if acked:
                    self._registry.update_status(worker.worker_id, WorkerStatus.STOPPING)

            total_latency = (time.perf_counter() - start_time) * 1000
            acks_received = sum(1 for ack in worker_acks if ack.acked)

            result = BroadcastHaltResult(
                halt_id=halt_id,
                total_workers=total_workers,
                acks_received=acks_received,
                acks_failed=total_workers - acks_received,
                total_latency_ms=total_latency,
                worker_acks=worker_acks,
                all_acked=(acks_received == total_workers),
            )

            logger.info(
                f"Halt broadcast: {acks_received}/{total_workers} acked "
                f"in {total_latency:.1f}ms"
            )

            return result

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_worker_status(self, worker_id: WorkerId) -> WorkerInfo | None:
        """Get worker status."""
        return self._registry.get(worker_id)

    def get_all_workers(self) -> list[WorkerInfo]:
        """Get all registered workers."""
        return self._registry.get_all()

    def get_alive_workers(self) -> list[WorkerInfo]:
        """Get all alive workers."""
        return self._registry.get_alive()

    # =========================================================================
    # HEARTBEAT HANDLING
    # =========================================================================

    def receive_heartbeat(self, message: HeartbeatMessage) -> None:
        """Process incoming heartbeat from worker."""
        self._heartbeat_tracker.receive(message)
        self._registry.update_heartbeat(
            message.worker_id, message.timestamp, message.sequence, HeartbeatStatus.HEALTHY
        )

    def _on_heartbeat_status_change(self, worker_id: WorkerId, status: HeartbeatStatus) -> None:
        """Handle heartbeat status change."""
        logger.warning(f"Heartbeat status change: {worker_id} -> {status}")

        if status == HeartbeatStatus.DEAD:
            # Worker crash detected
            self._handle_worker_crash(worker_id)

    def _handle_worker_crash(self, worker_id: WorkerId) -> None:
        """Handle detected worker crash."""
        logger.error(f"Worker crash detected: {worker_id}")

        # Update status
        self._registry.update_status(worker_id, WorkerStatus.CRASHED)

        # Get worker info
        worker = self._registry.get(worker_id)

        # Callback
        if self._on_worker_crash:
            self._on_worker_crash(worker_id)

        # Auto-restart if configured
        if worker and worker.config.auto_restart:
            if worker.restart_count < worker.config.max_restarts:
                logger.info(f"Auto-restarting worker: {worker_id}")
                # Deregister old
                self._registry.deregister(worker_id)
                # Spawn new
                result = self.spawn_worker(worker.config)
                if result.success:
                    # Update restart count
                    new_worker = self._registry.get(result.worker_id)
                    if new_worker:
                        new_worker.restart_count = worker.restart_count + 1

    # =========================================================================
    # STATE MACHINE (GovernanceInterface)
    # =========================================================================

    def process_state(self, input: StateInput) -> StateTransition:
        """Process dispatcher state."""
        previous_hash = self.compute_state_hash()

        self.check_halt()

        # Dispatcher state is the registry
        worker_count = self._registry.count()
        alive_count = len(self._registry.get_alive())

        new_hash = self.compute_state_hash()

        return StateTransition(
            previous_hash=previous_hash,
            new_hash=new_hash,
            mutations=[f"workers:{worker_count}", f"alive:{alive_count}"],
            timestamp=datetime.now(UTC),
        )

    def get_failure_modes(self) -> list[FailureMode]:
        return [
            FailureMode(
                id="DISPATCH-FAIL-1",
                trigger="all_workers_dead",
                classification=ErrorClassification(ErrorCategory.CRITICAL, ErrorAction.HALT),
            ),
            FailureMode(
                id="DISPATCH-FAIL-2",
                trigger="tmux_unavailable",
                classification=ErrorClassification(ErrorCategory.CRITICAL, ErrorAction.HALT),
            ),
        ]

    def get_degradation_paths(self) -> dict[str, DegradationAction]:
        return {}
