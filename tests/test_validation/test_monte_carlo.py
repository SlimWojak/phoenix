"""
Tests for Monte Carlo Simulation — S39 Track C
==============================================

Verifies percentiles, no risk verdicts.
Raw simulations T2-gated.
"""

from __future__ import annotations


def test_monte_carlo_no_risk_verdict():
    """MonteCarloResult has no risk verdict fields."""
    from validation.monte_carlo import MonteCarloResult

    result = MonteCarloResult()

    # MUST NOT have risk verdicts
    assert not hasattr(result, "risk_level")
    assert not hasattr(result, "risk_score")
    assert not hasattr(result, "danger_zone")
    assert not hasattr(result, "acceptable_risk")
    assert not hasattr(result, "verdict")


def test_monte_carlo_has_percentiles():
    """MonteCarloResult contains percentiles."""
    from validation.monte_carlo import MonteCarloSimulator

    simulator = MonteCarloSimulator()
    result = simulator.run(
        strategy_config={"name": "test"},
        n_simulations=100,
    )

    # Has drawdown percentiles
    dd = result.distribution.drawdown_percentiles
    assert hasattr(dd, "p5")
    assert hasattr(dd, "p25")
    assert hasattr(dd, "p50")
    assert hasattr(dd, "p75")
    assert hasattr(dd, "p95")


def test_monte_carlo_raw_null_by_default():
    """Raw simulations are null by default."""
    from validation.monte_carlo import MonteCarloSimulator

    simulator = MonteCarloSimulator()
    result = simulator.run(
        strategy_config={"name": "test"},
        n_simulations=100,
        include_raw=False,
    )

    assert result.raw_simulations.drawdowns is None


def test_monte_carlo_raw_requires_t2():
    """Raw simulations require T2 access."""
    from validation.monte_carlo import MonteCarloSimulator

    simulator = MonteCarloSimulator()

    # T1 with include_raw=True → still null
    result_t1 = simulator.run(
        strategy_config={"name": "test"},
        n_simulations=100,
        include_raw=True,
        tier="T1",
    )
    assert result_t1.raw_simulations.drawdowns is None

    # T2 with include_raw=True → populated
    result_t2 = simulator.run(
        strategy_config={"name": "test"},
        n_simulations=100,
        include_raw=True,
        tier="T2",
    )
    assert result_t2.raw_simulations.drawdowns is not None
    assert len(result_t2.raw_simulations.drawdowns) == 100


def test_monte_carlo_mandatory_disclaimer():
    """MonteCarloResult has mandatory disclaimer."""
    from validation.monte_carlo import MonteCarloResult

    result = MonteCarloResult()
    assert "FACTS_ONLY" in result.disclaimer


def test_monte_carlo_no_color_metadata():
    """MonteCarloResult has null color metadata."""
    from validation.monte_carlo import MonteCarloResult

    result = MonteCarloResult()

    assert result.visual_metadata.color_scale is None
    assert result.visual_metadata.highlight_threshold is None


def test_monte_carlo_return_percentiles():
    """MonteCarloResult has return percentiles."""
    from validation.monte_carlo import MonteCarloSimulator

    simulator = MonteCarloSimulator()
    result = simulator.run(
        strategy_config={"name": "test"},
        n_simulations=100,
    )

    ret = result.distribution.return_percentiles
    assert hasattr(ret, "p5")
    assert hasattr(ret, "p50")
    assert hasattr(ret, "p95")


def test_monte_carlo_forbidden_fields_constant():
    """FORBIDDEN_FIELDS contains risk verdict patterns."""
    from validation.monte_carlo import FORBIDDEN_FIELDS

    assert "risk_level" in FORBIDDEN_FIELDS
    assert "risk_score" in FORBIDDEN_FIELDS
    assert "danger_zone" in FORBIDDEN_FIELDS
    assert "verdict" in FORBIDDEN_FIELDS


def test_monte_carlo_id_auto_generated():
    """MonteCarloResult generates unique ID."""
    from validation.monte_carlo import MonteCarloResult

    result1 = MonteCarloResult()
    result2 = MonteCarloResult()

    assert result1.mc_id.startswith("MC_")
    assert result1.mc_id != result2.mc_id


def test_monte_carlo_provenance_complete():
    """MonteCarloResult has full provenance."""
    from validation.monte_carlo import MonteCarloSimulator

    simulator = MonteCarloSimulator()
    result = simulator.run(
        strategy_config={"name": "test"},
        n_simulations=100,
    )

    assert result.provenance.query_string != ""
    assert result.provenance.dataset_hash != ""
    assert result.provenance.governance_hash != ""


def test_monte_carlo_percentiles_ordered():
    """Percentiles are ordered (p5 < p50 < p95 for drawdown)."""
    from validation.monte_carlo import MonteCarloSimulator

    simulator = MonteCarloSimulator()
    result = simulator.run(
        strategy_config={"name": "test"},
        n_simulations=1000,
    )

    dd = result.distribution.drawdown_percentiles
    assert dd.p5 <= dd.p25 <= dd.p50 <= dd.p75 <= dd.p95
