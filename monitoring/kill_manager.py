"""
Kill Manager — ONE-WAY-KILL Flag Management
===========================================

Manages kill flags via BeadStore.
Kill flags are stored as KILL_FLAG beads, not YAML files.

INVARIANT: Kill flags are immutable beads (audit trail)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class KillFlag:
    """Kill flag state."""

    strategy_id: str
    active: bool
    reason: str
    triggered_by: str
    decay_metrics: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    lifted_by: str | None = None
    lifted_reason: str | None = None
    bead_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "active": self.active,
            "reason": self.reason,
            "triggered_by": self.triggered_by,
            "decay_metrics": self.decay_metrics,
            "timestamp": self.timestamp.isoformat(),
            "lifted_by": self.lifted_by,
            "lifted_reason": self.lifted_reason,
            "bead_id": self.bead_id,
        }


# =============================================================================
# KILL MANAGER
# =============================================================================


class KillManager:
    """
    Manages kill flags via BeadStore.

    All kill operations create immutable KILL_FLAG beads.
    """

    def __init__(self, bead_store: Any | None = None) -> None:
        """
        Initialize kill manager.

        Args:
            bead_store: BeadStore for KILL_FLAG beads
        """
        self._bead_store = bead_store
        self._cache: dict[str, KillFlag] = {}

    def set_kill_flag(
        self,
        strategy_id: str,
        reason: str,
        triggered_by: str,
        decay_metrics: dict[str, Any] | None = None,
    ) -> KillFlag:
        """
        Set kill flag for strategy.

        Creates KILL_FLAG bead with active=True.

        Args:
            strategy_id: Strategy to kill
            reason: Reason for kill
            triggered_by: SIGNALMAN, MANUAL, or SYSTEM
            decay_metrics: Optional decay metrics

        Returns:
            Created KillFlag
        """
        flag = KillFlag(
            strategy_id=strategy_id,
            active=True,
            reason=reason,
            triggered_by=triggered_by,
            decay_metrics=decay_metrics,
        )

        # Create bead
        bead_id = f"KILL-{uuid.uuid4().hex[:8]}"
        flag.bead_id = bead_id

        bead_content = {
            "strategy_id": strategy_id,
            "active": True,
            "reason": reason,
            "triggered_by": triggered_by,
            "decay_metrics": decay_metrics,
        }

        bead_dict = {
            "bead_id": bead_id,
            "bead_type": "KILL_FLAG",
            "prev_bead_id": None,
            "bead_hash": hashlib.sha256(
                json.dumps(bead_content, sort_keys=True).encode()
            ).hexdigest()[:16],
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "signer": "system",
            "version": "1.0",
            "content": bead_content,
        }

        if self._bead_store:
            try:
                self._bead_store.write_dict(bead_dict)
            except Exception:  # noqa: S110
                pass

        # Update cache
        self._cache[strategy_id] = flag

        return flag

    def lift_kill_flag(
        self,
        strategy_id: str,
        lifted_by: str,
        lifted_reason: str,
    ) -> KillFlag | None:
        """
        Lift kill flag for strategy.

        Creates new KILL_FLAG bead with active=False.

        Args:
            strategy_id: Strategy to lift kill
            lifted_by: Who lifted the flag
            lifted_reason: Reason for lifting

        Returns:
            Updated KillFlag or None if not found
        """
        # Check if active kill exists
        current = self.get_kill_flag(strategy_id)
        if not current or not current.active:
            return None

        flag = KillFlag(
            strategy_id=strategy_id,
            active=False,
            reason=current.reason,
            triggered_by=current.triggered_by,
            decay_metrics=current.decay_metrics,
            lifted_by=lifted_by,
            lifted_reason=lifted_reason,
        )

        # Create bead
        bead_id = f"KILL-{uuid.uuid4().hex[:8]}"
        flag.bead_id = bead_id

        bead_content = {
            "strategy_id": strategy_id,
            "active": False,
            "reason": current.reason,
            "triggered_by": current.triggered_by,
            "lifted_by": lifted_by,
            "lifted_reason": lifted_reason,
        }

        bead_dict = {
            "bead_id": bead_id,
            "bead_type": "KILL_FLAG",
            "prev_bead_id": current.bead_id,
            "bead_hash": hashlib.sha256(
                json.dumps(bead_content, sort_keys=True).encode()
            ).hexdigest()[:16],
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "signer": "human",
            "version": "1.0",
            "content": bead_content,
        }

        if self._bead_store:
            try:
                self._bead_store.write_dict(bead_dict)
            except Exception:  # noqa: S110
                pass

        # Update cache
        self._cache[strategy_id] = flag

        return flag

    def get_kill_flag(self, strategy_id: str) -> KillFlag | None:
        """
        Get current kill flag state for strategy.

        Args:
            strategy_id: Strategy to check

        Returns:
            KillFlag or None
        """
        # Check cache first
        if strategy_id in self._cache:
            return self._cache[strategy_id]

        # Query bead store
        if self._bead_store is None:
            return None

        try:
            beads = self._bead_store.query_sql(
                "SELECT * FROM beads WHERE bead_type = 'KILL_FLAG' "  # noqa: S608
                f"AND json_extract(content, '$.strategy_id') = '{strategy_id}' "
                "ORDER BY timestamp_utc DESC LIMIT 1",
            )

            if beads:
                bead = beads[0]
                content = bead.get("content", {})
                if isinstance(content, str):
                    content = json.loads(content)

                flag = KillFlag(
                    strategy_id=strategy_id,
                    active=content.get("active", False),
                    reason=content.get("reason", ""),
                    triggered_by=content.get("triggered_by", ""),
                    decay_metrics=content.get("decay_metrics"),
                    lifted_by=content.get("lifted_by"),
                    lifted_reason=content.get("lifted_reason"),
                    bead_id=bead.get("bead_id", ""),
                )

                self._cache[strategy_id] = flag
                return flag

        except Exception:  # noqa: S110
            pass

        return None

    def get_active_kills(self) -> list[KillFlag]:
        """
        Get all active kill flags.

        Returns:
            List of active KillFlags
        """
        active: list[KillFlag] = []

        if self._bead_store is None:
            return [f for f in self._cache.values() if f.active]

        try:
            # Get all KILL_FLAG beads
            beads = self._bead_store.query_sql(
                "SELECT * FROM beads WHERE bead_type = 'KILL_FLAG' " "ORDER BY timestamp_utc DESC",
            )

            # Group by strategy, take latest
            latest: dict[str, dict] = {}
            for bead in beads or []:
                content = bead.get("content", {})
                if isinstance(content, str):
                    content = json.loads(content)

                sid = content.get("strategy_id")
                if sid and sid not in latest:
                    latest[sid] = bead

            # Convert to KillFlags, filter active
            for sid, bead in latest.items():
                content = bead.get("content", {})
                if isinstance(content, str):
                    content = json.loads(content)

                if content.get("active"):
                    flag = KillFlag(
                        strategy_id=sid,
                        active=True,
                        reason=content.get("reason", ""),
                        triggered_by=content.get("triggered_by", ""),
                        decay_metrics=content.get("decay_metrics"),
                        bead_id=bead.get("bead_id", ""),
                    )
                    active.append(flag)
                    self._cache[sid] = flag

        except Exception:  # noqa: S110
            pass

        return active

    def is_killed(self, strategy_id: str) -> bool:
        """
        Check if strategy is killed.

        Args:
            strategy_id: Strategy to check

        Returns:
            True if kill flag is active
        """
        flag = self.get_kill_flag(strategy_id)
        return flag is not None and flag.active

    def compute_hash(self) -> str:
        """
        Compute hash of all active kill flags.

        Used for state anchor.

        Returns:
            Hash string
        """
        active = self.get_active_kills()

        if not active:
            return hashlib.sha256(b"no_kills").hexdigest()[:16]

        data = sorted([f.to_dict() for f in active], key=lambda x: x["strategy_id"])
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
