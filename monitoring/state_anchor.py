"""
State Anchor — T2 Intent State Binding
======================================

Binds T2 intents to current market/system state.
Prevents stale context execution.

INVARIANT: INV-STATE-ANCHOR-1
"T2 intents must include state_hash; reject stale with STATE_CONFLICT"
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

# =============================================================================
# ENUMS
# =============================================================================


class AnchorStatus(str, Enum):
    """State anchor validation status."""

    VALID = "VALID"
    STATE_CONFLICT = "STATE_CONFLICT"
    STALE_CONTEXT = "STALE_CONTEXT"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class StateAnchor:
    """State anchor for T2 intents."""

    anchor_id: str
    timestamp: datetime
    session_id: str
    strategy_params_hash: str
    market_snapshot_hash: str
    kill_flags_hash: str
    signalman_state_hash: str | None = None
    combined_hash: str = ""
    ttl_remaining_minutes: int = 30

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "strategy_params_hash": self.strategy_params_hash,
            "market_snapshot_hash": self.market_snapshot_hash,
            "kill_flags_hash": self.kill_flags_hash,
            "signalman_state_hash": self.signalman_state_hash,
            "combined_hash": self.combined_hash,
            "ttl_remaining_minutes": self.ttl_remaining_minutes,
        }


@dataclass
class ValidationResult:
    """Result of state anchor validation."""

    status: AnchorStatus
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "details": self.details,
        }


# =============================================================================
# STATE ANCHOR MANAGER
# =============================================================================


class StateAnchorManager:
    """
    Manages state anchors for T2 intents.

    INVARIANT: INV-STATE-ANCHOR-1
    Validates that intent state matches current state.
    """

    DEFAULT_TTL = 30  # Minutes

    def __init__(
        self,
        params_loader: Any | None = None,
        kill_manager: Any | None = None,
        cso_scanner: Any | None = None,
    ) -> None:
        """
        Initialize state anchor manager.

        Args:
            params_loader: ParamsLoader for strategy params
            kill_manager: KillManager for kill flags
            cso_scanner: CSOScanner for market structure
        """
        self._params_loader = params_loader
        self._kill_manager = kill_manager
        self._cso_scanner = cso_scanner
        self._current_anchor: StateAnchor | None = None

    def create_anchor(self, session_id: str) -> StateAnchor:
        """
        Create state anchor for current state.

        Args:
            session_id: Session this anchor belongs to

        Returns:
            StateAnchor
        """
        # Get component hashes
        params_hash = self._get_params_hash()
        market_hash = self._get_market_hash()
        kills_hash = self._get_kills_hash()
        signalman_hash = self._get_signalman_hash()

        # Compute combined hash
        components = sorted(
            [
                params_hash,
                market_hash,
                kills_hash,
                signalman_hash or "",
            ]
        )
        combined = hashlib.sha256("|".join(components).encode()).hexdigest()[:16]

        anchor = StateAnchor(
            anchor_id=f"ANCHOR-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            session_id=session_id,
            strategy_params_hash=params_hash,
            market_snapshot_hash=market_hash,
            kill_flags_hash=kills_hash,
            signalman_state_hash=signalman_hash,
            combined_hash=combined,
            ttl_remaining_minutes=self.DEFAULT_TTL,
        )

        self._current_anchor = anchor
        return anchor

    def validate_intent(
        self,
        intent_hash: str,
        intent_time: datetime | None = None,
    ) -> ValidationResult:
        """
        Validate intent state hash against current state.

        INVARIANT: INV-STATE-ANCHOR-1

        Args:
            intent_hash: Hash from intent
            intent_time: When intent was created (for TTL check)

        Returns:
            ValidationResult
        """
        # Get current state
        current_hash = self._compute_current_hash()

        # Check hash match
        if intent_hash != current_hash:
            # Find what changed
            changed = self._find_changes(intent_hash)

            return ValidationResult(
                status=AnchorStatus.STATE_CONFLICT,
                details={
                    "changed_components": changed,
                    "intent_hash": intent_hash,
                    "current_hash": current_hash,
                },
            )

        # Check TTL if time provided
        if intent_time:
            age = datetime.now(UTC) - intent_time
            ttl = timedelta(minutes=self._get_effective_ttl())

            if age > ttl:
                return ValidationResult(
                    status=AnchorStatus.STALE_CONTEXT,
                    details={
                        "age_minutes": age.total_seconds() / 60,
                        "ttl_minutes": ttl.total_seconds() / 60,
                        "reason": "Intent exceeded TTL",
                    },
                )

        return ValidationResult(
            status=AnchorStatus.VALID,
            details={
                "intent_hash": intent_hash,
                "current_hash": current_hash,
            },
        )

    def _compute_current_hash(self) -> str:
        """Compute current combined state hash."""
        params_hash = self._get_params_hash()
        market_hash = self._get_market_hash()
        kills_hash = self._get_kills_hash()
        signalman_hash = self._get_signalman_hash()

        components = sorted(
            [
                params_hash,
                market_hash,
                kills_hash,
                signalman_hash or "",
            ]
        )

        return hashlib.sha256("|".join(components).encode()).hexdigest()[:16]

    def _find_changes(self, intent_hash: str) -> list[str]:
        """Find which components changed since intent."""
        changed: list[str] = []

        if self._current_anchor is None:
            return ["unknown"]

        current_params = self._get_params_hash()
        if current_params != self._current_anchor.strategy_params_hash:
            changed.append("strategy_params")

        current_market = self._get_market_hash()
        if current_market != self._current_anchor.market_snapshot_hash:
            changed.append("market_snapshot")

        current_kills = self._get_kills_hash()
        if current_kills != self._current_anchor.kill_flags_hash:
            changed.append("kill_flags")

        current_signalman = self._get_signalman_hash()
        if current_signalman != self._current_anchor.signalman_state_hash:
            changed.append("signalman_state")

        return changed or ["unknown"]

    def _get_effective_ttl(self) -> int:
        """Get effective TTL considering conditions."""
        ttl = self.DEFAULT_TTL

        # Check for decay alerts (halves TTL)
        # Would query signalman here

        # Check for high volatility (reduces by 30%)
        # Would check market conditions here

        return max(5, ttl)  # Minimum 5 minutes

    def _get_params_hash(self) -> str:
        """Get hash of strategy params."""
        if self._params_loader:
            try:
                params = self._params_loader.load()
                return params.params_hash
            except Exception:  # noqa: S110
                pass

        # Fallback: hash config file directly
        config_path = Path(__file__).parent.parent / "config" / "cso_params.yaml"
        if config_path.exists():
            content = config_path.read_text()
            return hashlib.sha256(content.encode()).hexdigest()[:16]

        return hashlib.sha256(b"no_params").hexdigest()[:16]

    def _get_market_hash(self) -> str:
        """Get hash of current market structure."""
        if self._cso_scanner:
            try:
                result = self._cso_scanner.scan_all_pairs()
                data = result.to_summary()
                return hashlib.sha256(data.encode()).hexdigest()[:16]
            except Exception:  # noqa: S110
                pass

        return hashlib.sha256(b"no_market").hexdigest()[:16]

    def _get_kills_hash(self) -> str:
        """Get hash of active kill flags."""
        if self._kill_manager:
            try:
                return self._kill_manager.compute_hash()
            except Exception:  # noqa: S110
                pass

        return hashlib.sha256(b"no_kills").hexdigest()[:16]

    def _get_signalman_hash(self) -> str | None:
        """Get hash of signalman alerts."""
        # Would query Signalman for active alerts
        return None
