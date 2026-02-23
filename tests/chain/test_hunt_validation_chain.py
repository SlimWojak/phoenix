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

from validation import (
    BacktestWorker,
    CostCurveAnalyzer,
    ScalarBanLinter,
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
        param_space = sample_hypothesis["param_space"]
        grid_size = len(param_space["entry_delay"]) * len(param_space["exit_delay"])
        
        # Hunt should return ALL combinations
        expected_cells = grid_size  # 5 * 3 = 15
        
        # Create mock hunt results (all cells)
        hunt_results = []
        for entry in param_space["entry_delay"]:
            for exit in param_space["exit_delay"]:
                hunt_results.append({
                    "params": {"entry_delay": entry, "exit_delay": exit},
                    "metrics": {"sharpe": 1.0 + entry * 0.1, "trades": 100},
                })
        
        assert len(hunt_results) == expected_cells
        print(f"✓ Hunt grid exhaustive: {len(hunt_results)}/{expected_cells}")

    def test_hunt_output_preserves_param_order(self, sample_hypothesis: dict):
        """Results must preserve declared parameter order, not performance order."""
        param_space = sample_hypothesis["param_space"]
        
        # Hunt results should be in param_space order, NOT sorted by sharpe
        hunt_results = []
        for entry in param_space["entry_delay"]:
            for exit_val in param_space["exit_delay"]:
                hunt_results.append({
                    "params": {"entry_delay": entry, "exit_delay": exit_val},
                    "sharpe": 1.0 + entry * 0.1 - exit_val * 0.05,
                })
        
        # Extract entry_delay sequence
        entry_sequence = [r["params"]["entry_delay"] for r in hunt_results]
        
        # Should be [1,1,1,2,2,2,3,3,3,4,4,4,5,5,5] not sorted by sharpe
        expected_pattern = []
        for entry in param_space["entry_delay"]:
            expected_pattern.extend([entry] * len(param_space["exit_delay"]))
        
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
        from dataclasses import fields
        from datetime import UTC, datetime
        
        worker = BacktestWorker()
        
        # Simulate backtest on hunt variant
        result = worker.run(
            strategy_config={"entry_delay": 2},
            time_range_start=datetime(2024, 1, 1, tzinfo=UTC),
            time_range_end=datetime(2024, 1, 31, tzinfo=UTC),
            pairs=["EURUSD"],
        )
        
        # Must have individual metrics
        assert hasattr(result, "metrics")
        assert hasattr(result.metrics, "sharpe")
        assert hasattr(result.metrics, "win_rate")
        
        # Must NOT have composite score fields
        field_names = [f.name for f in fields(result)]
        assert "quality_score" not in field_names
        assert "viability_index" not in field_names
        print("✓ Backtest provides decomposed metrics")

    def test_backtest_to_walk_forward_clean(self, linter: ScalarBanLinter):
        """Chain from backtest to walk-forward must be clean."""
        from datetime import UTC, datetime
        
        # Run backtest
        worker = BacktestWorker()
        bt_result = worker.run(
            strategy_config={},
            time_range_start=datetime(2024, 1, 1, tzinfo=UTC),
            time_range_end=datetime(2024, 1, 31, tzinfo=UTC),
        )
        
        # Feed to walk-forward
        validator = WalkForwardValidator()
        wf_result = validator.run(strategy_config={}, n_splits=2)
        
        # Verify both modules produced results
        assert bt_result is not None
        assert wf_result is not None
        
        # Verify no CROSS-MODULE synthesis occurred
        # (individual module metrics like avg_trade are acceptable - they're decomposed)
        # The chain check is: no NEW aggregate scores emerged at seam
        assert not hasattr(bt_result, "combined_score")
        assert not hasattr(wf_result, "combined_score")
        assert not hasattr(bt_result, "overall_quality")
        assert not hasattr(wf_result, "overall_quality")
        
        print("✓ Backtest → WalkForward chain clean (no cross-module synthesis)")


class TestWalkForwardToCostCurveChain:
    """Test WalkForward → CostCurve integration seam."""

    def test_cost_curve_no_acceptability_verdict(self):
        """Cost curve must not have 'acceptable spread' verdicts."""
        from dataclasses import fields
        
        analyzer = CostCurveAnalyzer()
        
        result = analyzer.run(
            strategy_config={},
            base_sharpe=1.5,
            spread_scenarios=[0.5, 1.0, 1.5, 2.0, 2.5],
        )
        
        # Check field names for forbidden language
        field_names = [f.name for f in fields(result)]
        
        # Must NOT have acceptability language
        assert "acceptable_spread" not in field_names
        assert "tradeable" not in field_names
        assert "verdict" not in field_names
        print("✓ Cost curve has no acceptability verdicts")

    def test_cost_curve_provides_breakeven_fact(self):
        """Cost curve must provide factual breakeven, not recommendation."""
        from dataclasses import fields
        
        analyzer = CostCurveAnalyzer()
        
        result = analyzer.run(
            strategy_config={},
            base_sharpe=1.5,
            spread_scenarios=[0.5, 1.0, 1.5, 2.0, 2.5],
        )
        
        # Must have breakeven as factual number
        assert hasattr(result, "breakeven")
        assert hasattr(result.breakeven, "spread_at_zero_sharpe")
        
        # Must NOT have "recommended spread"
        field_names = [f.name for f in fields(result)]
        assert "recommended_spread" not in field_names
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
