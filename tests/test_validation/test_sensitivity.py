"""
Tests for Sensitivity Analysis — S39 Track D
============================================

Verifies param-ordered tables, no importance ranking.
Shuffle opt-in.
"""

from __future__ import annotations


def test_sensitivity_no_importance_ranking():
    """SensitivityResult has no importance ranking."""
    from validation.sensitivity import SensitivityResult

    result = SensitivityResult()

    # MUST NOT have importance/impact
    assert not hasattr(result, "importance")
    assert not hasattr(result, "impact_score")
    assert not hasattr(result, "most_sensitive")
    assert not hasattr(result, "magnitude_rank")


def test_sensitivity_table_param_ordered():
    """Sensitivity table is param-ordered by default."""
    from validation.sensitivity import SensitivityAnalyzer

    analyzer = SensitivityAnalyzer()
    result = analyzer.run(
        base_params={"threshold": 0.5},
        varied_param="threshold",
        variation_range=[0.3, 0.4, 0.5, 0.6, 0.7],
        shuffle=False,
    )

    assert result.table.sort_order == "PARAM_ORDER"
    assert not result.table.shuffle_applied


def test_sensitivity_shuffle_opt_in():
    """Shuffle is opt-in (T2)."""
    from validation.sensitivity import SensitivityAnalyzer

    analyzer = SensitivityAnalyzer()
    result = analyzer.run(
        base_params={"threshold": 0.5},
        varied_param="threshold",
        variation_range=[0.3, 0.4, 0.5],
        shuffle=True,
    )

    assert result.table.shuffle_applied is True
    assert result.table.sort_order == "SHUFFLED"


def test_sensitivity_rows_no_importance():
    """SensitivityRow has no importance field."""
    from validation.sensitivity import SensitivityRow

    row = SensitivityRow(
        param_value=0.5,
        sharpe=1.5,
        win_rate=0.55,
        max_drawdown=0.10,
    )

    # Decomposed metrics only
    assert row.param_value == 0.5
    assert row.sharpe == 1.5

    # No importance
    assert not hasattr(row, "importance")
    assert not hasattr(row, "impact")


def test_sensitivity_mandatory_disclaimer():
    """SensitivityResult has mandatory disclaimer."""
    from validation.sensitivity import SensitivityResult

    result = SensitivityResult()
    assert "FACTS_ONLY" in result.disclaimer


def test_sensitivity_forbidden_terms():
    """FORBIDDEN_TERMS contains importance patterns."""
    from validation.sensitivity import FORBIDDEN_TERMS

    assert "importance" in FORBIDDEN_TERMS
    assert "impact" in FORBIDDEN_TERMS
    assert "critical" in FORBIDDEN_TERMS
    assert "most_sensitive" in FORBIDDEN_TERMS


def test_sensitivity_table_columns():
    """Sensitivity table has expected columns."""
    from validation.sensitivity import SensitivityTable

    table = SensitivityTable()

    assert "param_value" in table.columns
    assert "sharpe" in table.columns
    assert "win_rate" in table.columns
    assert "max_drawdown" in table.columns

    # NO importance columns
    assert "importance" not in table.columns


def test_sensitivity_analyzer_run():
    """SensitivityAnalyzer.run returns proper result."""
    from validation.sensitivity import SensitivityAnalyzer, SensitivityResult

    analyzer = SensitivityAnalyzer()
    result = analyzer.run(
        base_params={"threshold": 0.5},
        varied_param="threshold",
        variation_range=[0.3, 0.5, 0.7],
    )

    assert isinstance(result, SensitivityResult)
    assert len(result.table.rows) == 3


def test_sensitivity_id_auto_generated():
    """SensitivityResult generates unique ID."""
    from validation.sensitivity import SensitivityResult

    result1 = SensitivityResult()
    result2 = SensitivityResult()

    assert result1.sens_id.startswith("SENS_")
    assert result1.sens_id != result2.sens_id


def test_sensitivity_no_color_metadata():
    """SensitivityResult has null color metadata."""
    from validation.sensitivity import SensitivityResult

    result = SensitivityResult()

    assert result.visual_metadata.color_scale is None
    assert result.visual_metadata.highlight_threshold is None


def test_sensitivity_provenance_complete():
    """SensitivityResult has full provenance."""
    from validation.sensitivity import SensitivityAnalyzer

    analyzer = SensitivityAnalyzer()
    result = analyzer.run(
        base_params={"threshold": 0.5},
        varied_param="threshold",
        variation_range=[0.3, 0.5],
    )

    assert result.provenance.query_string != ""
    assert result.provenance.dataset_hash != ""
