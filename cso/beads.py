"""
CSO Beads — DRAFT-only decision artifacts.

SPRINT: S27.0
STATUS: SCAFFOLD

Beads are immutable decision records.
In S27, CSO can ONLY create DRAFT beads (not CERTIFIED).

INVARIANTS:
- INV-DYNASTY-5: Bead immutability post-creation
- INV-CSO-DRAFT-ONLY: S27 CSO emits DRAFT beads only
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

# =============================================================================
# EXCEPTIONS
# =============================================================================


class ImmutabilityViolation(Exception):
    """Raised when attempting to mutate a frozen bead."""

    def __init__(self, bead_id: str, field: str):
        self.bead_id = bead_id
        self.field = field
        super().__init__(f"Cannot mutate field '{field}' on frozen bead {bead_id}")


class BeadStatusViolation(Exception):
    """Raised when creating non-DRAFT bead in S27."""

    def __init__(self, attempted_status: str):
        self.attempted_status = attempted_status
        super().__init__(f"S27 CSO can only create DRAFT beads, not {attempted_status}")


# =============================================================================
# BEAD TYPES
# =============================================================================


class BeadStatus(Enum):
    """Bead lifecycle status."""

    DRAFT = "DRAFT"  # Created by CSO, not yet reviewed
    CERTIFIED = "CERTIFIED"  # Human-approved (NOT allowed in S27)
    REJECTED = "REJECTED"  # Human-rejected
    EXPIRED = "EXPIRED"  # Past TTL without certification


class BeadType(Enum):
    """Type of bead content."""

    DECISION = "DECISION"  # Trade direction decision
    OBSERVATION = "OBSERVATION"  # Market observation
    INSIGHT = "INSIGHT"  # Pattern recognition
    COMPREHENSION = "COMPREHENSION"  # Understanding confirmation


# =============================================================================
# BEAD DATA CLASS
# =============================================================================


@dataclass
class Bead:
    """
    Immutable decision/observation artifact.

    Once created, fields CANNOT be modified (INV-DYNASTY-5).
    The only exception is outcome fields, which can be SET once (not modified).
    """

    # Identity
    bead_id: str
    bead_type: BeadType
    status: BeadStatus

    # Timing
    created_at: datetime
    expires_at: datetime | None

    # Content
    symbol: str
    content: dict
    comprehension_hash: str

    # Source
    source_module: str
    source_state_hash: str

    # Outcome (can be set once, not modified)
    outcome: dict | None = None
    outcome_set_at: datetime | None = None

    # Immutability flag
    _frozen: bool = field(default=False, repr=False)

    def __post_init__(self):
        """Freeze bead after creation."""
        # Validate S27 constraint: DRAFT only
        if self.status != BeadStatus.DRAFT:
            raise BeadStatusViolation(self.status.value)

        # Compute comprehension hash if not provided
        if not self.comprehension_hash:
            object.__setattr__(self, "comprehension_hash", self._compute_hash())

        # Freeze
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name: str, value) -> None:
        """Enforce immutability."""
        if hasattr(self, "_frozen") and self._frozen:
            # Allow setting outcome ONCE
            if name == "outcome" and self.outcome is None:
                object.__setattr__(self, "outcome", value)
                object.__setattr__(self, "outcome_set_at", datetime.now(UTC))
                return
            raise ImmutabilityViolation(self.bead_id, name)
        object.__setattr__(self, name, value)

    def _compute_hash(self) -> str:
        """Compute comprehension hash from content."""
        hashable = {
            "bead_type": self.bead_type.value,
            "symbol": self.symbol,
            "content": self.content,
            "source_state_hash": self.source_state_hash,
        }
        canonical = json.dumps(hashable, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        """Serialize to dict (for storage)."""
        return {
            "bead_id": self.bead_id,
            "bead_type": self.bead_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "symbol": self.symbol,
            "content": self.content,
            "comprehension_hash": self.comprehension_hash,
            "source_module": self.source_module,
            "source_state_hash": self.source_state_hash,
            "outcome": self.outcome,
            "outcome_set_at": self.outcome_set_at.isoformat() if self.outcome_set_at else None,
        }


# =============================================================================
# BEAD FACTORY
# =============================================================================


class BeadFactory:
    """
    Factory for creating DRAFT beads.

    S27 CONSTRAINT: Can only create DRAFT beads.
    """

    def __init__(self, source_module: str):
        self.source_module = source_module
        self._counter = 0

    def create_decision_bead(
        self,
        symbol: str,
        direction: str,
        confidence: float,
        gate_result: dict,
        state_hash: str,
        ttl_hours: int = 24,
    ) -> Bead:
        """
        Create a DRAFT decision bead.

        Args:
            symbol: Trading symbol
            direction: LONG/SHORT/NEUTRAL
            confidence: 0.0-1.0
            gate_result: 4Q gate evaluation
            state_hash: Source state hash
            ttl_hours: Time to live (default 24h)

        Returns:
            Frozen DRAFT bead
        """
        now = datetime.now(UTC)
        self._counter += 1

        bead_id = f"BEA-{self.source_module}-{now.strftime('%Y%m%d%H%M%S')}-{self._counter:04d}"

        content = {
            "direction": direction,
            "confidence": confidence,
            "gate_result": gate_result,
        }

        from datetime import timedelta

        return Bead(
            bead_id=bead_id,
            bead_type=BeadType.DECISION,
            status=BeadStatus.DRAFT,  # ALWAYS DRAFT in S27
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours) if ttl_hours else None,
            symbol=symbol,
            content=content,
            comprehension_hash="",  # Computed in __post_init__
            source_module=self.source_module,
            source_state_hash=state_hash,
        )

    def create_observation_bead(
        self, symbol: str, observation_type: str, details: dict, state_hash: str
    ) -> Bead:
        """Create a DRAFT observation bead."""
        now = datetime.now(UTC)
        self._counter += 1

        bead_id = f"BEA-{self.source_module}-{now.strftime('%Y%m%d%H%M%S')}-{self._counter:04d}"

        content = {
            "observation_type": observation_type,
            "details": details,
        }

        return Bead(
            bead_id=bead_id,
            bead_type=BeadType.OBSERVATION,
            status=BeadStatus.DRAFT,
            created_at=now,
            expires_at=None,
            symbol=symbol,
            content=content,
            comprehension_hash="",
            source_module=self.source_module,
            source_state_hash=state_hash,
        )

    def create_comprehension_bead(self, symbol: str, understanding: dict, state_hash: str) -> Bead:
        """Create a DRAFT comprehension bead (intertwine response)."""
        now = datetime.now(UTC)
        self._counter += 1

        bead_id = f"BEA-{self.source_module}-{now.strftime('%Y%m%d%H%M%S')}-{self._counter:04d}"

        return Bead(
            bead_id=bead_id,
            bead_type=BeadType.COMPREHENSION,
            status=BeadStatus.DRAFT,
            created_at=now,
            expires_at=None,
            symbol=symbol,
            content=understanding,
            comprehension_hash="",
            source_module=self.source_module,
            source_state_hash=state_hash,
        )
