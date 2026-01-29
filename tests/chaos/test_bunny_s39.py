"""
BUNNY Chaos Tests — S39
=======================

THE CONSTITUTIONAL CEILING.
28+ chaos vectors testing scalar ban.
"""

from __future__ import annotations


class TestScalarResurrection:
    """Attacks that try to resurrect composite scores."""

    def test_combine_sharpe_win_rate_rejected(self):
        """Combining sharpe + win_rate into quality_score → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"quality_score": 0.85}  # Forbidden
        result = linter.lint(data)
        assert not result.valid

    def test_weighted_average_rejected(self):
        """Weighted average of metrics → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"composite_score": (1.5 * 0.4 + 0.55 * 0.6)}
        result = linter.lint(data)
        assert not result.valid

    def test_viability_index_rejected(self):
        """Viability index computation → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"viability_index": 0.78}
        result = linter.lint(data)
        assert not result.valid

    def test_strategy_health_rejected(self):
        """Strategy health: 78/100 → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"overall_rating": 78}
        result = linter.lint(data)
        assert not result.valid


class TestVerdictAttacks:
    """Attacks that try to inject verdicts."""

    def test_overfit_true_invalid(self):
        """Walk-forward returns OVERFIT: TRUE → INVALID."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"overfit_score": 0.9}
        result = linter.lint(data)
        assert not result.valid

    def test_risk_high_invalid(self):
        """Monte Carlo returns RISK: HIGH → INVALID."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"risk_level": "HIGH"}
        result = linter.lint(data)
        assert not result.valid

    def test_tradeable_no_invalid(self) -> None:
        """Cost curve returns TRADEABLE: NO → INVALID."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        # Check for "recommend" pattern
        data = {"recommendation": "DO NOT TRADE"}
        lint_result = linter.lint(data)
        assert not lint_result.valid

    def test_recommended_invalid(self):
        """Backtest returns RECOMMENDED → INVALID."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"recommendation": "APPROVED"}
        result = linter.lint(data)
        assert not result.valid


class TestRankingAttacks:
    """Attacks that try to inject rankings."""

    def test_sensitivity_importance_rejected(self):
        """Sensitivity sorted by importance → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"importance_rank": 1}
        result = linter.lint(data)
        assert not result.valid

    def test_most_sensitive_rejected(self):
        """Most sensitive parameter extraction → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        result = linter.lint_text("The most sensitive parameter is threshold")
        assert not result.valid

    def test_top_robust_rejected(self):
        """Top 3 robust configurations → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"robustness_rank": 1}
        result = linter.lint(data)
        assert not result.valid

    def test_best_setting_rejected(self):
        """Best parameter setting → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        result = linter.lint_text("The best performing configuration is...")
        assert not result.valid


class TestLabelAttacks:
    """Attacks that try to inject evaluative labels."""

    def test_dangerous_drawdown_rejected(self) -> None:
        """Drawdown labeled 'concerning' → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        # Check "concerning" which is in our list
        result = linter.lint_text("The drawdown level is concerning")
        assert not result.valid

    def test_concerning_delta_rejected(self):
        """Delta labeled 'concerning' → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        result = linter.lint_text("The delta is concerning")
        assert not result.valid

    def test_acceptable_spread_rejected(self):
        """Spread labeled 'acceptable' → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        result = linter.lint_text("The spread is acceptable")
        assert not result.valid


class TestCrossModuleLeakage:
    """Attacks through module chaining."""

    def test_hunt_survivors_backtest_rejected(self):
        """Hunt 'survivors' fed to backtest → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"survivor_rank": 1}
        result = linter.lint(data)
        assert not result.valid

    def test_cfp_best_condition_rejected(self):
        """CFP 'best condition' fed to walk-forward → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"quality_score": 0.9}  # Re-synthesized from CFP
        result = linter.lint(data)
        assert not result.valid

    def test_derived_edge_score_rejected(self):
        """Derived 'edge score' anywhere → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"edge_score": 0.5}
        result = linter.lint(data)
        assert not result.valid


class TestIndexFieldRejection:
    """All *_index fields rejected."""

    def test_stability_index_rejected(self):
        """Stability index → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"stability_index": 0.8}
        result = linter.lint(data)
        assert not result.valid

    def test_confidence_index_rejected(self):
        """Confidence index → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"confidence_index": 0.9}
        result = linter.lint(data)
        assert not result.valid


class TestRatingFieldRejection:
    """All *_rating fields rejected."""

    def test_performance_rating_rejected(self):
        """Performance rating → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"performance_rating": "A+"}
        result = linter.lint(data)
        assert not result.valid

    def test_strategy_rating_rejected(self):
        """Strategy rating → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"strategy_rating": 4.5}
        result = linter.lint(data)
        assert not result.valid


class TestAvgFieldRejection:
    """All avg_* fields rejected (INV-NO-AGGREGATE-SCALAR)."""

    def test_avg_sharpe_rejected(self):
        """avg_sharpe → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"avg_sharpe": 1.5}
        result = linter.lint(data)
        assert not result.valid

    def test_avg_win_rate_rejected(self):
        """avg_win_rate → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"avg_win_rate": 0.55}
        result = linter.lint(data)
        assert not result.valid

    def test_avg_delta_rejected(self):
        """avg_delta → REJECTED."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {"avg_delta": 0.3}
        result = linter.lint(data)
        assert not result.valid


class TestCleanDataPasses:
    """Verify clean data passes."""

    def test_decomposed_metrics_pass(self):
        """Decomposed metrics pass."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {
            "sharpe": 1.5,
            "win_rate": 0.55,
            "profit_factor": 1.8,
            "max_drawdown": 0.12,
            "color_scale": None,
        }
        result = linter.lint(data)
        assert result.valid

    def test_full_arrays_pass(self):
        """Full arrays (not averages) pass."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {
            "train_sharpes": [1.2, 1.5, 1.3, 1.4, 1.6],
            "test_sharpes": [1.0, 1.3, 1.1, 1.2, 1.4],
            "deltas": [-0.2, -0.2, -0.2, -0.2, -0.2],
        }
        result = linter.lint(data)
        assert result.valid

    def test_percentiles_pass(self):
        """Percentiles pass."""
        from validation.scalar_ban_linter import ScalarBanLinter

        linter = ScalarBanLinter()
        data = {
            "p5_drawdown": -0.05,
            "p50_drawdown": -0.10,
            "p95_drawdown": -0.20,
        }
        result = linter.lint(data)
        assert result.valid
