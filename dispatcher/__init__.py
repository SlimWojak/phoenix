"""
Phoenix Dispatcher — Worker coordination and control.

SPRINT: 26.TRACK_D
VERSION: 1.0

Provides:
- Dispatcher: Central coordinator for Phoenix workers
- WorkerBase: Abstract base for workers (inherits GovernanceInterface)
- TmuxController: TMUX session management
- HeartbeatTracker: Worker liveness monitoring
"""

from .types import (
    WorkerId,
    SessionId,
    WorkerType,
    WorkerStatus,
    HeartbeatStatus,
    WorkerConfig,
    DispatcherConfig,
    WorkerInfo,
    SpawnResult,
    KillResult,
    BroadcastHaltResult,
    HaltAck,
    HeartbeatMessage,
    SessionInfo,
    CommandResult,
)

from .heartbeat import (
    HeartbeatTracker,
    HeartbeatEmitter,
    HeartbeatRecord,
)

from .tmux_control import TmuxController

from .worker_base import (
    WorkerBase,
    MockWorker,
)

from .dispatcher import (
    Dispatcher,
    WorkerRegistry,
)


__all__ = [
    # Types
    'WorkerId',
    'SessionId',
    'WorkerType',
    'WorkerStatus',
    'HeartbeatStatus',
    'WorkerConfig',
    'DispatcherConfig',
    'WorkerInfo',
    'SpawnResult',
    'KillResult',
    'BroadcastHaltResult',
    'HaltAck',
    'HeartbeatMessage',
    'SessionInfo',
    'CommandResult',
    # Heartbeat
    'HeartbeatTracker',
    'HeartbeatEmitter',
    'HeartbeatRecord',
    # TMUX
    'TmuxController',
    # Worker
    'WorkerBase',
    'MockWorker',
    # Dispatcher
    'Dispatcher',
    'WorkerRegistry',
]

__version__ = '1.0.0'
