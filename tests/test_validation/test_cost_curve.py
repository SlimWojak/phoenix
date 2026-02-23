"""
Tests for Cost Curve Analysis — S39 Track E
===========================================

Verifies factual degradation table, no acceptability verdict.
"""

from __future__ import annotations


def test_cost_curve_no_acceptability_verdict():
    """CostCurveResult has no acceptability verdict."""
    from validation.cost_curve import CostCurveResult

    result = CostCurveResult()

    # MUST NOT have acceptability
    assert not hasattr(result, "acceptable_spread")
    assert not hasattr(result, "cost_tolerance")
    assert not hasattr(result, "tradeable")
    assert not hasattr(result, "recommendation")


def test_cost_curve_has_degradation_table():
    """CostCurveResult has degradation table."""
    from validation.cost_curve import CostCurveAnalyzer

    analyzer = CostCurveAnalyzer()
    result = analyzer.run(
        strategy_config={"name": "test"},
        spread_scenarios=[0.0, 1.0, 2.0],
    )

    assert len(result.table.rows) == 3
    for row in result.table.rows:
        assert hasattr(row, "spread_pips")
        assert hasattr(row, "sharpe")


def test_cost_curve_breakeven_is_factual():
    """Breakeven is factual (sharpe=0), not "acceptable"."""
    from validation.cost_curve import CostCurveAnalyzer

    analyzer = CostCurveAnalyzer()
    result = analyzer.run(
        strategy_config={"name": "test"},
        base_sharpe=1.5,
    )

    # Breakeven is where sharpe = 0
    assert hasattr(result.breakeven, "spread_at_zero_sharpe")

    # NOT "maximum_acceptable_spread"
    assert not hasattr(result.breakeven, "maximum_acceptable_spread")
    assert not hasattr(result.breakeven, "recommended_max")


def test_cost_curve_table_spread_ordered():
    """Cost curve table is spread-ordered."""
    from validation.cost_curve import CostCurveAnalyzer

    analyzer = CostCurveAnalyzer()
    result = analyzer.run(
        strategy_config={"name": "test"},
        spread_scenarios=[0.0, 1.0, 2.0, 3.0],
    )

    assert result.table.sort_order == "SPREAD_ORDER"

    # Verify ascending order
    spreads = [row.spread_pips for row in result.table.rows]
    assert spreads == sorted(spreads)


def test_cost_curve_mandatory_disclaimer():
    """CostCurveResult has mandatory disclaimer."""
    from validation.cost_curve import CostCurveResult

    result = CostCurveResult()
    assert "FACTS_ONLY" in result.disclaimer


def test_cost_curve_no_color_metadata():
    """CostCurveResult has null color metadata."""
    from validation.cost_curve import CostCurveResult

    result = CostCurveResult()

    assert result.visual_metadata.color_scale is None
    assert result.visual_metadata.highlight_threshold is None


def test_cost_curve_row_no_acceptability():
    """CostCurveRow has no acceptability field."""
    from validation.cost_curve import CostCurveRow

    row = CostCurveRow(
        spread_pips=1.0,
        sharpe=1.0,
        profit_factor=1.5,
        net_pnl=5000.0,
    )

    # Decomposed only
    assert row.spread_pips == 1.0
    assert row.sharpe == 1.0

    # No acceptability
    assert not hasattr(row, "acceptable")
    assert not hasattr(row, "tradeable")


def test_cost_curve_forbidden_terms():
    """FORBIDDEN_TERMS contains acceptability patterns."""
    from validation.cost_curve import FORBIDDEN_TERMS

    assert "acceptable_spread" in FORBIDDEN_TERMS
    assert "cost_tolerance" in FORBIDDEN_TERMS
    assert "tradeable" in FORBIDDEN_TERMS
    assert "recommend" in FORBIDDEN_TERMS


def test_cost_curve_id_auto_generated():
    """CostCurveResult generates unique ID."""
    from validation.cost_curve import CostCurveResult

    result1 = CostCurveResult()
    result2 = CostCurveResult()

    assert result1.cc_id.startswith("CC_")
    assert result1.cc_id != result2.cc_id


def test_cost_curve_provenance_complete():
    """CostCurveResult has full provenance."""
    from validation.cost_curve import CostCurveAnalyzer

    analyzer = CostCurveAnalyzer()
    result = analyzer.run(
        strategy_config={"name": "test"},
        spread_scenarios=[0.0, 1.0],
    )

    assert result.provenance.query_string != ""
    assert result.provenance.dataset_hash != ""


def test_cost_curve_degradation_monotonic():
    """Sharpe degrades with spread."""
    from validation.cost_curve import CostCurveAnalyzer

    analyzer = CostCurveAnalyzer()
    result = analyzer.run(
        strategy_config={"name": "test"},
        spread_scenarios=[0.0, 1.0, 2.0, 3.0],
        base_sharpe=2.0,
    )

    # Higher spread → lower sharpe (simplified model)
    sharpes = [row.sharpe for row in result.table.rows]
    # With our linear degradation model
    assert sharpes == sorted(sharpes, reverse=True)
