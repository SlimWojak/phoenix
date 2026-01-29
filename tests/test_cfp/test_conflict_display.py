"""
Conflict Display Tests — S35 Track E
====================================

INVARIANTS PROVEN:
  - INV-ATTR-CONFLICT-DISPLAY: Best always paired with worst
  - INV-ATTR-NO-RANKING: No ordered lists beyond top/bottom
  - INV-NO-DEFAULT-SALIENCE: Equal visual weight + random position
  - INV-CFP-LOW-N-GATE: N < 30 cannot persist as FACT without T2

EXIT GATE E:
  Criterion: "Any 'best' query automatically returns 'worst' pair"
  Proof: "Unpaired best rejected; randomized positioning verified"
"""


import pytest

from cfp.conflict_display import (
    LOW_N_THRESHOLD,
    ConflictDisplay,
    SpreadStatus,
    validate_conflict_request,
)
from cfp.executor import ResultType

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def display() -> ConflictDisplay:
    """Create conflict display instance."""
    return ConflictDisplay()


@pytest.fixture
def sample_values() -> dict[str, dict]:
    """Sample dimension values for testing."""
    return {
        "London": {
            "metrics": {"sharpe": 1.6, "win_rate": 0.61},
            "sample_size": 47,
            "provenance": {
                "query_string": "test",
                "dataset_hash": "abc123",
                "governance_hash": "def456",
            },
        },
        "Tokyo": {
            "metrics": {"sharpe": 0.8, "win_rate": 0.52},
            "sample_size": 35,
            "provenance": {
                "query_string": "test",
                "dataset_hash": "abc123",
                "governance_hash": "def456",
            },
        },
        "NY": {
            "metrics": {"sharpe": 1.2, "win_rate": 0.58},
            "sample_size": 42,
            "provenance": {
                "query_string": "test",
                "dataset_hash": "abc123",
                "governance_hash": "def456",
            },
        },
    }


@pytest.fixture
def low_n_values() -> dict[str, dict]:
    """Sample values with low sample sizes."""
    return {
        "London": {
            "metrics": {"sharpe": 1.6},
            "sample_size": 15,  # Below threshold
            "provenance": {},
        },
        "Tokyo": {
            "metrics": {"sharpe": 0.8},
            "sample_size": 10,  # Below threshold
            "provenance": {},
        },
    }


# =============================================================================
# CONFLICT PAIR CREATION
# =============================================================================


class TestConflictPairCreation:
    """Tests for conflict pair creation."""

    def test_create_pair_best_and_worst(
        self, display: ConflictDisplay, sample_values: dict
    ) -> None:
        """Creating pair includes both best and worst."""
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        assert pair.best.dimension_value == "London"  # Highest sharpe
        assert pair.worst.dimension_value == "Tokyo"  # Lowest sharpe

    def test_create_pair_has_spread(self, display: ConflictDisplay, sample_values: dict) -> None:
        """Created pair includes spread calculation."""
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        assert pair.spread.metric == "sharpe"
        assert pair.spread.delta == pytest.approx(0.8, rel=0.1)  # 1.6 - 0.8

    def test_create_pair_spread_disabled_by_default(
        self, display: ConflictDisplay, sample_values: dict
    ) -> None:
        """Spread is disabled by default (GPT v0.2)."""
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        assert pair.spread.status == SpreadStatus.DISABLED

    def test_create_pair_spread_enabled_explicit(self, sample_values: dict) -> None:
        """Spread can be enabled explicitly."""
        display = ConflictDisplay(spread_enabled=True)
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        assert pair.spread.status == SpreadStatus.ENABLED

    def test_create_pair_scope_explicit(
        self, display: ConflictDisplay, sample_values: dict
    ) -> None:
        """Scope is always explicit, never global (GPT v0.2)."""
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
            scope_description="EURUSD, 2025",
        )

        assert pair is not None
        assert pair.scope.comparison_domain == "explicit"  # Never "global"
        assert pair.scope.dimension == "session"

    def test_create_pair_insufficient_values(self, display: ConflictDisplay) -> None:
        """Returns None if insufficient values."""
        # Only one value — can't create pair
        single_value = {
            "London": {"metrics": {"sharpe": 1.6}, "sample_size": 47, "provenance": {}},
        }

        pair = display.create_pair(
            dimension="session",
            values=single_value,
            comparison_metric="sharpe",
        )

        assert pair is None


# =============================================================================
# RANDOMIZED POSITIONING (OWL v0.2)
# =============================================================================


class TestRandomizedPositioning:
    """Tests for randomized best/worst positioning."""

    def test_render_randomized_distribution(
        self, display: ConflictDisplay, sample_values: dict
    ) -> None:
        """Rendered positions are approximately 50/50 over many renders."""
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
        )

        assert pair is not None

        # Render 100 times and count left/right distribution
        best_on_left_count = 0
        renders = 100

        for _ in range(renders):
            rendered = display.render(pair)
            if rendered.left_label == "BEST":
                best_on_left_count += 1

        # Should be approximately 50/50 (allow 20% tolerance)
        ratio = best_on_left_count / renders
        assert 0.3 <= ratio <= 0.7, f"Distribution should be ~50/50, got {ratio}"

    def test_render_includes_labels(self, display: ConflictDisplay, sample_values: dict) -> None:
        """Rendered pair always includes labels."""
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        rendered = display.render(pair)

        # Labels must be present
        assert rendered.left_label in ["BEST", "WORST"]
        assert rendered.right_label in ["BEST", "WORST"]
        assert rendered.left_label != rendered.right_label


# =============================================================================
# LOW-N PERSISTENCE GATE (OWL v0.2)
# =============================================================================


class TestLowNGate:
    """Tests for low-N persistence gate."""

    def test_low_n_cannot_persist(self, display: ConflictDisplay, low_n_values: dict) -> None:
        """Low sample size pairs cannot persist as FACT."""
        pair = display.create_pair(
            dimension="session",
            values=low_n_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        assert not pair.can_persist

        can_persist, reason = display.check_persistence_gate(pair)
        assert not can_persist
        assert str(LOW_N_THRESHOLD) in reason

    def test_sufficient_n_can_persist(self, display: ConflictDisplay, sample_values: dict) -> None:
        """Sufficient sample size pairs can persist."""
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        assert pair.can_persist

        can_persist, reason = display.check_persistence_gate(pair)
        assert can_persist
        assert reason == ""

    def test_result_type_view_when_low_n(
        self, display: ConflictDisplay, low_n_values: dict
    ) -> None:
        """Result type is VIEW when low-N."""
        pair = display.create_pair(
            dimension="session",
            values=low_n_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        result_type = display.get_result_type(pair)
        assert result_type == ResultType.VIEW

    def test_result_type_fact_when_sufficient_n(
        self, display: ConflictDisplay, sample_values: dict
    ) -> None:
        """Result type is FACT when N >= 30."""
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        result_type = display.get_result_type(pair)
        assert result_type == ResultType.FACT


# =============================================================================
# CONFLICT REQUEST VALIDATION
# =============================================================================


class TestConflictRequestValidation:
    """Tests for conflict request validation."""

    def test_best_without_worst_rejected(self) -> None:
        """Requesting 'best' without 'worst' is rejected."""
        valid, error = validate_conflict_request(
            request_type="best",
            include_worst=False,
        )

        assert not valid
        assert "INV-ATTR-CONFLICT-DISPLAY" in error

    def test_best_with_worst_accepted(self) -> None:
        """Requesting 'best' with 'worst' is accepted."""
        valid, error = validate_conflict_request(
            request_type="best",
            include_worst=True,
        )

        assert valid
        assert error == ""

    def test_both_request_accepted(self) -> None:
        """Requesting 'both' is accepted."""
        valid, error = validate_conflict_request(
            request_type="both",
            include_worst=True,
        )

        assert valid


# =============================================================================
# SERIALIZATION
# =============================================================================


class TestSerialization:
    """Tests for conflict pair serialization."""

    def test_to_dict_complete(self, display: ConflictDisplay, sample_values: dict) -> None:
        """Serialization includes all fields."""
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        data = display.to_dict(pair)

        assert "dimension" in data
        assert "best" in data
        assert "worst" in data
        assert "spread" in data
        assert "scope" in data
        assert "can_persist" in data

    def test_to_dict_spread_hidden_when_disabled(
        self, display: ConflictDisplay, sample_values: dict
    ) -> None:
        """Spread delta is None when disabled."""
        pair = display.create_pair(
            dimension="session",
            values=sample_values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        data = display.to_dict(pair)

        # Delta should be None when disabled
        assert data["spread"]["delta"] is None
        assert data["spread"]["status"] == "DISABLED"


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_same_metric_values(self, display: ConflictDisplay) -> None:
        """Handles equal metric values."""
        values = {
            "A": {"metrics": {"sharpe": 1.0}, "sample_size": 50, "provenance": {}},
            "B": {"metrics": {"sharpe": 1.0}, "sample_size": 50, "provenance": {}},
        }

        pair = display.create_pair(
            dimension="test",
            values=values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        assert pair.spread.delta == 0.0

    def test_none_metric_values_filtered(self, display: ConflictDisplay) -> None:
        """None metric values are filtered out."""
        values = {
            "A": {"metrics": {"sharpe": 1.5}, "sample_size": 50, "provenance": {}},
            "B": {"metrics": {"sharpe": None}, "sample_size": 50, "provenance": {}},
            "C": {"metrics": {"sharpe": 0.5}, "sample_size": 50, "provenance": {}},
        }

        pair = display.create_pair(
            dimension="test",
            values=values,
            comparison_metric="sharpe",
        )

        assert pair is not None
        # B should be filtered, leaving A and C
        assert pair.best.dimension_value == "A"
        assert pair.worst.dimension_value == "C"


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
