"""
Cross-Module Audit — S39 Integration
====================================

Tests that validation outputs pass through linter cleanly.
INV-CROSS-MODULE-NO-SYNTH: Chain outputs decomposed only.
"""

from __future__ import annotations

from datetime import UTC, datetime


def test_backtest_result_passes_linter():
    """BacktestResult passes ScalarBanLinter."""
    from validation.backtest import BacktestWorker
    from validation.scalar_ban_linter import ScalarBanLinter

    worker = BacktestWorker()
    result = worker.run(
        strategy_config={"name": "test"},
        time_range_start=datetime(2020, 1, 1, tzinfo=UTC),
        time_range_end=datetime(2022, 1, 1, tzinfo=UTC),
    )

    # Convert to dict and lint
    linter = ScalarBanLinter()
    data = {
        "backtest_id": result.backtest_id,
        "disclaimer": result.disclaimer,
        "sharpe": result.metrics.sharpe,
        "win_rate": result.metrics.win_rate,
        "profit_factor": result.metrics.profit_factor,
        "max_drawdown": result.metrics.max_drawdown,
        "color_scale": result.visual_metadata.color_scale,
    }

    lint_result = linter.lint(data)
    assert lint_result.valid, f"Violations: {lint_result.error_messages}"


def test_walk_forward_result_passes_linter():
    """WalkForwardResult passes ScalarBanLinter."""
    from validation.scalar_ban_linter import ScalarBanLinter
    from validation.walk_forward import WalkForwardValidator

    validator = WalkForwardValidator()
    result = validator.run(
        strategy_config={"name": "test"},
        n_splits=5,
    )

    linter = ScalarBanLinter()
    data = {
        "wf_id": result.wf_id,
        "disclaimer": result.disclaimer,
        "train_sharpes": result.split_distribution.train_sharpes,
        "test_sharpes": result.split_distribution.test_sharpes,
        "deltas": result.split_distribution.deltas,
        "n_positive_splits": result.descriptive_summary.n_positive_splits,
        "n_negative_splits": result.descriptive_summary.n_negative_splits,
    }

    lint_result = linter.lint(data)
    assert lint_result.valid, f"Violations: {lint_result.error_messages}"


def test_monte_carlo_result_passes_linter():
    """MonteCarloResult passes ScalarBanLinter."""
    from validation.monte_carlo import MonteCarloSimulator
    from validation.scalar_ban_linter import ScalarBanLinter

    simulator = MonteCarloSimulator()
    result = simulator.run(
        strategy_config={"name": "test"},
        n_simulations=100,
    )

    linter = ScalarBanLinter()
    data = {
        "mc_id": result.mc_id,
        "disclaimer": result.disclaimer,
        "p5_drawdown": result.distribution.drawdown_percentiles.p5,
        "p50_drawdown": result.distribution.drawdown_percentiles.p50,
        "p95_drawdown": result.distribution.drawdown_percentiles.p95,
        "color_scale": result.visual_metadata.color_scale,
    }

    lint_result = linter.lint(data)
    assert lint_result.valid, f"Violations: {lint_result.error_messages}"


def test_sensitivity_result_passes_linter():
    """SensitivityResult passes ScalarBanLinter."""
    from validation.scalar_ban_linter import ScalarBanLinter
    from validation.sensitivity import SensitivityAnalyzer

    analyzer = SensitivityAnalyzer()
    result = analyzer.run(
        base_params={"threshold": 0.5},
        varied_param="threshold",
        variation_range=[0.3, 0.5, 0.7],
    )

    linter = ScalarBanLinter()
    data = {
        "sens_id": result.sens_id,
        "disclaimer": result.disclaimer,
        "rows": [
            {
                "param_value": row.param_value,
                "sharpe": row.sharpe,
                "win_rate": row.win_rate,
            }
            for row in result.table.rows
        ],
        "color_scale": result.visual_metadata.color_scale,
    }

    lint_result = linter.lint(data)
    assert lint_result.valid, f"Violations: {lint_result.error_messages}"


def test_cost_curve_result_passes_linter():
    """CostCurveResult passes ScalarBanLinter."""
    from validation.cost_curve import CostCurveAnalyzer
    from validation.scalar_ban_linter import ScalarBanLinter

    analyzer = CostCurveAnalyzer()
    result = analyzer.run(
        strategy_config={"name": "test"},
        spread_scenarios=[0.0, 1.0, 2.0],
    )

    linter = ScalarBanLinter()
    data = {
        "cc_id": result.cc_id,
        "disclaimer": result.disclaimer,
        "spread_at_zero_sharpe": result.breakeven.spread_at_zero_sharpe,
        "rows": [
            {
                "spread_pips": row.spread_pips,
                "sharpe": row.sharpe,
            }
            for row in result.table.rows
        ],
        "color_scale": result.visual_metadata.color_scale,
    }

    lint_result = linter.lint(data)
    assert lint_result.valid, f"Violations: {lint_result.error_messages}"


def test_chained_validation_decomposed():
    """Chained validation outputs remain decomposed."""
    from validation.backtest import BacktestWorker
    from validation.monte_carlo import MonteCarloSimulator
    from validation.scalar_ban_linter import ScalarBanLinter
    from validation.walk_forward import WalkForwardValidator

    # Chain: Backtest → Walk-Forward → Monte Carlo
    bt_worker = BacktestWorker()
    wf_validator = WalkForwardValidator()
    mc_simulator = MonteCarloSimulator()

    bt_result = bt_worker.run(
        strategy_config={"name": "test"},
        time_range_start=datetime(2020, 1, 1, tzinfo=UTC),
        time_range_end=datetime(2022, 1, 1, tzinfo=UTC),
    )

    wf_result = wf_validator.run(
        strategy_config={"name": "test"},
        n_splits=5,
    )

    mc_result = mc_simulator.run(
        strategy_config={"name": "test"},
        n_simulations=100,
    )

    # Combined output for chain (still decomposed)
    chain_output = {
        "backtest": {
            "sharpe": bt_result.metrics.sharpe,
            "win_rate": bt_result.metrics.win_rate,
        },
        "walk_forward": {
            "deltas": wf_result.split_distribution.deltas,
            "n_splits": wf_result.configuration.n_splits,
        },
        "monte_carlo": {
            "p50_drawdown": mc_result.distribution.drawdown_percentiles.p50,
            "p95_drawdown": mc_result.distribution.drawdown_percentiles.p95,
        },
        # NO: combined_score, viability_index, overall_rating
    }

    # Lint the chain output
    linter = ScalarBanLinter()
    lint_result = linter.lint(chain_output)
    assert lint_result.valid, f"Violations: {lint_result.error_messages}"


def test_no_synthesis_across_modules():
    """No synthesis across validation modules."""
    from validation.scalar_ban_linter import ScalarBanLinter

    linter = ScalarBanLinter()

    # BAD: Synthesized across modules
    bad_output = {
        "viability_index": 0.85,  # FORBIDDEN - matches viability*
        "overall_score": 0.9,  # FORBIDDEN - matches overall*
        "modules": ["backtest", "walk_forward", "monte_carlo"],
    }

    lint_result = linter.lint(bad_output)
    assert not lint_result.valid  # Should fail due to viability_index and overall_score


def test_all_modules_have_disclaimer():
    """All validation modules have mandatory disclaimer."""
    from validation.backtest import BacktestResult
    from validation.cost_curve import CostCurveResult
    from validation.monte_carlo import MonteCarloResult
    from validation.sensitivity import SensitivityResult
    from validation.walk_forward import WalkForwardResult

    results = [
        BacktestResult(),
        WalkForwardResult(),
        MonteCarloResult(),
        SensitivityResult(),
        CostCurveResult(),
    ]

    for result in results:
        assert "FACTS_ONLY" in result.disclaimer


def test_all_modules_have_null_color():
    """All validation modules have null color metadata."""
    from validation.backtest import BacktestResult
    from validation.cost_curve import CostCurveResult
    from validation.monte_carlo import MonteCarloResult
    from validation.sensitivity import SensitivityResult
    from validation.walk_forward import WalkForwardResult

    results = [
        BacktestResult(),
        WalkForwardResult(),
        MonteCarloResult(),
        SensitivityResult(),
        CostCurveResult(),
    ]

    for result in results:
        assert result.visual_metadata.color_scale is None


def test_validation_pipeline_clean():
    """Full validation pipeline produces linter-clean output."""
    from datetime import UTC, datetime

    from validation.backtest import BacktestWorker
    from validation.cost_curve import CostCurveAnalyzer
    from validation.monte_carlo import MonteCarloSimulator
    from validation.scalar_ban_linter import ScalarBanLinter
    from validation.sensitivity import SensitivityAnalyzer
    from validation.walk_forward import WalkForwardValidator

    # Run all validators
    bt = BacktestWorker().run(
        strategy_config={"name": "test"},
        time_range_start=datetime(2020, 1, 1, tzinfo=UTC),
        time_range_end=datetime(2022, 1, 1, tzinfo=UTC),
    )
    wf = WalkForwardValidator().run({"name": "test"}, n_splits=5)
    mc = MonteCarloSimulator().run({"name": "test"}, n_simulations=100)
    sens = SensitivityAnalyzer().run({"threshold": 0.5}, "threshold", [0.3, 0.5, 0.7])
    cc = CostCurveAnalyzer().run({"name": "test"}, [0.0, 1.0, 2.0])

    # Aggregate (decomposed only)
    pipeline_output = {
        "disclaimer": "FACTS_ONLY — NO INTERPRETATION OR VERDICT",
        "backtest_sharpe": bt.metrics.sharpe,
        "wf_deltas": wf.split_distribution.deltas,
        "mc_p95_drawdown": mc.distribution.drawdown_percentiles.p95,
        "sens_row_count": len(sens.table.rows),
        "cc_breakeven": cc.breakeven.spread_at_zero_sharpe,
        "color_scale": None,
    }

    linter = ScalarBanLinter()
    result = linter.lint(pipeline_output)
    assert result.valid, f"Violations: {result.error_messages}"
