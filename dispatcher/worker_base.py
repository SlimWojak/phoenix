"""
Worker Base — Abstract base for Phoenix workers.

SPRINT: 26.TRACK_D
VERSION: 1.0

All Phoenix workers inherit from WorkerBase, which inherits GovernanceInterface.
"""

from abc import abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import sys
import os
import signal
import logging
from pathlib import Path

# Add phoenix root to path
PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import (
    GovernanceInterface,
    ModuleTier,
    StateInput,
    StateTransition,
    FailureMode,
    DegradationAction,
    ErrorClassification,
    ErrorCategory,
    ErrorAction,
    QualityTelemetry,
    HealthState,
    LifecycleState,
)

from .types import (
    WorkerId,
    WorkerType,
    WorkerStatus,
    HeartbeatMessage,
)
from .heartbeat import HeartbeatEmitter

logger = logging.getLogger(__name__)


# =============================================================================
# WORKER BASE
# =============================================================================

class WorkerBase(GovernanceInterface):
    """
    Abstract base class for Phoenix workers.
    
    Extends GovernanceInterface with worker-specific functionality:
    - Worker identity (id, type, parent dispatcher)
    - Heartbeat emission
    - Halt signal handling
    
    INVARIANTS:
    - INV-DISPATCH-1: Worker registers with dispatcher on start
    - INV-DISPATCH-2: Worker responds to halt signals
    - INV-DISPATCH-3: Worker emits regular heartbeats
    """
    
    def __init__(
        self,
        worker_id: WorkerId,
        worker_type: WorkerType,
        tier: ModuleTier = ModuleTier.T0,
        heartbeat_interval_ms: int = 1000,
        parent_dispatcher: Optional[str] = None
    ):
        super().__init__()
        
        self._worker_id = worker_id
        self._worker_type = worker_type
        self._tier = tier
        self._parent_dispatcher = parent_dispatcher
        self._status = WorkerStatus.STARTING
        
        # Heartbeat
        self._heartbeat_emitter = HeartbeatEmitter(
            worker_id=worker_id,
            interval_ms=heartbeat_interval_ms,
            send_fn=self._send_heartbeat
        )
        
        # Setup signal handlers
        self._setup_signal_handlers()
    
    # =========================================================================
    # IDENTITY (GovernanceInterface)
    # =========================================================================
    
    @property
    def module_id(self) -> str:
        return str(self._worker_id)
    
    @property
    def module_tier(self) -> ModuleTier:
        return self._tier
    
    @property
    def enforced_invariants(self) -> List[str]:
        return [
            "INV-DISPATCH-1",  # Register with dispatcher
            "INV-DISPATCH-2",  # Respond to halt
            "INV-DISPATCH-3",  # Emit heartbeats
            "INV-CONTRACT-1",  # Determinism
        ]
    
    @property
    def yield_points(self) -> List[str]:
        return ["process_work", "main_loop"]
    
    # =========================================================================
    # WORKER IDENTITY
    # =========================================================================
    
    @property
    def worker_id(self) -> WorkerId:
        return self._worker_id
    
    @property
    def worker_type(self) -> WorkerType:
        return self._worker_type
    
    @property
    def parent_dispatcher(self) -> Optional[str]:
        return self._parent_dispatcher
    
    @property
    def status(self) -> WorkerStatus:
        return self._status
    
    def set_status(self, status: WorkerStatus) -> None:
        """Update worker status."""
        old_status = self._status
        self._status = status
        self._heartbeat_emitter.set_status(status)
        logger.info(f"Worker {self._worker_id} status: {old_status} -> {status}")
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    def start(self) -> bool:
        """
        Start the worker.
        
        1. Initialize
        2. Register with dispatcher (if parent set)
        3. Start heartbeat
        4. Enter main loop
        """
        try:
            # Initialize via GovernanceInterface
            init_result = self.initialize({})
            if not init_result.success:
                logger.error(f"Worker initialization failed: {init_result}")
                return False
            
            # Start heartbeat
            self._heartbeat_emitter.start()
            
            # Mark running
            self.set_status(WorkerStatus.RUNNING)
            
            logger.info(f"Worker {self._worker_id} started")
            return True
            
        except Exception as e:
            logger.error(f"Worker start failed: {e}")
            self.set_status(WorkerStatus.CRASHED)
            return False
    
    def stop(self, reason: str = "shutdown") -> bool:
        """
        Stop the worker gracefully.
        """
        try:
            self.set_status(WorkerStatus.STOPPING)
            
            # Stop heartbeat
            self._heartbeat_emitter.stop()
            
            # Shutdown via GovernanceInterface
            self.shutdown(reason)
            
            self.set_status(WorkerStatus.STOPPED)
            logger.info(f"Worker {self._worker_id} stopped: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Worker stop failed: {e}")
            return False
    
    def run(self) -> None:
        """
        Main worker entry point.
        
        Starts worker and enters main loop.
        """
        if not self.start():
            return
        
        try:
            self.main_loop()
        except Exception as e:
            logger.error(f"Worker main loop error: {e}")
            self.set_status(WorkerStatus.CRASHED)
        finally:
            self.stop("main_loop_exit")
    
    # =========================================================================
    # MAIN LOOP (Override in subclass)
    # =========================================================================
    
    @abstractmethod
    def main_loop(self) -> None:
        """
        Worker main loop.
        
        Subclasses implement their work here.
        Must call self.check_halt() at yield points.
        """
        pass
    
    @abstractmethod
    def process_work(self, work_item: Any) -> Any:
        """
        Process a single work item.
        
        Called from main_loop.
        """
        pass
    
    # =========================================================================
    # HALT HANDLING
    # =========================================================================
    
    def _setup_signal_handlers(self) -> None:
        """Setup OS signal handlers for halt."""
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)
    
    def _handle_sigterm(self, signum, frame) -> None:
        """Handle SIGTERM - graceful shutdown."""
        logger.info(f"Worker {self._worker_id} received SIGTERM")
        self.request_halt()
    
    def _handle_sigint(self, signum, frame) -> None:
        """Handle SIGINT (Ctrl-C) - graceful shutdown."""
        logger.info(f"Worker {self._worker_id} received SIGINT")
        self.request_halt()
    
    def on_halt(self) -> None:
        """
        Called when halt is triggered.
        
        Override to add cleanup logic.
        """
        logger.info(f"Worker {self._worker_id} halting")
        self.stop("halt_signal")
    
    # =========================================================================
    # HEARTBEAT
    # =========================================================================
    
    def _send_heartbeat(self, message: HeartbeatMessage) -> None:
        """
        Send heartbeat to dispatcher.
        
        Override to implement actual IPC.
        Default: log only (for testing).
        """
        logger.debug(f"Heartbeat: {message.worker_id} seq={message.sequence}")
    
    # =========================================================================
    # STATE MACHINE (GovernanceInterface)
    # =========================================================================
    
    def process_state(self, input: StateInput) -> StateTransition:
        """
        Process state transition.
        
        Delegates to process_work for actual logic.
        """
        previous_hash = self.compute_state_hash()
        
        self.check_halt()  # Yield point
        
        result = self.process_work(input.data)
        
        new_hash = self.compute_state_hash()
        
        return StateTransition(
            previous_hash=previous_hash,
            new_hash=new_hash,
            mutations=["work_processed"],
            timestamp=datetime.now(timezone.utc)
        )
    
    # =========================================================================
    # ERROR HANDLING
    # =========================================================================
    
    def get_failure_modes(self) -> List[FailureMode]:
        return [
            FailureMode(
                id="WORKER-FAIL-1",
                trigger="heartbeat_timeout",
                classification=ErrorClassification(
                    ErrorCategory.CRITICAL,
                    ErrorAction.HALT
                )
            ),
            FailureMode(
                id="WORKER-FAIL-2",
                trigger="dispatcher_lost",
                classification=ErrorClassification(
                    ErrorCategory.CRITICAL,
                    ErrorAction.HALT
                )
            ),
            FailureMode(
                id="WORKER-FAIL-3",
                trigger="work_error",
                classification=ErrorClassification(
                    ErrorCategory.RECOVERABLE,
                    ErrorAction.RETRY
                )
            ),
        ]
    
    def get_degradation_paths(self) -> Dict[str, DegradationAction]:
        return {
            "WORKER-FAIL-3": DegradationAction(
                action_type="retry_with_backoff",
                params={"max_retries": 3, "backoff_ms": 1000}
            ),
        }


# =============================================================================
# MOCK WORKER (for testing)
# =============================================================================

class MockWorker(WorkerBase):
    """
    Simple worker for testing dispatcher mechanics.
    """
    
    def __init__(
        self,
        worker_id: WorkerId,
        loop_delay_ms: int = 100
    ):
        super().__init__(
            worker_id=worker_id,
            worker_type=WorkerType.GENERIC,
            tier=ModuleTier.T0
        )
        self._loop_delay_ms = loop_delay_ms
        self._work_count = 0
    
    def main_loop(self) -> None:
        """Simple loop that checks halt."""
        import time
        
        while not self._halt_manager._halt_signal.is_set():
            self.check_halt()  # Yield point
            self._work_count += 1
            time.sleep(self._loop_delay_ms / 1000)
    
    def process_work(self, work_item: Any) -> Any:
        """Process mock work."""
        return {"processed": work_item, "count": self._work_count}
