"""
Tests for Scalar Ban Linter — S39 Track F
=========================================

THE CONSTITUTIONAL CEILING.
Tests the "Linter of Linters."
"""

from __future__ import annotations


def test_linter_catches_score_fields():
    """Linter catches *_score fields."""
    from validation.scalar_ban_linter import ScalarBanLinter, ViolationType

    linter = ScalarBanLinter()

    data = {
        "quality_score": 0.85,
        "sharpe": 1.5,
    }

    result = linter.lint(data)

    assert not result.valid
    assert len(result.violations) == 1
    assert result.violations[0].violation_type == ViolationType.FORBIDDEN_FIELD


def test_linter_catches_avg_fields():
    """Linter catches avg_* fields (INV-NO-AGGREGATE-SCALAR)."""
    from validation.scalar_ban_linter import ScalarBanLinter, ViolationType

    linter = ScalarBanLinter()

    data = {
        "avg_sharpe": 1.5,
        "avg_win_rate": 0.55,
    }

    result = linter.lint(data)

    assert not result.valid
    # Should catch both avg_* fields
    avg_violations = [v for v in result.violations if v.violation_type == ViolationType.AVG_FIELD]
    assert len(avg_violations) == 2


def test_linter_catches_evaluative_adjectives():
    """Linter catches evaluative adjectives."""
    from validation.scalar_ban_linter import ScalarBanLinter, ViolationType

    linter = ScalarBanLinter()

    result = linter.lint_text("The strategy shows strong performance")

    assert not result.valid
    adj_violations = [
        v for v in result.violations if v.violation_type == ViolationType.EVALUATIVE_ADJECTIVE
    ]
    assert len(adj_violations) >= 1


def test_linter_catches_verdict_language():
    """Linter catches verdict language."""
    from validation.scalar_ban_linter import ScalarBanLinter, ViolationType

    linter = ScalarBanLinter()

    result = linter.lint_text("The system appears overfit")

    assert not result.valid
    verdict_violations = [
        v for v in result.violations if v.violation_type == ViolationType.VERDICT_LANGUAGE
    ]
    assert len(verdict_violations) >= 1


def test_linter_catches_color_metadata():
    """Linter catches non-null color metadata."""
    from validation.scalar_ban_linter import ScalarBanLinter, ViolationType

    linter = ScalarBanLinter()

    data = {
        "sharpe": 1.5,
        "color_scale": {"red": "bad", "green": "good"},
    }

    result = linter.lint(data)

    assert not result.valid
    color_violations = [
        v for v in result.violations if v.violation_type == ViolationType.COLOR_METADATA
    ]
    assert len(color_violations) == 1


def test_linter_passes_clean_data():
    """Linter passes clean data."""
    from validation.scalar_ban_linter import ScalarBanLinter

    linter = ScalarBanLinter()

    data = {
        "sharpe": 1.5,
        "win_rate": 0.55,
        "profit_factor": 1.8,
        "max_drawdown": 0.12,
        "disclaimer": "FACTS_ONLY",
        "color_scale": None,  # null is OK
    }

    result = linter.lint(data)

    assert result.valid
    assert len(result.violations) == 0


def test_linter_catches_index_fields():
    """Linter catches *_index fields."""
    from validation.scalar_ban_linter import ScalarBanLinter

    linter = ScalarBanLinter()

    data = {"viability_index": 0.9}

    result = linter.lint(data)

    assert not result.valid


def test_linter_catches_nested_violations():
    """Linter catches violations in nested dicts."""
    from validation.scalar_ban_linter import ScalarBanLinter

    linter = ScalarBanLinter()

    data = {
        "metrics": {
            "base": {
                "robustness_score": 0.8,  # nested forbidden
            },
        },
    }

    result = linter.lint(data)

    assert not result.valid
    assert any("robustness_score" in v.field_or_text for v in result.violations)


def test_linter_catches_threshold_implications():
    """Linter catches threshold implication language."""
    from validation.scalar_ban_linter import ScalarBanLinter, ViolationType

    linter = ScalarBanLinter()

    # Test above threshold pattern
    result = linter.lint_text("The value is above threshold for viability")

    assert not result.valid
    threshold_violations = [
        v for v in result.violations if v.violation_type == ViolationType.THRESHOLD_IMPLICATION
    ]
    assert len(threshold_violations) >= 1


def test_linter_catches_comparison_superlatives():
    """Linter catches comparison superlatives."""
    from validation.scalar_ban_linter import ScalarBanLinter, ViolationType

    linter = ScalarBanLinter()

    result = linter.lint_text("This is the most sensitive parameter")

    assert not result.valid
    superlative_violations = [
        v for v in result.violations if v.violation_type == ViolationType.COMPARISON_SUPERLATIVE
    ]
    assert len(superlative_violations) >= 1


def test_linter_catches_summary_synthesis():
    """Linter catches summary synthesis language."""
    from validation.scalar_ban_linter import ScalarBanLinter, ViolationType

    linter = ScalarBanLinter()

    result = linter.lint_text("Overall, the system performs well")

    assert not result.valid
    synthesis_violations = [
        v for v in result.violations if v.violation_type == ViolationType.SUMMARY_SYNTHESIS
    ]
    assert len(synthesis_violations) >= 1


def test_linter_error_messages():
    """Linter provides error messages."""
    from validation.scalar_ban_linter import ScalarBanLinter

    linter = ScalarBanLinter()

    data = {"quality_score": 0.85}
    result = linter.lint(data)

    assert len(result.error_messages) > 0
    assert "FORBIDDEN_FIELD" in result.error_messages[0]


def test_scalar_ban_error_exception():
    """ScalarBanError contains violations."""
    from validation.scalar_ban_linter import ScalarBanError, ScalarBanViolation, ViolationType

    violations = [
        ScalarBanViolation(
            violation_type=ViolationType.FORBIDDEN_FIELD,
            field_or_text="quality_score",
            pattern_matched=".*_score$",
            message="Forbidden field pattern",
        )
    ]

    error = ScalarBanError(violations)

    assert len(error.violations) == 1
    assert "Forbidden field pattern" in str(error)


def test_linter_catches_list_violations():
    """Linter catches violations in lists."""
    from validation.scalar_ban_linter import ScalarBanLinter

    linter = ScalarBanLinter()

    data = {
        "splits": [
            {"split_id": 0, "overfit_score": 0.8},  # forbidden
            {"split_id": 1, "sharpe": 1.5},
        ],
    }

    result = linter.lint(data)

    assert not result.valid


def test_evaluative_adjectives_constant():
    """EVALUATIVE_ADJECTIVES contains expected words."""
    from validation.scalar_ban_linter import EVALUATIVE_ADJECTIVES

    assert "strong" in EVALUATIVE_ADJECTIVES
    assert "weak" in EVALUATIVE_ADJECTIVES
    assert "solid" in EVALUATIVE_ADJECTIVES
    assert "fragile" in EVALUATIVE_ADJECTIVES
    assert "robust" in EVALUATIVE_ADJECTIVES


def test_linter_passes_mathematical_descriptors():
    """Linter passes mathematical descriptors."""
    from validation.scalar_ban_linter import ScalarBanLinter

    linter = ScalarBanLinter()

    # Mathematical descriptors are OK
    result = linter.lint_text("The median value is 1.5. The standard deviation is 0.3.")

    assert result.valid


def test_linter_catches_recommend_language():
    """Linter catches recommend language."""
    from validation.scalar_ban_linter import ScalarBanLinter

    linter = ScalarBanLinter()

    result = linter.lint_text("We recommend using a spread below 1.0")

    assert not result.valid
