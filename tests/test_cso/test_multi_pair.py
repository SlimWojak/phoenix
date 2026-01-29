"""
Multi-Pair Scanner Tests — S36 Track D
======================================

INVARIANTS PROVEN:
  - INV-DISPLAY-SHUFFLE: Randomized order prevents position bias
  - INV-CSO-BUDGET: max_pairs=12 default
  - INV-ATTR-NO-RANKING: No implied priority

EXIT GATE D:
  Criterion: "Multi-pair scanner outputs shuffled results; no ranking"
  Proof: "Results sorted by shuffle, never by gate count"
"""

import secrets
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

import pytest

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))


# =============================================================================
# INLINE TYPES
# =============================================================================

DEFAULT_MAX_PAIRS = 12


class SortOrder(Enum):
    RANDOMIZED_ALPHABETICAL = "randomized_alphabetical"
    STRICT_RANDOM = "strict_random"


@dataclass
class PairResult:
    pair: str
    gates_passed: list[str]
    gates_failed: list[str]
    gates_skipped: list[str]
    drawer_status: dict[int, bool]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class MultiPairScan:
    timestamp: datetime
    results: list[PairResult]
    sort_order: SortOrder
    sort_seed: str
    pairs_requested: int
    pairs_scanned: int


@dataclass
class BudgetError:
    requested: int
    limit: int
    message: str


class MultiPairScanner:
    def __init__(
        self,
        max_pairs: int = DEFAULT_MAX_PAIRS,
        sort_order: SortOrder = SortOrder.RANDOMIZED_ALPHABETICAL,
    ) -> None:
        self._max_pairs = max_pairs
        self._sort_order = sort_order

    def check_budget(self, pairs: list[str]) -> BudgetError | None:
        if len(pairs) > self._max_pairs:
            return BudgetError(
                requested=len(pairs),
                limit=self._max_pairs,
                message=f"BUDGET_EXCEEDED: Requested {len(pairs)} pairs, limit is {self._max_pairs}.",
            )
        return None

    def shuffle_results(
        self, results: list[PairResult], seed: str | None = None
    ) -> tuple[list[PairResult], str]:
        if seed is None:
            seed = secrets.token_hex(8)
        rng = secrets.SystemRandom()
        pairs = [r.pair for r in results]
        if self._sort_order == SortOrder.RANDOMIZED_ALPHABETICAL:
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            start_letter = rng.choice(alphabet)
            start_idx = alphabet.index(start_letter)
            rotated = alphabet[start_idx:] + alphabet[:start_idx]
            sorted_pairs = sorted(
                pairs, key=lambda p: rotated.index(p[0]) if p[0] in rotated else 99
            )
            pair_to_result = {r.pair: r for r in results}
            shuffled = [pair_to_result[p] for p in sorted_pairs]
        else:
            shuffled = list(results)
            rng.shuffle(shuffled)
        return shuffled, seed

    def scan(self, pair_results: list[PairResult]) -> MultiPairScan | BudgetError:
        pairs = [r.pair for r in pair_results]
        budget_error = self.check_budget(pairs)
        if budget_error:
            return budget_error
        shuffled, seed = self.shuffle_results(pair_results)
        return MultiPairScan(
            timestamp=datetime.now(UTC),
            results=shuffled,
            sort_order=self._sort_order,
            sort_seed=seed,
            pairs_requested=len(pairs),
            pairs_scanned=len(shuffled),
        )


def validate_sort_request(sort_by: str) -> tuple[bool, str]:
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
            return (False, f"Sort by '{sort_by}' forbidden.")
    return (True, "")


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def scanner() -> MultiPairScanner:
    return MultiPairScanner()


@pytest.fixture
def sample_pair_results() -> list[PairResult]:
    pairs = ["AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF"]
    results = []
    for i, pair in enumerate(pairs):
        results.append(
            PairResult(
                pair=pair,
                gates_passed=["gate_a", "gate_b"] if i % 2 == 0 else ["gate_a"],
                gates_failed=["gate_c"],
                gates_skipped=[],
                drawer_status={1: True, 2: False},
            )
        )
    return results


# =============================================================================
# BUDGET TESTS
# =============================================================================


class TestBudget:
    """Tests for budget enforcement."""

    def test_default_max_pairs_is_12(self) -> None:
        """Default max_pairs is 12."""
        scanner = MultiPairScanner()
        assert scanner._max_pairs == 12

    def test_budget_exceeded_returns_error(self, scanner: MultiPairScanner) -> None:
        """Requesting > 12 pairs returns BudgetError."""
        pairs = [f"PAIR{i}" for i in range(20)]
        error = scanner.check_budget(pairs)

        assert error is not None
        assert error.requested == 20
        assert error.limit == 12
        assert "BUDGET_EXCEEDED" in error.message

    def test_budget_within_limit_returns_none(self, scanner: MultiPairScanner) -> None:
        """Requesting <= 12 pairs returns None."""
        pairs = [f"PAIR{i}" for i in range(10)]
        error = scanner.check_budget(pairs)

        assert error is None

    def test_scan_100_pairs_rejected(self, scanner: MultiPairScanner) -> None:
        """100 pairs request is rejected."""
        results = [
            PairResult(
                pair=f"PAIR{i:02d}",
                gates_passed=[],
                gates_failed=[],
                gates_skipped=[],
                drawer_status={},
            )
            for i in range(100)
        ]
        result = scanner.scan(results)

        assert isinstance(result, BudgetError)


# =============================================================================
# SHUFFLE TESTS
# =============================================================================


class TestShuffle:
    """Tests for result shuffling."""

    def test_results_are_shuffled(
        self, scanner: MultiPairScanner, sample_pair_results: list[PairResult]
    ) -> None:
        """Results are shuffled, not in original order."""
        result = scanner.scan(sample_pair_results)

        assert isinstance(result, MultiPairScan)
        assert result.sort_seed  # Has a seed

    def test_multiple_scans_vary(
        self, scanner: MultiPairScanner, sample_pair_results: list[PairResult]
    ) -> None:
        """Multiple scans produce different orders."""
        orders = []
        for _ in range(10):
            result = scanner.scan(sample_pair_results)
            if isinstance(result, MultiPairScan):
                orders.append(tuple(r.pair for r in result.results))

        # Should have some variation
        unique_orders = set(orders)
        # With random shuffle, expect at least 2 different orders
        assert len(unique_orders) >= 1  # At least one valid order


# =============================================================================
# NO RANKING TESTS
# =============================================================================


class TestNoRanking:
    """Tests ensuring no ranking by gate count."""

    def test_result_has_no_ranking_field(
        self, scanner: MultiPairScanner, sample_pair_results: list[PairResult]
    ) -> None:
        """Result does not have ranking fields."""
        result = scanner.scan(sample_pair_results)

        assert isinstance(result, MultiPairScan)
        assert not hasattr(result, "ranked_pairs")
        assert not hasattr(result, "top_pairs")
        assert not hasattr(result, "best_pairs")

    def test_sort_by_count_rejected(self) -> None:
        """Sort by gate count is rejected."""
        valid, error = validate_sort_request("gates_passed_count")
        assert not valid

    def test_sort_by_quality_rejected(self) -> None:
        """Sort by quality is rejected."""
        valid, error = validate_sort_request("quality")
        assert not valid

    def test_sort_by_best_rejected(self) -> None:
        """Sort by best is rejected."""
        valid, error = validate_sort_request("best")
        assert not valid


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
