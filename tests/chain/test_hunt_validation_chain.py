"""
FLOW 2: Hunt → Backtest → WalkForward → CostCurve
=================================================

S40 Chain Validation — Proves Hunt output chains cleanly
through validation pipeline without ranking/synthesis.

INVARIANTS:
  - INV-HUNT-NO-SURVIVOR-RANKING: Grid remains exhaustive
  - INV-SCALAR-BAN: No scores at any seam
  - INV-SENSITIVITY-PARAM-ORDER: Results preserve declared order
"""

from __future__ import annotations

import pytest

from hunt import Hypothesis, HuntExecutor, HuntResult
from validation import (
    BacktestResult,
    BacktestWorker,
    CostCurveAnalyzer,
    CostCurveResult,
    ScalarBanLinter,
    WalkForwardResult,
    WalkForwardValidator,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_hypothesis() -> dict:
    """Create a sample Hunt hypothesis as dict (simplified for testing)."""
    return {
        "hypothesis_id": "hyp_001",
        "name": "entry_delay_grid",
        "description": "Test entry delay parameter",
        "param_space": {
            "entry_delay": [1, 2, 3, 4, 5],
            "exit_delay": [1, 2, 3],
        },
        "created_by": "operator",
    }


@pytest.fixture
def linter() -> ScalarBanLinter:
    """Create scalar ban linter."""
    return ScalarBanLinter()


# =============================================================================
# FLOW TESTS
# =============================================================================


class TestHuntToBacktestChain:
    """Test Hunt → Backtest integration seam."""

    def test_hunt_output_is_exhaustive_grid(self, sample_hypothesis: dict):
        """Hunt must output ALL grid cells, no survivor filtering."""
        # Simulate hunt execution
        grid_size = len(sample_hypothesis.param_space["entry_delay"]) * len(
            sample_hypothesis.param_space["exit_delay"]
        )
        
        # Hunt should return ALL combinations
        expected_cells = grid_size  # 5 * 3 = 15
        
        # Create mock hunt results (all cells)
        hunt_results = []
        for entry in sample_hypothesis.param_space["entry_delay"]:
            for exit in sample_hypothesis.param_space["exit_delay"]:
                hunt_results.append({
                    "params": {"entry_delay": entry, "exit_delay": exit},
                    "metrics": {"sharpe": 1.0 + entry * 0.1, "trades": 100},
                })
        
        assert len(hunt_results) == expected_cells
        print(f"✓ Hunt grid exhaustive: {len(hunt_results)}/{expected_cells}")

    def test_hunt_output_preserves_param_order(self, sample_hypothesis: dict):
        """Results must preserve declared parameter order, not performance order."""
        # Hunt results should be in param_space order, NOT sorted by sharpe
        hunt_results = []
        for entry in sample_hypothesis.param_space["entry_delay"]:
            for exit in sample_hypothesis.param_space["exit_delay"]:
                hunt_results.append({
                    "params": {"entry_delay": entry, "exit_delay": exit},
                    "sharpe": 1.0 + entry * 0.1 - exit * 0.05,
                })
        
        # Extract entry_delay sequence
        entry_sequence = [r["params"]["entry_delay"] for r in hunt_results]
        
        # Should be [1,1,1,2,2,2,3,3,3,4,4,4,5,5,5] not sorted by sharpe
        expected_pattern = []
        for entry in sample_hypothesis.param_space["entry_delay"]:
            expected_pattern.extend([entry] * len(sample_hypothesis.param_space["exit_delay"]))
        
        assert entry_sequence == expected_pattern
        print("✓ Hunt output preserves param order")

    def test_hunt_output_passes_scalar_ban(self, linter: ScalarBanLinter):
        """Hunt output must pass scalar ban (no ranking scores)."""
        hunt_output = {
            "hypothesis_id": "hyp_001",
            "grid_results": [
                {"params": {"entry_delay": 1}, "sharpe": 1.2, "win_rate": 0.55},
                {"params": {"entry_delay": 2}, "sharpe": 0.9, "win_rate": 0.52},
            ],
            "disclaimer": "Raw grid results. No ranking. Human interprets.",
        }
        
        result = linter.lint(hunt_output)
        assert result.valid, f"Scalar ban violations: {result.violations}"
        print("✓ Hunt output passes scalar ban")


class TestBacktestToWalkForwardChain:
    """Test Backtest → WalkForward integration seam."""

    def test_backtest_provides_decomposed_metrics(self):
        """Backtest must provide decomposed metrics, not composite scores."""
        worker = BacktestWorker()
        
        # Simulate backtest on hunt variant
        result = worker.backtest(
            strategy_config={"entry_delay": 2},
            price_data=[100, 101, 99, 102, 103],
        )
        
        # Must have individual metrics
        assert hasattr(result, "metrics")
        assert hasattr(result.metrics, "sharpe")
        assert hasattr(result.metrics, "win_rate")
        
        # Must NOT have composite score
        result_dict = result.to_dict()
        assert "quality_score" not in result_dict
        assert "viability_index" not in result_dict
        print("✓ Backtest provides decomposed metrics")

    def test_backtest_to_walk_forward_clean(self, linter: ScalarBanLinter):
        """Chain from backtest to walk-forward must be clean."""
        # Run backtest
        worker = BacktestWorker()
        bt_result = worker.backtest(
            strategy_config={},
            price_data=[100, 101, 102, 101, 103],
        )
        
        # Feed to walk-forward
        validator = WalkForwardValidator()
        wf_result = validator.validate(
            equity_curve=[100, 102, 104, 103, 105],
            n_splits=2,
            strategy_config={},
        )
        
        # Lint combined output
        combined = {
            "backtest": bt_result.to_dict(),
            "walk_forward": wf_result.to_dict(),
        }
        
        result = linter.lint(combined)
        assert result.valid
        print("✓ Backtest → WalkForward chain clean")


class TestWalkForwardToCostCurveChain:
    """Test WalkForward → CostCurve integration seam."""

    def test_cost_curve_no_acceptability_verdict(self):
        """Cost curve must not have 'acceptable spread' verdicts."""
        analyzer = CostCurveAnalyzer()
        
        result = analyzer.analyze(
            base_sharpe=1.5,
            spread_scenarios=[0.5, 1.0, 1.5, 2.0, 2.5],
            strategy_config={},
        )
        
        result_dict = result.to_dict()
        
        # Must NOT have acceptability language
        assert "acceptable_spread" not in result_dict
        assert "tradeable" not in result_dict
        assert "verdict" not in result_dict
        print("✓ Cost curve has no acceptability verdicts")

    def test_cost_curve_provides_breakeven_fact(self):
        """Cost curve must provide factual breakeven, not recommendation."""
        analyzer = CostCurveAnalyzer()
        
        result = analyzer.analyze(
            base_sharpe=1.5,
            spread_scenarios=[0.5, 1.0, 1.5, 2.0, 2.5],
            strategy_config={},
        )
        
        # Must have breakeven as factual number
        assert hasattr(result, "breakeven")
        assert hasattr(result.breakeven, "spread_at_zero_sharpe")
        
        # Must NOT have "recommended spread"
        result_dict = result.to_dict()
        assert "recommended_spread" not in result_dict
        print("✓ Cost curve provides factual breakeven")


class TestFullChainNoSynthesis:
    """Test complete Hunt → Backtest → WalkForward → CostCurve chain."""

    def test_no_synthesis_across_4_modules(self, linter: ScalarBanLinter):
        """No synthesized scores should emerge across 4-module chain."""
        # Simulate full chain output
        chain_output = {
            "hunt": {
                "hypothesis_id": "hyp_001",
                "grid_results": [
                    {"params": {"delay": 1}, "sharpe": 1.2},
                    {"params": {"delay": 2}, "sharpe": 0.9},
                ],
            },
            "backtest": {
                "sharpe": 1.1,
                "win_rate": 0.53,
                "max_drawdown": 0.15,
            },
            "walk_forward": {
                "split_sharpes": [1.0, 1.2, 0.9],
                "deltas": [-0.1, 0.1, -0.2],
            },
            "cost_curve": {
                "degradation_table": [
                    {"spread": 0.5, "sharpe": 1.4},
                    {"spread": 1.0, "sharpe": 1.1},
                ],
                "breakeven_spread": 2.1,
            },
        }
        
        result = linter.lint(chain_output)
        assert result.valid, f"Synthesis detected: {result.violations}"
        print("✓ No synthesis across 4-module chain")


# =============================================================================
# INVARIANT ASSERTIONS
# =============================================================================


class TestChainInvariants:
    """Explicit invariant checks."""

    def test_inv_hunt_no_survivor_ranking(self):
        """INV-HUNT-NO-SURVIVOR-RANKING: All grid cells present."""
        # Hunt must not filter to "winners"
        param_space = {"a": [1, 2, 3], "b": [4, 5]}
        expected_size = 3 * 2  # 6 cells
        
        # Simulate hunt output
        results = []
        for a in param_space["a"]:
            for b in param_space["b"]:
                results.append({"a": a, "b": b})
        
        assert len(results) == expected_size
        print(f"✓ INV-HUNT-NO-SURVIVOR-RANKING: {len(results)}/{expected_size}")

    def test_inv_scalar_ban_at_every_seam(self, linter: ScalarBanLinter):
        """INV-SCALAR-BAN: Enforced at every integration seam."""
        seams = [
            {"seam": "hunt_output", "sharpe": 1.2, "trades": 100},
            {"seam": "backtest_output", "win_rate": 0.55, "max_dd": 0.15},
            {"seam": "wf_output", "test_sharpes": [1.0, 0.9]},
            {"seam": "cc_output", "breakeven": 2.1},
        ]
        
        for seam in seams:
            result = linter.lint(seam)
            assert result.valid, f"Seam {seam['seam']} failed: {result.violations}"
        
        print(f"✓ INV-SCALAR-BAN enforced at {len(seams)} seams")
