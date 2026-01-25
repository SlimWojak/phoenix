"""
Heartbeat Mechanism — Worker liveness monitoring.

SPRINT: 26.TRACK_D
VERSION: 1.0

Heartbeat flow:
  Worker → Dispatcher (periodic)
  Dispatcher monitors, flags missing heartbeats
"""

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Callable
from dataclasses import dataclass
import logging

from .types import (
    WorkerId,
    HeartbeatMessage,
    HeartbeatStatus,
    WorkerStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# HEARTBEAT TRACKER
# =============================================================================

@dataclass
class HeartbeatRecord:
    """Tracked heartbeat state for a worker."""
    worker_id: WorkerId
    last_message: Optional[HeartbeatMessage]
    last_received: Optional[datetime]
    expected_interval_ms: int
    timeout_ms: int
    status: HeartbeatStatus
    missed_count: int


class HeartbeatTracker:
    """
    Tracks worker heartbeats and detects failures.
    
    Thread-safe monitoring of worker liveness.
    """
    
    def __init__(
        self,
        check_interval_ms: int = 500,
        on_status_change: Optional[Callable[[WorkerId, HeartbeatStatus], None]] = None
    ):
        self._records: Dict[WorkerId, HeartbeatRecord] = {}
        self._lock = threading.RLock()
        self._check_interval_ms = check_interval_ms
        self._on_status_change = on_status_change
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
    
    # =========================================================================
    # REGISTRATION
    # =========================================================================
    
    def register(
        self,
        worker_id: WorkerId,
        interval_ms: int = 1000,
        timeout_ms: int = 5000
    ) -> None:
        """Register a worker for heartbeat tracking."""
        with self._lock:
            self._records[worker_id] = HeartbeatRecord(
                worker_id=worker_id,
                last_message=None,
                last_received=None,
                expected_interval_ms=interval_ms,
                timeout_ms=timeout_ms,
                status=HeartbeatStatus.HEALTHY,  # Assume healthy at start
                missed_count=0
            )
            logger.debug(f"Registered heartbeat tracking for {worker_id}")
    
    def deregister(self, worker_id: WorkerId) -> None:
        """Remove worker from tracking."""
        with self._lock:
            if worker_id in self._records:
                del self._records[worker_id]
                logger.debug(f"Deregistered heartbeat tracking for {worker_id}")
    
    # =========================================================================
    # HEARTBEAT RECEPTION
    # =========================================================================
    
    def receive(self, message: HeartbeatMessage) -> None:
        """Process incoming heartbeat."""
        with self._lock:
            if message.worker_id not in self._records:
                logger.warning(f"Heartbeat from unregistered worker: {message.worker_id}")
                return
            
            record = self._records[message.worker_id]
            old_status = record.status
            
            record.last_message = message
            record.last_received = datetime.now(timezone.utc)
            record.missed_count = 0
            record.status = HeartbeatStatus.HEALTHY
            
            if old_status != HeartbeatStatus.HEALTHY and self._on_status_change:
                self._on_status_change(message.worker_id, HeartbeatStatus.HEALTHY)
    
    # =========================================================================
    # STATUS CHECK
    # =========================================================================
    
    def check_all(self) -> Dict[WorkerId, HeartbeatStatus]:
        """Check all workers and return current statuses."""
        now = datetime.now(timezone.utc)
        results = {}
        
        with self._lock:
            for worker_id, record in self._records.items():
                old_status = record.status
                new_status = self._evaluate_status(record, now)
                
                if new_status != old_status:
                    record.status = new_status
                    if self._on_status_change:
                        self._on_status_change(worker_id, new_status)
                
                results[worker_id] = new_status
        
        return results
    
    def get_status(self, worker_id: WorkerId) -> Optional[HeartbeatStatus]:
        """Get current heartbeat status for worker."""
        with self._lock:
            if worker_id in self._records:
                return self._records[worker_id].status
            return None
    
    def _evaluate_status(
        self,
        record: HeartbeatRecord,
        now: datetime
    ) -> HeartbeatStatus:
        """Evaluate heartbeat status based on timing."""
        if record.last_received is None:
            # Never received a heartbeat
            return HeartbeatStatus.MISSING
        
        elapsed_ms = (now - record.last_received).total_seconds() * 1000
        
        if elapsed_ms > record.timeout_ms:
            record.missed_count += 1
            if record.missed_count >= 3:
                return HeartbeatStatus.DEAD
            return HeartbeatStatus.MISSING
        elif elapsed_ms > record.expected_interval_ms * 2:
            return HeartbeatStatus.LATE
        else:
            return HeartbeatStatus.HEALTHY
    
    # =========================================================================
    # MONITORING THREAD
    # =========================================================================
    
    def start_monitoring(self) -> None:
        """Start background monitoring thread."""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="heartbeat-monitor"
        )
        self._monitor_thread.start()
        logger.info("Heartbeat monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        logger.info("Heartbeat monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                self.check_all()
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
            time.sleep(self._check_interval_ms / 1000)
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def get_all_records(self) -> Dict[WorkerId, HeartbeatRecord]:
        """Get copy of all records."""
        with self._lock:
            return dict(self._records)
    
    def get_unhealthy_workers(self) -> list[WorkerId]:
        """Get list of workers with non-HEALTHY status."""
        with self._lock:
            return [
                wid for wid, record in self._records.items()
                if record.status != HeartbeatStatus.HEALTHY
            ]


# =============================================================================
# HEARTBEAT EMITTER (for workers)
# =============================================================================

class HeartbeatEmitter:
    """
    Emits heartbeats from worker to dispatcher.
    
    Used by WorkerBase to send periodic heartbeats.
    """
    
    def __init__(
        self,
        worker_id: WorkerId,
        interval_ms: int = 1000,
        send_fn: Optional[Callable[[HeartbeatMessage], None]] = None
    ):
        self.worker_id = worker_id
        self.interval_ms = interval_ms
        self.send_fn = send_fn
        self._sequence = 0
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._status = WorkerStatus.RUNNING
        self._quality_score = 1.0
    
    def start(self) -> None:
        """Start emitting heartbeats."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._emit_loop,
            daemon=True,
            name=f"heartbeat-{self.worker_id}"
        )
        self._thread.start()
    
    def stop(self) -> None:
        """Stop emitting heartbeats."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def set_status(self, status: WorkerStatus) -> None:
        """Update status reported in heartbeats."""
        self._status = status
    
    def set_quality_score(self, score: float) -> None:
        """Update quality score reported in heartbeats."""
        self._quality_score = max(0.0, min(1.0, score))
    
    def _emit_loop(self) -> None:
        """Background emission loop."""
        while self._running:
            try:
                self._emit_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat emission error: {e}")
            time.sleep(self.interval_ms / 1000)
    
    def _emit_heartbeat(self) -> None:
        """Emit a single heartbeat."""
        self._sequence += 1
        message = HeartbeatMessage(
            worker_id=self.worker_id,
            status=self._status,
            quality_score=self._quality_score,
            timestamp=datetime.now(timezone.utc),
            sequence=self._sequence
        )
        
        if self.send_fn:
            self.send_fn(message)
