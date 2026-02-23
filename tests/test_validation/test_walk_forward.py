"""
Tests for Walk-Forward Validation — S39 Track B
================================================

Verifies full arrays, no avg_* fields.
INV-NO-AGGREGATE-SCALAR critical.
"""

from __future__ import annotations


def test_walk_forward_no_avg_fields():
    """WalkForwardResult has NO avg_* fields."""
    from validation.walk_forward import WalkForwardResult

    result = WalkForwardResult()

    # CRITICAL: INV-NO-AGGREGATE-SCALAR
    assert not hasattr(result, "avg_train_sharpe")
    assert not hasattr(result, "avg_test_sharpe")
    assert not hasattr(result, "avg_delta_sharpe")
    assert not hasattr(result, "avg_win_rate")


def test_walk_forward_has_full_arrays():
    """WalkForwardResult contains full arrays."""
    from validation.walk_forward import WalkForwardValidator

    validator = WalkForwardValidator()
    result = validator.run(
        strategy_config={"name": "test"},
        n_splits=5,
    )

    # MUST have full arrays
    assert len(result.split_distribution.train_sharpes) == 5
    assert len(result.split_distribution.test_sharpes) == 5
    assert len(result.split_distribution.deltas) == 5


def test_walk_forward_deltas_computed():
    """Deltas are test - train (factual, not judgment)."""
    from validation.walk_forward import WalkForwardValidator

    validator = WalkForwardValidator()
    result = validator.run(
        strategy_config={"name": "test"},
        n_splits=3,
    )

    # Each delta should be present
    for split in result.per_split_results:
        assert hasattr(split, "delta_sharpe")
        # delta = test - train
        expected = round(split.test_metrics.sharpe - split.train_metrics.sharpe, 2)
        assert split.delta_sharpe == expected


def test_walk_forward_descriptive_summary_not_verdict():
    """Descriptive summary is NOT a verdict."""
    from validation.walk_forward import WalkForwardResult

    result = WalkForwardResult()

    # Has descriptive summary
    assert hasattr(result, "descriptive_summary")

    # Not a verdict
    assert not hasattr(result, "verdict")
    assert not hasattr(result, "overfit_score")
    assert not hasattr(result, "stability_rating")


def test_walk_forward_mandatory_disclaimer():
    """WalkForwardResult has mandatory disclaimer."""
    from validation.walk_forward import WalkForwardResult

    result = WalkForwardResult()

    assert "FACTS_ONLY" in result.disclaimer


def test_validate_no_avg_fields_passes_clean():
    """validate_no_avg_fields passes clean result."""
    from validation.walk_forward import WalkForwardResult, validate_no_avg_fields

    result = WalkForwardResult()
    valid, errors = validate_no_avg_fields(result)

    assert valid is True
    assert len(errors) == 0


def test_walk_forward_per_split_results():
    """Per-split results are individual, not averaged."""
    from validation.walk_forward import WalkForwardValidator

    validator = WalkForwardValidator()
    result = validator.run(
        strategy_config={"name": "test"},
        n_splits=4,
    )

    assert len(result.per_split_results) == 4
    for i, split in enumerate(result.per_split_results):
        assert split.split_id == i
        assert hasattr(split, "train_metrics")
        assert hasattr(split, "test_metrics")


def test_walk_forward_forbidden_fields_constant():
    """FORBIDDEN_FIELDS contains avg_* pattern."""
    from validation.walk_forward import FORBIDDEN_FIELDS

    # CRITICAL check
    assert "avg_train_sharpe" in FORBIDDEN_FIELDS
    assert "avg_test_sharpe" in FORBIDDEN_FIELDS
    assert "avg_delta_sharpe" in FORBIDDEN_FIELDS
    assert "avg_" in FORBIDDEN_FIELDS


def test_walk_forward_variance_visible():
    """Full arrays make variance visible to human."""
    from validation.walk_forward import WalkForwardValidator

    validator = WalkForwardValidator()
    result = validator.run(
        strategy_config={"name": "test"},
        n_splits=5,
    )

    # Human can see the spread
    deltas = result.split_distribution.deltas
    assert isinstance(deltas, list)
    assert len(deltas) == 5

    # No hidden average
    # [-1, -1, -1, 4, -1] → avg=0 hides fragility
    # With full arrays, human sees all values


def test_walk_forward_id_auto_generated():
    """WalkForwardResult generates unique ID."""
    from validation.walk_forward import WalkForwardResult

    result1 = WalkForwardResult()
    result2 = WalkForwardResult()

    assert result1.wf_id.startswith("WF_")
    assert result1.wf_id != result2.wf_id


def test_walk_forward_descriptive_stats_count():
    """Descriptive summary counts positive/negative splits."""
    from validation.walk_forward import WalkForwardValidator

    validator = WalkForwardValidator()
    result = validator.run(
        strategy_config={"name": "test"},
        n_splits=5,
    )

    # Should have counts
    summary = result.descriptive_summary
    total = summary.n_positive_splits + summary.n_negative_splits
    assert total <= 5  # Could have zeros
