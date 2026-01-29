"""
Multi-Pair Scanner — S36 Track D
================================

Scan all pairs simultaneously.
Output SHUFFLED — never by "quality" or gate count.

INVARIANTS:
  - INV-DISPLAY-SHUFFLE: Randomized order prevents position bias
  - INV-CSO-BUDGET: max_pairs=12 default
  - INV-ATTR-NO-RANKING: No implied priority
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_MAX_PAIRS = 12
DEFAULT_PAIRS = ["AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF"]


class SortOrder(Enum):
    """Sort order for multi-pair results."""

    RANDOMIZED_ALPHABETICAL = "randomized_alphabetical"
    STRICT_RANDOM = "strict_random"


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class PairResult:
    """Result for a single pair."""

    pair: str
    gates_passed: list[str]
    gates_failed: list[str]
    gates_skipped: list[str]
    drawer_status: dict[int, bool]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class MultiPairScan:
    """
    Multi-pair scan result.

    FORBIDDEN: Any sort by gate count or quality.
    """

    timestamp: datetime
    results: list[PairResult]
    sort_order: SortOrder
    sort_seed: str
    pairs_requested: int
    pairs_scanned: int

    # FORBIDDEN: Do not add these fields
    # - ranked_pairs
    # - top_pairs
    # - best_pairs
    # - quality_sorted


@dataclass
class BudgetError:
    """Error when budget exceeded."""

    requested: int
    limit: int
    message: str


# =============================================================================
# MULTI-PAIR SCANNER
# =============================================================================


class MultiPairScanner:
    """
    Scans multiple pairs and returns shuffled results.

    FORBIDDEN:
      - Sort by gates_passed count
      - Sort by "quality"
      - Any ranking

    Usage:
        scanner = MultiPairScanner()
        result = scanner.scan(pairs, evaluator, market_states, strategy_hash)
    """

    def __init__(
        self,
        max_pairs: int = DEFAULT_MAX_PAIRS,
        sort_order: SortOrder = SortOrder.RANDOMIZED_ALPHABETICAL,
    ) -> None:
        """
        Initialize scanner.

        Args:
            max_pairs: Maximum pairs (12 default, T2 for override)
            sort_order: How to order results (always randomized)
        """
        self._max_pairs = max_pairs
        self._sort_order = sort_order

    def check_budget(self, pairs: list[str]) -> BudgetError | None:
        """
        Check if request exceeds budget.

        Args:
            pairs: Requested pairs

        Returns:
            BudgetError if exceeded, None otherwise
        """
        if len(pairs) > self._max_pairs:
            return BudgetError(
                requested=len(pairs),
                limit=self._max_pairs,
                message=(
                    f"BUDGET_EXCEEDED: Requested {len(pairs)} pairs, "
                    f"limit is {self._max_pairs}. T2 required for override."
                ),
            )
        return None

    def shuffle_results(
        self,
        results: list[PairResult],
        seed: str | None = None,
    ) -> tuple[list[PairResult], str]:
        """
        Shuffle results to prevent position bias.

        RANDOMIZED_ALPHABETICAL: Random starting letter, then alpha
        STRICT_RANDOM: Complete randomization

        Args:
            results: Results to shuffle
            seed: Optional seed for reproducibility

        Returns:
            (shuffled_results, seed_used)
        """
        if seed is None:
            seed = secrets.token_hex(8)

        rng = secrets.SystemRandom()
        pairs = [r.pair for r in results]

        if self._sort_order == SortOrder.RANDOMIZED_ALPHABETICAL:
            # Random starting letter, then alphabetical
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            start_letter = rng.choice(alphabet)
            start_idx = alphabet.index(start_letter)
            rotated = alphabet[start_idx:] + alphabet[:start_idx]

            # Sort by rotated alphabet
            sorted_pairs = sorted(
                pairs, key=lambda p: rotated.index(p[0]) if p[0] in rotated else 99
            )
            pair_to_result = {r.pair: r for r in results}
            shuffled = [pair_to_result[p] for p in sorted_pairs]

        else:  # STRICT_RANDOM
            shuffled = list(results)
            rng.shuffle(shuffled)

        return shuffled, seed

    def scan(
        self,
        pair_results: list[PairResult],
    ) -> MultiPairScan | BudgetError:
        """
        Create multi-pair scan from individual results.

        Args:
            pair_results: Results from individual pair evaluations

        Returns:
            MultiPairScan (shuffled) or BudgetError
        """
        # Check budget
        pairs = [r.pair for r in pair_results]
        budget_error = self.check_budget(pairs)
        if budget_error:
            return budget_error

        # Shuffle results
        shuffled, seed = self.shuffle_results(pair_results)

        return MultiPairScan(
            timestamp=datetime.now(UTC),
            results=shuffled,
            sort_order=self._sort_order,
            sort_seed=seed,
            pairs_requested=len(pairs),
            pairs_scanned=len(shuffled),
        )


# =============================================================================
# VALIDATION
# =============================================================================


def validate_sort_request(sort_by: str) -> tuple[bool, str]:
    """
    Validate a sort request.

    FORBIDDEN: Sort by gate count or quality.

    Args:
        sort_by: Requested sort field

    Returns:
        (valid, error_message)
    """
    forbidden = [
        "gates_passed_count",
        "gates_count",
        "count",
        "quality",
        "score",
        "best",
        "top",
        "rank",
    ]

    sort_lower = sort_by.lower()
    for f in forbidden:
        if f in sort_lower:
            return (
                False,
                f"Sort by '{sort_by}' forbidden. "
                "Only randomized_alphabetical or strict_random allowed.",
            )

    return (True, "")


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "MultiPairScanner",
    "MultiPairScan",
    "PairResult",
    "SortOrder",
    "BudgetError",
    "validate_sort_request",
    "DEFAULT_MAX_PAIRS",
    "DEFAULT_PAIRS",
]
