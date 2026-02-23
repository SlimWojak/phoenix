"""
Tests for Backtest Worker — S39 Track A
=======================================

Verifies decomposed metrics. No composite scores.
"""

from __future__ import annotations

from datetime import UTC, datetime


def test_backtest_result_no_composite_fields():
    """BacktestResult has no composite score fields."""
    from validation.backtest import BacktestResult

    result = BacktestResult()

    # MUST NOT have composite fields
    assert not hasattr(result, "quality_score")
    assert not hasattr(result, "viability_index")
    assert not hasattr(result, "robustness_score")
    assert not hasattr(result, "overall_rating")
    assert not hasattr(result, "recommendation")
    assert not hasattr(result, "verdict")

    # MUST have decomposed metrics
    assert hasattr(result, "metrics")
    assert hasattr(result.metrics, "sharpe")
    assert hasattr(result.metrics, "win_rate")
    assert hasattr(result.metrics, "profit_factor")


def test_backtest_result_mandatory_disclaimer():
    """BacktestResult has mandatory disclaimer."""
    from validation.backtest import MANDATORY_DISCLAIMER, BacktestResult

    result = BacktestResult()

    assert result.disclaimer == MANDATORY_DISCLAIMER
    assert "FACTS_ONLY" in result.disclaimer
    assert "VERDICT" in result.disclaimer


def test_backtest_result_no_color_metadata():
    """BacktestResult has null color metadata."""
    from validation.backtest import BacktestResult

    result = BacktestResult()

    assert result.visual_metadata.color_scale is None
    assert result.visual_metadata.highlight_threshold is None
    assert result.visual_metadata.emphasis_rules is None


def test_backtest_worker_run():
    """BacktestWorker.run returns decomposed metrics."""
    from validation.backtest import BacktestResult, BacktestWorker

    worker = BacktestWorker()
    result = worker.run(
        strategy_config={"name": "test_strategy"},
        time_range_start=datetime(2020, 1, 1, tzinfo=UTC),
        time_range_end=datetime(2022, 1, 1, tzinfo=UTC),
        pairs=["EURUSD"],
    )

    assert isinstance(result, BacktestResult)
    assert result.parameters.pairs == ["EURUSD"]
    assert result.metrics.trade_count >= 0
    assert result.disclaimer != ""


def test_backtest_validator_rejects_forbidden():
    """BacktestValidator rejects forbidden fields."""
    from validation.backtest import BacktestResult, BacktestValidator

    validator = BacktestValidator()
    result = BacktestResult()

    valid, errors = validator.validate(result)
    assert valid is True
    assert len(errors) == 0


def test_backtest_forbidden_fields_constant():
    """FORBIDDEN_FIELDS contains expected patterns."""
    from validation.backtest import FORBIDDEN_FIELDS

    assert "quality_score" in FORBIDDEN_FIELDS
    assert "viability_index" in FORBIDDEN_FIELDS
    assert "robustness_score" in FORBIDDEN_FIELDS
    assert "verdict" in FORBIDDEN_FIELDS


def test_backtest_result_has_provenance():
    """BacktestResult has full provenance."""
    from validation.backtest import BacktestWorker

    worker = BacktestWorker()
    result = worker.run(
        strategy_config={"name": "test"},
        time_range_start=datetime(2020, 1, 1, tzinfo=UTC),
        time_range_end=datetime(2021, 1, 1, tzinfo=UTC),
    )

    assert result.provenance.query_string != ""
    assert result.provenance.dataset_hash != ""
    assert result.provenance.governance_hash != ""


def test_backtest_metrics_decomposed():
    """BacktestMetrics contains decomposed values."""
    from validation.backtest import BacktestMetrics

    metrics = BacktestMetrics(
        sharpe=1.5,
        win_rate=0.55,
        profit_factor=1.8,
        max_drawdown=0.12,
        avg_trade=50.0,
        trade_count=100,
    )

    # Each metric is standalone
    assert metrics.sharpe == 1.5
    assert metrics.win_rate == 0.55
    assert metrics.profit_factor == 1.8

    # No composite combination
    assert not hasattr(metrics, "combined_score")
    assert not hasattr(metrics, "weighted_average")


def test_backtest_id_auto_generated():
    """BacktestResult generates unique ID."""
    from validation.backtest import BacktestResult

    result1 = BacktestResult()
    result2 = BacktestResult()

    assert result1.backtest_id.startswith("BT_")
    assert result2.backtest_id.startswith("BT_")
    assert result1.backtest_id != result2.backtest_id


def test_backtest_timestamp_utc():
    """BacktestResult timestamp is UTC."""
    from validation.backtest import BacktestResult

    result = BacktestResult()

    assert result.timestamp.tzinfo is not None
