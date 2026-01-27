"""
Approval Tokens — T2 authorization mechanism

VERSION: 0.2
CONTRACT: GOVERNANCE_INTERFACE_CONTRACT.md

INVARIANTS:
  INV-GOV-HALT-BEFORE-ACTION: gate checks halt_signal before capital-affecting submit
"""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .errors import (
    HaltBlocksActionError,
    TokenExpiredError,
    TokenScopeError,
    TokenStateMismatchError,
)
from .halt import HaltSignal

# =============================================================================
# APPROVAL TOKEN
# =============================================================================


@dataclass
class ApprovalToken:
    """
    T2 approval token for capital-affecting actions.

    Validation requirements:
    - token not expired
    - state_hash matches current
    - halt_signal == FALSE
    - scope includes requested action
    """

    issued_by: str  # human_id
    issued_at: datetime
    expires_at: datetime
    scope: list[str]  # action_types permitted
    state_hash: str  # must match compute_state_hash()

    token_id: str = field(default="")

    def __post_init__(self):
        if not self.token_id:
            # Generate token ID from content hash
            content = f"{self.issued_by}|{self.issued_at}|{self.state_hash}"
            self.token_id = hashlib.sha256(content.encode()).hexdigest()[:12]

    def is_expired(self, now: datetime | None = None) -> bool:
        """Check if token has expired."""
        if now is None:
            now = datetime.now(UTC)
        return now >= self.expires_at

    def has_scope(self, action: str) -> bool:
        """Check if action is in token scope."""
        return action in self.scope or "*" in self.scope

    def to_dict(self) -> dict:
        return {
            "token_id": self.token_id,
            "issued_by": self.issued_by,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "scope": self.scope,
            "state_hash": self.state_hash,
        }


# =============================================================================
# TOKEN VALIDATOR
# =============================================================================


class TokenValidator:
    """
    Validates approval tokens for T2 actions.

    Enforces INV-GOV-HALT-BEFORE-ACTION.
    """

    def __init__(self, halt_signal: HaltSignal, state_hash_fn: callable):
        """
        Args:
            halt_signal: HaltSignal instance to check
            state_hash_fn: Function that returns current state hash
        """
        self.halt_signal = halt_signal
        self.state_hash_fn = state_hash_fn

    def validate(self, token: ApprovalToken, action: str, now: datetime | None = None) -> bool:
        """
        Validate token for a specific action.

        Checks:
        1. halt_signal == FALSE (INV-GOV-HALT-BEFORE-ACTION)
        2. token not expired
        3. state_hash matches current
        4. scope includes action

        Raises:
            HaltBlocksActionError: if halt signal is set
            TokenExpiredError: if token is expired
            TokenStateMismatchError: if state hash doesn't match
            TokenScopeError: if action not in scope

        Returns:
            True if validation passes
        """
        if now is None:
            now = datetime.now(UTC)

        # Check 1: Halt signal (INV-GOV-HALT-BEFORE-ACTION)
        if self.halt_signal.is_set():
            raise HaltBlocksActionError(
                action=action, halt_id=self.halt_signal.halt_id or "unknown"
            )

        # Check 2: Expiration
        if token.is_expired(now):
            raise TokenExpiredError(f"Token {token.token_id} expired at {token.expires_at}")

        # Check 3: State hash
        current_hash = self.state_hash_fn()
        if token.state_hash != current_hash:
            raise TokenStateMismatchError(token_hash=token.state_hash, current_hash=current_hash)

        # Check 4: Scope
        if not token.has_scope(action):
            raise TokenScopeError(f"Action '{action}' not in token scope {token.scope}")

        return True


# =============================================================================
# TOKEN ISSUER (for testing/simulation)
# =============================================================================


class TokenIssuer:
    """
    Issues approval tokens.

    In production, this would integrate with human approval flow.
    For testing, allows programmatic token generation.
    """

    def __init__(self, issuer_id: str = "test_sovereign"):
        self.issuer_id = issuer_id

    def issue(
        self,
        state_hash: str,
        scope: list[str],
        duration_seconds: int = 3600,
        now: datetime | None = None,
    ) -> ApprovalToken:
        """
        Issue a new approval token.

        Args:
            state_hash: Current state hash
            scope: List of permitted actions
            duration_seconds: Token validity duration
            now: Current time (for testing)

        Returns:
            New ApprovalToken
        """
        from datetime import timedelta

        if now is None:
            now = datetime.now(UTC)

        return ApprovalToken(
            issued_by=self.issuer_id,
            issued_at=now,
            expires_at=now + timedelta(seconds=duration_seconds),
            scope=scope,
            state_hash=state_hash,
        )
