"""
Execution Intent — Deterministic intent objects.

SPRINT: S27.0
STATUS: SKELETON
CAPITAL: DISABLED

Intent objects represent WHAT the system wants to do.
They are:
- Deterministic (same input → same intent hash)
- Immutable after creation
- NOT actual orders (no capital mutation)

FORBIDDEN:
- Live order submission
- Broker connections
- Capital mutation

INVARIANTS:
- INV-CONTRACT-1: deterministic
- INV-EXEC-NO-CAPITAL: no capital actions in S27
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum

# =============================================================================
# EXCEPTIONS
# =============================================================================


class IntentMutationError(Exception):
    """Raised when attempting to mutate a frozen intent."""

    pass


class CapitalActionForbiddenError(Exception):
    """Raised when attempting capital action in S27."""

    def __init__(self, action: str):
        self.action = action
        super().__init__(
            f"INV-EXEC-NO-CAPITAL violated: " f"Capital action '{action}' forbidden in S27"
        )


# =============================================================================
# INTENT TYPES
# =============================================================================


class IntentType(Enum):
    """Type of execution intent."""

    ENTRY = "ENTRY"  # New position intent
    EXIT = "EXIT"  # Close position intent
    SCALE = "SCALE"  # Scale position intent
    HEDGE = "HEDGE"  # Hedge intent
    CANCEL = "CANCEL"  # Cancel pending intent


class IntentStatus(Enum):
    """Status of intent lifecycle."""

    PENDING = "PENDING"  # Created, not yet processed
    BLOCKED = "BLOCKED"  # Blocked by halt gate
    APPROVED = "APPROVED"  # Passed gates (but NOT executed in S27)
    REJECTED = "REJECTED"  # Failed validation
    EXPIRED = "EXPIRED"  # TTL exceeded


class Direction(Enum):
    """Trade direction."""

    LONG = "LONG"
    SHORT = "SHORT"


# =============================================================================
# INTENT DATA CLASS
# =============================================================================


@dataclass
class ExecutionIntent:
    """
    Deterministic intent object.

    IMMUTABLE after creation.
    DOES NOT execute — skeleton only in S27.
    """

    # Identity
    intent_id: str
    intent_type: IntentType
    status: IntentStatus

    # Timing
    created_at: datetime
    expires_at: datetime | None

    # Target
    symbol: str
    direction: Direction

    # Parameters (skeleton — not used for actual orders)
    size: float
    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None

    # Source
    source_bead_id: str | None
    source_state_hash: str

    # Hash
    intent_hash: str = field(default="")

    # Frozen flag
    _frozen: bool = field(default=False, repr=False)

    def __post_init__(self):
        """Freeze intent and compute hash."""
        if not self.intent_hash:
            object.__setattr__(self, "intent_hash", self._compute_hash())
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name: str, value) -> None:
        """Enforce immutability."""
        if hasattr(self, "_frozen") and self._frozen:
            # Allow status updates through proper method
            if name == "status":
                raise IntentMutationError("Use update_status() to change intent status")
            raise IntentMutationError(f"Cannot modify {name} on frozen intent")
        object.__setattr__(self, name, value)

    def _compute_hash(self) -> str:
        """
        Compute deterministic hash.

        INV-CONTRACT-1: Same input → same hash.
        """
        hashable = {
            "intent_type": self.intent_type.value,
            "symbol": self.symbol,
            "direction": self.direction.value,
            "size": self.size,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "source_bead_id": self.source_bead_id,
            "source_state_hash": self.source_state_hash,
        }
        canonical = json.dumps(hashable, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def update_status(self, new_status: IntentStatus) -> "ExecutionIntent":
        """
        Create new intent with updated status.

        Returns NEW intent (immutability preserved).
        """
        return ExecutionIntent(
            intent_id=self.intent_id,
            intent_type=self.intent_type,
            status=new_status,
            created_at=self.created_at,
            expires_at=self.expires_at,
            symbol=self.symbol,
            direction=self.direction,
            size=self.size,
            entry_price=self.entry_price,
            stop_loss=self.stop_loss,
            take_profit=self.take_profit,
            source_bead_id=self.source_bead_id,
            source_state_hash=self.source_state_hash,
            intent_hash=self.intent_hash,  # Preserve hash
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "intent_id": self.intent_id,
            "intent_type": self.intent_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "symbol": self.symbol,
            "direction": self.direction.value,
            "size": self.size,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "source_bead_id": self.source_bead_id,
            "source_state_hash": self.source_state_hash,
            "intent_hash": self.intent_hash,
        }


# =============================================================================
# INTENT FACTORY
# =============================================================================


class IntentFactory:
    """
    Factory for creating execution intents.

    S27: Creates intents but DOES NOT execute them.
    """

    def __init__(self, source_module: str):
        self.source_module = source_module
        self._counter = 0

    def create_entry_intent(
        self,
        symbol: str,
        direction: Direction,
        size: float,
        state_hash: str,
        bead_id: str | None = None,
        entry_price: float | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        ttl_minutes: int = 60,
    ) -> ExecutionIntent:
        """
        Create an entry intent.

        S27: Intent only — no actual order submission.
        """
        now = datetime.now(UTC)
        self._counter += 1

        intent_id = f"INT-{self.source_module}-{now.strftime('%Y%m%d%H%M%S')}-{self._counter:04d}"

        return ExecutionIntent(
            intent_id=intent_id,
            intent_type=IntentType.ENTRY,
            status=IntentStatus.PENDING,
            created_at=now,
            expires_at=now + timedelta(minutes=ttl_minutes) if ttl_minutes else None,
            symbol=symbol,
            direction=direction,
            size=size,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            source_bead_id=bead_id,
            source_state_hash=state_hash,
        )

    def create_exit_intent(
        self,
        symbol: str,
        direction: Direction,
        size: float,
        state_hash: str,
        bead_id: str | None = None,
    ) -> ExecutionIntent:
        """Create an exit intent."""
        now = datetime.now(UTC)
        self._counter += 1

        intent_id = f"INT-{self.source_module}-{now.strftime('%Y%m%d%H%M%S')}-{self._counter:04d}"

        return ExecutionIntent(
            intent_id=intent_id,
            intent_type=IntentType.EXIT,
            status=IntentStatus.PENDING,
            created_at=now,
            expires_at=None,
            symbol=symbol,
            direction=direction,
            size=size,
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            source_bead_id=bead_id,
            source_state_hash=state_hash,
        )
