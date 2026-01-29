"""
Athena Rate Limiter — S37 Track B
=================================

Prevents calibration storms (1000+ beads in one session).
Reuses S36 AlertRateLimiter pattern.

INVARIANTS:
  - max_claims_per_hour: 100
  - max_facts_per_hour: 500
  - max_conflicts_per_hour: 50 (per domain)
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum


# =============================================================================
# CONSTANTS
# =============================================================================

MAX_CLAIMS_PER_HOUR = 100
MAX_FACTS_PER_HOUR = 500
MAX_CONFLICTS_PER_HOUR = 50  # per domain


class RateLimitType(str, Enum):
    """Types of rate limits."""

    CLAIM = "CLAIM"
    FACT = "FACT"
    CONFLICT = "CONFLICT"


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    reason: str = ""
    remaining: int = 0
    reset_in_seconds: int = 0


# =============================================================================
# RATE LIMITER
# =============================================================================


class AthenaRateLimiter:
    """
    Rate limits bead storage operations.

    Prevents calibration storms:
    - 100 claims/hour
    - 500 facts/hour
    - 50 conflicts/hour (per domain)
    """

    def __init__(
        self,
        max_claims: int = MAX_CLAIMS_PER_HOUR,
        max_facts: int = MAX_FACTS_PER_HOUR,
        max_conflicts: int = MAX_CONFLICTS_PER_HOUR,
    ) -> None:
        """Initialize rate limiter."""
        self._max_claims = max_claims
        self._max_facts = max_facts
        self._max_conflicts = max_conflicts

        # Timestamps of recent operations
        self._claim_times: deque[datetime] = deque(maxlen=200)
        self._fact_times: deque[datetime] = deque(maxlen=1000)
        self._conflict_times: dict[str, deque[datetime]] = defaultdict(
            lambda: deque(maxlen=100)
        )

    def _clean_old_entries(
        self,
        times: deque[datetime],
        window: timedelta = timedelta(hours=1),
    ) -> deque[datetime]:
        """Remove entries older than window."""
        now = datetime.now(UTC)
        cutoff = now - window
        return deque((t for t in times if t > cutoff), maxlen=times.maxlen)

    def check_claim(self) -> RateLimitResult:
        """
        Check if a claim can be stored.

        Returns:
            RateLimitResult
        """
        self._claim_times = self._clean_old_entries(self._claim_times)

        if len(self._claim_times) >= self._max_claims:
            oldest = min(self._claim_times)
            reset_in = int((oldest + timedelta(hours=1) - datetime.now(UTC)).total_seconds())
            return RateLimitResult(
                allowed=False,
                reason=f"RATE_LIMIT: {self._max_claims} claims/hour exceeded",
                remaining=0,
                reset_in_seconds=max(0, reset_in),
            )

        return RateLimitResult(
            allowed=True,
            remaining=self._max_claims - len(self._claim_times),
        )

    def record_claim(self) -> None:
        """Record a claim storage."""
        self._claim_times.append(datetime.now(UTC))

    def check_fact(self) -> RateLimitResult:
        """
        Check if a fact can be stored.

        Returns:
            RateLimitResult
        """
        self._fact_times = self._clean_old_entries(self._fact_times)

        if len(self._fact_times) >= self._max_facts:
            oldest = min(self._fact_times)
            reset_in = int((oldest + timedelta(hours=1) - datetime.now(UTC)).total_seconds())
            return RateLimitResult(
                allowed=False,
                reason=f"RATE_LIMIT: {self._max_facts} facts/hour exceeded",
                remaining=0,
                reset_in_seconds=max(0, reset_in),
            )

        return RateLimitResult(
            allowed=True,
            remaining=self._max_facts - len(self._fact_times),
        )

    def record_fact(self) -> None:
        """Record a fact storage."""
        self._fact_times.append(datetime.now(UTC))

    def check_conflict(self, domain: str) -> RateLimitResult:
        """
        Check if a conflict can be stored for a domain.

        Args:
            domain: The conflict domain

        Returns:
            RateLimitResult
        """
        self._conflict_times[domain] = self._clean_old_entries(
            self._conflict_times[domain]
        )

        if len(self._conflict_times[domain]) >= self._max_conflicts:
            oldest = min(self._conflict_times[domain])
            reset_in = int((oldest + timedelta(hours=1) - datetime.now(UTC)).total_seconds())
            return RateLimitResult(
                allowed=False,
                reason=f"RATE_LIMIT: {self._max_conflicts} conflicts/hour in domain '{domain}' exceeded",
                remaining=0,
                reset_in_seconds=max(0, reset_in),
            )

        return RateLimitResult(
            allowed=True,
            remaining=self._max_conflicts - len(self._conflict_times[domain]),
        )

    def record_conflict(self, domain: str) -> None:
        """Record a conflict storage for a domain."""
        self._conflict_times[domain].append(datetime.now(UTC))


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "AthenaRateLimiter",
    "RateLimitResult",
    "RateLimitType",
    "MAX_CLAIMS_PER_HOUR",
    "MAX_FACTS_PER_HOUR",
    "MAX_CONFLICTS_PER_HOUR",
]
