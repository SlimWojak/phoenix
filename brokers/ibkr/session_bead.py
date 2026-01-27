"""
IBKR Session Bead — Connection lifecycle tracking
==================================================

S33: FIRST_BLOOD

Emits IBKR_SESSION beads for audit trail of all connection events.

BEAD EVENTS:
- CONNECT: Initial connection established
- DISCONNECT: Connection lost
- RECONNECT: Reconnection attempt (with attempt number)
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    pass


class SessionEvent(Enum):
    """IBKR session event types."""

    CONNECT = "CONNECT"
    DISCONNECT = "DISCONNECT"
    RECONNECT = "RECONNECT"


@dataclass
class SessionBeadData:
    """
    IBKR_SESSION bead data structure.

    Matches schema defined in beads.yaml.
    """

    bead_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bead_type: str = "IBKR_SESSION"
    prev_bead_id: str | None = None
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    signer: str = "system"
    version: str = "1.0"

    # Session-specific fields
    event: SessionEvent = SessionEvent.CONNECT
    mode: str = "MOCK"  # IBKRMode value
    account: str = ""
    port: int = 4002
    gateway_version: str | None = None
    reconnect_attempt: int = 0

    # Computed
    bead_hash: str = ""

    def __post_init__(self) -> None:
        """Compute hash after initialization."""
        if not self.bead_hash:
            self.bead_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA256 hash of bead content."""
        content = (
            f"{self.bead_type}|{self.event.value}|{self.mode}|{self.account}|"
            f"{self.port}|{self.reconnect_attempt}|{self.timestamp_utc.isoformat()}|"
            f"{self.prev_bead_id or 'null'}|{self.signer}"
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "bead_id": self.bead_id,
            "bead_type": self.bead_type,
            "prev_bead_id": self.prev_bead_id,
            "bead_hash": self.bead_hash,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "signer": self.signer,
            "version": self.version,
            "event": self.event.value,
            "mode": self.mode,
            "account": self.account,
            "port": self.port,
            "gateway_version": self.gateway_version,
            "reconnect_attempt": self.reconnect_attempt,
        }


# Type for bead emission callback
BeadEmitter = Callable[[SessionBeadData], None]


class SessionBeadEmitter:
    """
    Emits IBKR_SESSION beads for connection lifecycle events.

    Tracks chain for merkle-lite lineage.
    """

    def __init__(self, emitter: BeadEmitter | None = None) -> None:
        """
        Initialize emitter.

        Args:
            emitter: Callback to emit beads (e.g., BeadStore.append)
        """
        self._emitter = emitter
        self._last_bead_id: str | None = None

    def set_emitter(self, emitter: BeadEmitter) -> None:
        """Set bead emission callback."""
        self._emitter = emitter

    def emit_connect(
        self,
        mode: str,
        account: str,
        port: int,
        gateway_version: str | None = None,
    ) -> SessionBeadData:
        """
        Emit CONNECT event bead.

        Args:
            mode: IBKRMode value
            account: Account ID
            port: Gateway port
            gateway_version: IB Gateway version (if known)

        Returns:
            Created bead data
        """
        bead = SessionBeadData(
            event=SessionEvent.CONNECT,
            mode=mode,
            account=account,
            port=port,
            gateway_version=gateway_version,
            prev_bead_id=self._last_bead_id,
        )

        self._emit(bead)
        return bead

    def emit_disconnect(
        self,
        mode: str,
        account: str,
        port: int,
        reason: str | None = None,
    ) -> SessionBeadData:
        """
        Emit DISCONNECT event bead.

        Args:
            mode: IBKRMode value
            account: Account ID
            port: Gateway port
            reason: Disconnect reason (for logging)

        Returns:
            Created bead data
        """
        bead = SessionBeadData(
            event=SessionEvent.DISCONNECT,
            mode=mode,
            account=account,
            port=port,
            prev_bead_id=self._last_bead_id,
        )

        self._emit(bead)
        return bead

    def emit_reconnect(
        self,
        mode: str,
        account: str,
        port: int,
        attempt: int,
        gateway_version: str | None = None,
    ) -> SessionBeadData:
        """
        Emit RECONNECT event bead.

        Args:
            mode: IBKRMode value
            account: Account ID
            port: Gateway port
            attempt: Reconnection attempt number (1-indexed)
            gateway_version: IB Gateway version (if known)

        Returns:
            Created bead data
        """
        bead = SessionBeadData(
            event=SessionEvent.RECONNECT,
            mode=mode,
            account=account,
            port=port,
            reconnect_attempt=attempt,
            gateway_version=gateway_version,
            prev_bead_id=self._last_bead_id,
        )

        self._emit(bead)
        return bead

    def _emit(self, bead: SessionBeadData) -> None:
        """Emit bead and track chain."""
        self._last_bead_id = bead.bead_id

        if self._emitter:
            self._emitter(bead)

    def get_last_bead_id(self) -> str | None:
        """Get last emitted bead ID for chain tracking."""
        return self._last_bead_id
