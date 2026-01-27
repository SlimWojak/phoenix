"""
Dispatcher Types — Worker coordination primitives.

SPRINT: 26.TRACK_D
VERSION: 1.0
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# =============================================================================
# IDENTIFIERS
# =============================================================================


class WorkerId(str):
    """Unique worker identifier."""

    @classmethod
    def generate(cls, worker_type: str) -> "WorkerId":
        """Generate new worker ID."""
        short_uuid = str(uuid.uuid4())[:8]
        return cls(f"{worker_type}-{short_uuid}")


class SessionId(str):
    """TMUX session identifier."""

    pass


# =============================================================================
# ENUMS
# =============================================================================


class WorkerType(Enum):
    """Types of Phoenix workers."""

    ENRICHMENT = "enrichment"
    CSO = "cso"
    EXECUTION = "execution"
    MONITOR = "monitor"
    GENERIC = "generic"


class WorkerStatus(Enum):
    """Worker lifecycle states."""

    PENDING = "pending"  # Spawn requested
    STARTING = "starting"  # Process launching
    RUNNING = "running"  # Active and healthy
    DEGRADED = "degraded"  # Running but unhealthy
    STOPPING = "stopping"  # Shutdown in progress
    STOPPED = "stopped"  # Clean shutdown
    CRASHED = "crashed"  # Unexpected termination
    ORPHANED = "orphaned"  # Lost contact


class HeartbeatStatus(Enum):
    """Heartbeat health states."""

    HEALTHY = "healthy"  # Recent heartbeat
    LATE = "late"  # Heartbeat overdue
    MISSING = "missing"  # No heartbeat in timeout
    DEAD = "dead"  # Confirmed dead


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class WorkerConfig:
    """Configuration for spawning a worker."""

    worker_type: WorkerType
    name: str | None = None
    command: str | None = None
    working_dir: str | None = None
    env_vars: dict[str, str] = field(default_factory=dict)
    heartbeat_interval_ms: int = 1000
    heartbeat_timeout_ms: int = 5000
    auto_restart: bool = False
    max_restarts: int = 3

    def __post_init__(self):
        if self.name is None:
            self.name = f"{self.worker_type.value}-worker"


@dataclass
class DispatcherConfig:
    """Dispatcher configuration."""

    dispatcher_id: str = "phoenix-dispatcher"
    heartbeat_check_interval_ms: int = 500
    halt_timeout_ms: int = 500
    max_workers: int = 50
    tmux_session_prefix: str = "phoenix"


# =============================================================================
# RESULTS
# =============================================================================


@dataclass
class SpawnResult:
    """Result of worker spawn operation."""

    success: bool
    worker_id: WorkerId | None
    session_id: SessionId | None
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class KillResult:
    """Result of worker kill operation."""

    success: bool
    worker_id: WorkerId
    clean_shutdown: bool
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HeartbeatMessage:
    """Worker heartbeat payload."""

    worker_id: WorkerId
    status: WorkerStatus
    quality_score: float
    timestamp: datetime
    sequence: int
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerInfo:
    """Complete worker state."""

    worker_id: WorkerId
    worker_type: WorkerType
    status: WorkerStatus
    session_id: SessionId | None
    pid: int | None
    spawned_at: datetime
    last_heartbeat: datetime | None
    heartbeat_status: HeartbeatStatus
    heartbeat_sequence: int
    restart_count: int
    config: WorkerConfig

    def is_alive(self) -> bool:
        """Check if worker is considered alive."""
        return self.status in (WorkerStatus.RUNNING, WorkerStatus.DEGRADED, WorkerStatus.STARTING)


@dataclass
class HaltAck:
    """Worker halt acknowledgment."""

    worker_id: WorkerId
    acked: bool
    latency_ms: float
    final_status: WorkerStatus
    timestamp: datetime


@dataclass
class BroadcastHaltResult:
    """Result of broadcast halt operation."""

    halt_id: str
    total_workers: int
    acks_received: int
    acks_failed: int
    total_latency_ms: float
    worker_acks: list[HaltAck]
    all_acked: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def success(self) -> bool:
        return self.all_acked and self.total_latency_ms < 500


# =============================================================================
# TMUX TYPES
# =============================================================================


@dataclass
class SessionInfo:
    """TMUX session information."""

    session_id: SessionId
    session_name: str
    window_count: int
    created_at: datetime | None
    attached: bool


@dataclass
class CommandResult:
    """Result of tmux command execution."""

    success: bool
    session_id: SessionId
    command: str
    output: str | None = None
    error: str | None = None
