"""
Stale Gate — Context freshness enforcement
==========================================

S32: EXECUTION_PATH

Prevents execution with outdated context.
If state anchor is >15min stale → STATE_CONFLICT + temp kill.

INVARIANT: INV-STALE-KILL-1
>15min stale → STATE_CONFLICT rejection + temporary kill flag
Emergency closes bypass (capital protection).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

# Constants
DEFAULT_TTL_SEC = 1800  # 30 minutes
HIGH_VOL_TTL_SEC = 900  # 15 minutes
NEWS_TTL_SEC = 600  # 10 minutes
STALE_THRESHOLD_SEC = 900  # 15 minutes (INV-STALE-KILL-1)


class StateConflict(Enum):
    """State conflict types."""

    NONE = "NONE"
    STALE_CONTEXT = "STALE_CONTEXT"
    STATE_MISMATCH = "STATE_MISMATCH"
    MISSING_ANCHOR = "MISSING_ANCHOR"


@dataclass
class StaleCheckResult:
    """Result of stale check."""

    fresh: bool
    conflict: StateConflict = StateConflict.NONE
    reason: str = ""
    ttl_remaining_sec: int = 0
    should_kill: bool = False

    @classmethod
    def success(cls, ttl_remaining: int) -> StaleCheckResult:
        """Create success result."""
        return cls(fresh=True, ttl_remaining_sec=ttl_remaining)

    @classmethod
    def stale(cls, reason: str, should_kill: bool = False) -> StaleCheckResult:
        """Create stale result."""
        return cls(
            fresh=False,
            conflict=StateConflict.STALE_CONTEXT,
            reason=reason,
            should_kill=should_kill,
        )


@dataclass
class StateAnchor:
    """
    State anchor — binds intent to market/system state.

    Captures a snapshot of relevant state at a point in time.
    Used to detect if context has changed since intent creation.
    """

    anchor_id: str = ""
    state_hash: str = ""
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ttl_sec: int = DEFAULT_TTL_SEC
    regime: str = "NORMAL"  # NORMAL, HIGH_VOL, NEWS

    # State components
    market_state: dict[str, Any] = field(default_factory=dict)
    system_state: dict[str, Any] = field(default_factory=dict)

    @property
    def expires_at(self) -> datetime:
        """Calculate expiry time."""
        return self.captured_at + timedelta(seconds=self.ttl_sec)

    @property
    def is_expired(self) -> bool:
        """Check if anchor has expired."""
        return datetime.now(UTC) > self.expires_at

    @property
    def ttl_remaining_sec(self) -> int:
        """Seconds until expiry."""
        remaining = (self.expires_at - datetime.now(UTC)).total_seconds()
        return max(0, int(remaining))

    @property
    def age_sec(self) -> int:
        """Age of anchor in seconds."""
        return int((datetime.now(UTC) - self.captured_at).total_seconds())

    def compute_hash(self) -> str:
        """Compute hash of state."""
        import json
        state_dict = {
            "market": self.market_state,
            "system": self.system_state,
            "captured_at": self.captured_at.isoformat(),
        }
        json_str = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "anchor_id": self.anchor_id,
            "state_hash": self.state_hash,
            "captured_at": self.captured_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ttl_sec": self.ttl_sec,
            "ttl_remaining_sec": self.ttl_remaining_sec,
            "age_sec": self.age_sec,
            "regime": self.regime,
            "is_expired": self.is_expired,
        }


class StaleGate:
    """
    Stale gate — prevents execution with outdated context.

    INVARIANT: INV-STALE-KILL-1
    >15min stale → STATE_CONFLICT rejection + temporary kill flag.

    Adaptive TTL:
    - Default: 30 min
    - High volatility: 15 min
    - News proximity: 10 min

    Emergency closes bypass (capital protection).
    """

    def __init__(
        self,
        stale_threshold_sec: int = STALE_THRESHOLD_SEC,
        emit_kill_flag: Callable[[str, str], None] | None = None,
        notify: Callable[[str, str], None] | None = None,
    ) -> None:
        """
        Initialize stale gate.

        Args:
            stale_threshold_sec: Threshold for stale rejection (default 15min)
            emit_kill_flag: Callback to emit kill flag
            notify: Notification callback
        """
        self._stale_threshold_sec = stale_threshold_sec
        self._emit_kill_flag = emit_kill_flag
        self._notify = notify
        self._anchors: dict[str, StateAnchor] = {}
        self._temp_kills: dict[str, datetime] = {}  # state_hash → kill_until

    def register_anchor(self, anchor: StateAnchor) -> None:
        """
        Register a state anchor.

        Args:
            anchor: State anchor to register
        """
        # Compute hash if not set
        if not anchor.state_hash:
            anchor.state_hash = anchor.compute_hash()
        if not anchor.anchor_id:
            anchor.anchor_id = f"ANCHOR-{anchor.state_hash[:8]}"

        self._anchors[anchor.state_hash] = anchor

    def create_anchor(
        self,
        market_state: dict[str, Any],
        system_state: dict[str, Any],
        regime: str = "NORMAL",
    ) -> StateAnchor:
        """
        Create and register a new state anchor.

        Args:
            market_state: Market state snapshot
            system_state: System state snapshot
            regime: Volatility regime

        Returns:
            New StateAnchor
        """
        # Determine TTL based on regime
        if regime == "HIGH_VOL":
            ttl = HIGH_VOL_TTL_SEC
        elif regime == "NEWS":
            ttl = NEWS_TTL_SEC
        else:
            ttl = DEFAULT_TTL_SEC

        anchor = StateAnchor(
            market_state=market_state,
            system_state=system_state,
            ttl_sec=ttl,
            regime=regime,
        )
        anchor.state_hash = anchor.compute_hash()
        anchor.anchor_id = f"ANCHOR-{anchor.state_hash[:8]}"

        self.register_anchor(anchor)
        return anchor

    def check(
        self,
        state_hash: str,
        is_exit: bool = False,
    ) -> StaleCheckResult:
        """
        Check if state is fresh.

        INVARIANT: INV-STALE-KILL-1
        >15min stale → STATE_CONFLICT + temp kill.

        Args:
            state_hash: State hash to check
            is_exit: True if this is an exit/close operation

        Returns:
            StaleCheckResult
        """
        # Emergency closes bypass (capital protection)
        if is_exit:
            return StaleCheckResult.success(ttl_remaining=0)

        # Check for temporary kill on this state
        if state_hash in self._temp_kills:
            kill_until = self._temp_kills[state_hash]
            if datetime.now(UTC) < kill_until:
                return StaleCheckResult.stale(
                    reason="Temporary kill active due to stale state",
                    should_kill=False,  # Already killed
                )
            else:
                # Kill expired, remove it
                del self._temp_kills[state_hash]

        # Find anchor
        anchor = self._anchors.get(state_hash)

        if anchor is None:
            return StaleCheckResult(
                fresh=False,
                conflict=StateConflict.MISSING_ANCHOR,
                reason="State anchor not found",
            )

        # Check if expired
        if anchor.is_expired:
            return self._handle_stale(anchor, "State anchor expired")

        # Check stale threshold
        if anchor.age_sec > self._stale_threshold_sec:
            return self._handle_stale(
                anchor,
                f"State is {anchor.age_sec}s old (threshold: {self._stale_threshold_sec}s)",
            )

        return StaleCheckResult.success(ttl_remaining=anchor.ttl_remaining_sec)

    def _handle_stale(self, anchor: StateAnchor, reason: str) -> StaleCheckResult:
        """
        Handle stale state.

        INVARIANT: INV-STALE-KILL-1
        Triggers temp kill flag and notification.
        """
        # Set temporary kill (5 minutes)
        kill_duration = timedelta(minutes=5)
        self._temp_kills[anchor.state_hash] = datetime.now(UTC) + kill_duration

        # Emit kill flag if callback available
        if self._emit_kill_flag:
            self._emit_kill_flag(
                f"STATE_CONFLICT:{anchor.anchor_id}",
                f"Stale state detected: {reason}",
            )

        # Notify
        if self._notify:
            self._notify(
                f"STALE GATE: {reason}. Temporary kill active for 5min.",
                "WARNING",
            )

        return StaleCheckResult.stale(reason=reason, should_kill=True)

    def refresh_anchor(
        self,
        old_hash: str,
        market_state: dict[str, Any],
        system_state: dict[str, Any],
    ) -> StateAnchor:
        """
        Refresh a stale anchor with new state.

        Args:
            old_hash: Old state hash
            market_state: New market state
            system_state: New system state

        Returns:
            New StateAnchor
        """
        # Get regime from old anchor if exists
        old_anchor = self._anchors.get(old_hash)
        regime = old_anchor.regime if old_anchor else "NORMAL"

        # Remove old anchor
        if old_hash in self._anchors:
            del self._anchors[old_hash]

        # Remove temp kill if any
        if old_hash in self._temp_kills:
            del self._temp_kills[old_hash]

        # Create new anchor
        return self.create_anchor(market_state, system_state, regime)

    def get_active_kills(self) -> list[str]:
        """Get list of state hashes with active temp kills."""
        now = datetime.now(UTC)
        return [
            h for h, until in self._temp_kills.items()
            if until > now
        ]

    def cleanup(self, max_age_sec: int = 7200) -> int:
        """
        Clean up old anchors.

        Args:
            max_age_sec: Remove anchors older than this

        Returns:
            Number of anchors removed
        """
        cutoff = datetime.now(UTC) - timedelta(seconds=max_age_sec)
        removed = 0

        for state_hash, anchor in list(self._anchors.items()):
            if anchor.captured_at < cutoff:
                del self._anchors[state_hash]
                removed += 1

        # Clean expired temp kills
        now = datetime.now(UTC)
        for state_hash, until in list(self._temp_kills.items()):
            if until < now:
                del self._temp_kills[state_hash]

        return removed
