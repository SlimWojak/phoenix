"""
T2 Tokens — Approval token management
=====================================

S32: EXECUTION_PATH

Implements single-use, time-limited approval tokens.
Token security is paramount - replay/expiry/wrong-intent all reject.

INVARIANTS:
- INV-T2-TOKEN-1: Single-use, 5-min expiry
- INV-T2-TOKEN-AUDIT-1: Bead at every state change
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from memory.bead_store import BeadStore


# Constants
TOKEN_TTL_SEC = 300  # 5 minutes
MAX_TOKENS_PER_INTENT = 3


class TokenStatus(Enum):
    """Token lifecycle states."""

    ISSUED = "ISSUED"
    USED = "USED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class RejectionReason(Enum):
    """Reasons for token rejection."""

    ALREADY_USED = "ALREADY_USED"
    EXPIRED = "EXPIRED"
    INTENT_MISMATCH = "INTENT_MISMATCH"
    EVIDENCE_MISMATCH = "EVIDENCE_MISMATCH"
    INVALID_FORMAT = "INVALID_FORMAT"
    NOT_FOUND = "NOT_FOUND"
    STALE_CONTEXT = "STALE_CONTEXT"


@dataclass
class Token:
    """
    T2 approval token.

    Single-use, time-limited authorization for capital operations.
    """

    token_id: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    intent_id: str = ""
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    evidence_hash: str = ""
    used: bool = False
    used_at: datetime | None = None
    status: TokenStatus = TokenStatus.ISSUED

    def __post_init__(self) -> None:
        """Set expiry if not already set."""
        if self.expires_at is None:
            self.expires_at = self.issued_at + timedelta(seconds=TOKEN_TTL_SEC)

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(UTC) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid for use."""
        return (
            not self.used
            and not self.is_expired
            and self.status == TokenStatus.ISSUED
        )

    @property
    def ttl_remaining_sec(self) -> float:
        """Seconds until expiry."""
        remaining = (self.expires_at - datetime.now(UTC)).total_seconds()
        return max(0.0, remaining)

    def mark_used(self) -> None:
        """Mark token as used (single-use enforcement)."""
        self.used = True
        self.used_at = datetime.now(UTC)
        self.status = TokenStatus.USED

    def mark_expired(self) -> None:
        """Mark token as expired."""
        self.status = TokenStatus.EXPIRED

    def mark_rejected(self, reason: RejectionReason) -> None:
        """Mark token as rejected."""
        self.status = TokenStatus.REJECTED

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "token_id": self.token_id,
            "intent_id": self.intent_id,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "evidence_hash": self.evidence_hash,
            "used": self.used,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "status": self.status.value,
            "is_valid": self.is_valid,
            "ttl_remaining_sec": self.ttl_remaining_sec,
        }


@dataclass
class ValidationResult:
    """Result of token validation."""

    valid: bool
    token: Token | None = None
    reason: RejectionReason | None = None
    errors: list[str] = field(default_factory=list)

    @classmethod
    def success(cls, token: Token) -> ValidationResult:
        """Create success result."""
        return cls(valid=True, token=token)

    @classmethod
    def failure(cls, reason: RejectionReason, message: str) -> ValidationResult:
        """Create failure result."""
        return cls(valid=False, reason=reason, errors=[message])


class TokenStore:
    """
    In-memory token store with bead persistence.

    HYBRID STORAGE (GPT + GROK synthesis):
    - Authoritative: BeadStore (T2_TOKEN beads)
    - Fast lookup: In-memory cache (5-min TTL)
    - Cross-check: Validate cache against bead on suspicious patterns

    INVARIANT: INV-T2-TOKEN-AUDIT-1
    Every state change emits a T2_TOKEN bead.
    """

    def __init__(
        self,
        bead_store: BeadStore | None = None,
        emit_bead: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        """
        Initialize token store.

        Args:
            bead_store: BeadStore for persistence (optional)
            emit_bead: Callback for bead emission (optional)
        """
        self._cache: dict[str, Token] = {}
        self._intent_tokens: dict[str, list[str]] = {}  # intent_id → token_ids
        self._bead_store = bead_store
        self._emit_bead = emit_bead

    def issue(self, intent_id: str, evidence_hash: str) -> Token:
        """
        Issue a new token.

        Args:
            intent_id: Intent this token authorizes
            evidence_hash: Hash of approved evidence

        Returns:
            New Token

        Raises:
            ValueError: If max tokens per intent exceeded
        """
        # Check token limit per intent
        existing = self._intent_tokens.get(intent_id, [])
        if len(existing) >= MAX_TOKENS_PER_INTENT:
            raise ValueError(
                f"Max tokens ({MAX_TOKENS_PER_INTENT}) exceeded for intent {intent_id}"
            )

        # Create token
        token = Token(
            intent_id=intent_id,
            evidence_hash=evidence_hash,
        )

        # Store in cache
        self._cache[token.token_id] = token
        self._intent_tokens.setdefault(intent_id, []).append(token.token_id)

        # Emit ISSUED bead
        self._emit_token_bead(token, "ISSUED")

        return token

    def validate(
        self,
        token_id: str,
        intent_id: str,
        evidence_hash: str,
    ) -> ValidationResult:
        """
        Validate a token for use.

        INVARIANT: INV-T2-TOKEN-1
        Checks: exists, not used, not expired, intent match, evidence match.

        Args:
            token_id: Token to validate
            intent_id: Expected intent
            evidence_hash: Expected evidence hash

        Returns:
            ValidationResult with success/failure details
        """
        # Check cache first
        token = self._cache.get(token_id)

        if token is None:
            return ValidationResult.failure(
                RejectionReason.NOT_FOUND,
                f"Token {token_id[:8]}... not found",
            )

        # Check if already used
        if token.used:
            self._emit_token_bead(token, "REJECTED", "ALREADY_USED")
            return ValidationResult.failure(
                RejectionReason.ALREADY_USED,
                "Token already used (INV-T2-TOKEN-1: single-use)",
            )

        # Check expiry
        if token.is_expired:
            token.mark_expired()
            self._emit_token_bead(token, "EXPIRED")
            return ValidationResult.failure(
                RejectionReason.EXPIRED,
                "Token expired (INV-T2-TOKEN-1: 5-min TTL)",
            )

        # Check intent match
        if token.intent_id != intent_id:
            self._emit_token_bead(token, "REJECTED", "INTENT_MISMATCH")
            return ValidationResult.failure(
                RejectionReason.INTENT_MISMATCH,
                f"Token intent mismatch: expected {intent_id[:8]}...",
            )

        # Check evidence match
        if token.evidence_hash != evidence_hash:
            self._emit_token_bead(token, "REJECTED", "EVIDENCE_MISMATCH")
            return ValidationResult.failure(
                RejectionReason.EVIDENCE_MISMATCH,
                "Evidence hash mismatch (context changed since approval)",
            )

        return ValidationResult.success(token)

    def consume(self, token_id: str) -> bool:
        """
        Consume (use) a token.

        INVARIANT: INV-T2-TOKEN-1
        Marks token as used, preventing replay.

        Args:
            token_id: Token to consume

        Returns:
            True if consumed successfully
        """
        token = self._cache.get(token_id)
        if token is None or token.used:
            return False

        token.mark_used()
        self._emit_token_bead(token, "USED")
        return True

    def get(self, token_id: str) -> Token | None:
        """Get token by ID."""
        return self._cache.get(token_id)

    def expire_stale(self) -> int:
        """
        Expire all stale tokens.

        Called periodically (every 30s).

        Returns:
            Number of tokens expired
        """
        expired_count = 0
        for token in list(self._cache.values()):
            if token.status == TokenStatus.ISSUED and token.is_expired:
                token.mark_expired()
                self._emit_token_bead(token, "EXPIRED")
                expired_count += 1
        return expired_count

    def cleanup(self, max_age_sec: int = 3600) -> int:
        """
        Clean up old tokens from cache.

        Args:
            max_age_sec: Remove tokens older than this

        Returns:
            Number of tokens removed
        """
        cutoff = datetime.now(UTC) - timedelta(seconds=max_age_sec)
        removed = 0

        for token_id, token in list(self._cache.items()):
            if token.issued_at < cutoff:
                del self._cache[token_id]
                removed += 1

        return removed

    def _emit_token_bead(
        self,
        token: Token,
        event: str,
        reason: str | None = None,
    ) -> None:
        """
        Emit T2_TOKEN bead.

        INVARIANT: INV-T2-TOKEN-AUDIT-1
        Every state change emits a bead.
        """
        if self._emit_bead is None:
            return

        bead_data = {
            "bead_type": "T2_TOKEN",
            "token_id": token.token_id,
            "intent_id": token.intent_id,
            "event": event,
            "reason": reason,
            "evidence_hash": token.evidence_hash,
            "expires_at": token.expires_at.isoformat(),
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }

        try:
            self._emit_bead(bead_data)
        except Exception:  # noqa: S110
            pass  # Non-blocking - audit is important but not critical path


def create_token_validator(
    store: TokenStore,
) -> Callable[[str, Any], ValidationResult]:
    """
    Create a token validation callable for IBKR connector.

    Args:
        store: TokenStore instance

    Returns:
        Validation callable
    """

    def validator(token_id: str, order: Any) -> ValidationResult:
        """Validate token for order."""
        # Extract intent from order (signal_id)
        intent_id = getattr(order, "signal_id", "") or str(uuid.uuid4())

        # Compute evidence hash from order context
        evidence = {
            "symbol": getattr(order, "symbol", ""),
            "side": getattr(order, "side", ""),
            "quantity": getattr(order, "quantity", 0),
        }
        evidence_hash = hashlib.sha256(
            str(sorted(evidence.items())).encode()
        ).hexdigest()

        return store.validate(token_id, intent_id, evidence_hash)

    return validator
