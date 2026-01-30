"""
Pre-Commit Hook Tests — S40 Track C
===================================

Proves INV-HOOK-1 and INV-HOOK-2.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from tools.hooks.pre_commit_linter import (
    PreCommitLinter,
    LintRule,
    Violation,
    ViolationSeverity,
    has_blocking_violations,
)
from tools.hooks.scalar_ban_hook import (
    ScalarBanHook,
    get_constitutional_rules,
    SCALAR_PATTERNS,
    AVG_PATTERNS,
    CAUSAL_PATTERNS,
    GRADE_PATTERNS,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def linter() -> PreCommitLinter:
    """Create linter with all constitutional rules."""
    return PreCommitLinter(get_constitutional_rules())


@pytest.fixture
def hook() -> ScalarBanHook:
    """Create scalar ban hook."""
    return ScalarBanHook()


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# =============================================================================
# INV-HOOK-1: BLOCKS SCALAR_SCORE
# =============================================================================


class TestScalarBan:
    """Prove INV-HOOK-1: Pre-commit blocks scalar_score in new code."""

    def test_catches_scalar_score(self, hook: ScalarBanHook, temp_dir: Path):
        """INV-HOOK-1: scalar_score is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("result.scalar_score = compute_value(data)")

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        assert any("scalar_score" in v.matched_text.lower() for v in violations)
        print("✓ INV-HOOK-1: scalar_score caught")

    def test_catches_viability_index(self, hook: ScalarBanHook, temp_dir: Path):
        """viability_index is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("strategy.viability_index = 0.85")

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        assert any("viability_index" in v.matched_text.lower() for v in violations)
        print("✓ viability_index caught")

    def test_catches_confidence_score(self, hook: ScalarBanHook, temp_dir: Path):
        """confidence_score is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text('result["confidence_score"] = compute_confidence()')

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ confidence_score caught")

    def test_catches_overall_quality(self, hook: ScalarBanHook, temp_dir: Path):
        """overall_quality is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("overall_quality = sum(metrics) / len(metrics)")

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ overall_quality caught")

    def test_clean_code_passes(self, hook: ScalarBanHook, temp_dir: Path):
        """Clean code without violations passes."""
        test_file = temp_dir / "good_code.py"
        test_file.write_text("""
def analyze_strategy(params):
    # Return decomposed metrics, not scalar scores
    return {
        "sharpe_array": compute_sharpe_array(params),
        "returns_array": compute_returns(params),
        "drawdown_curve": compute_drawdown(params),
    }
""")

        violations = hook.check_file(test_file)

        assert len(violations) == 0
        print("✓ Clean code passes")


# =============================================================================
# INV-HOOK-2: BLOCKS CAUSAL LANGUAGE
# =============================================================================


class TestCausalLanguageBan:
    """Prove INV-HOOK-2: Pre-commit blocks causal language."""

    def test_catches_contributed_to(self, hook: ScalarBanHook, temp_dir: Path):
        """INV-HOOK-2: 'contributed to' is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text('attribution = "Parameter X contributed to 30% of returns"')

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        assert any("contributed to" in v.matched_text.lower() for v in violations)
        print("✓ INV-HOOK-2: 'contributed to' caught")

    def test_catches_caused_by(self, hook: ScalarBanHook, temp_dir: Path):
        """'caused by' is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text('message = "Drawdown caused by market volatility"')

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ 'caused by' caught")

    def test_catches_drove_percentage(self, hook: ScalarBanHook, temp_dir: Path):
        """'drove X%' is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text('report = "Parameter Y drove 45% of performance"')

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ 'drove X%' caught")


# =============================================================================
# RANKING BAN
# =============================================================================


class TestRankingBan:
    """Test ranking pattern detection."""

    def test_catches_rank_position(self, hook: ScalarBanHook, temp_dir: Path):
        """rank_position is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("strategy.rank_position = 1")

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ rank_position caught")

    def test_catches_best_strategy(self, hook: ScalarBanHook, temp_dir: Path):
        """best_strategy is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("best_strategy = strategies[0]")

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ best_strategy caught")


# =============================================================================
# GRADE BAN
# =============================================================================


class TestGradeBan:
    """Test grade pattern detection."""

    def test_catches_grade_a(self, hook: ScalarBanHook, temp_dir: Path):
        """'Grade A' is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text('result.grade = "Grade A"')

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ 'Grade A' caught")

    def test_catches_quality_grade(self, hook: ScalarBanHook, temp_dir: Path):
        """quality_grade is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text('setup["quality_grade"] = "excellent"')

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ quality_grade caught")


# =============================================================================
# AVG PATTERN BAN
# =============================================================================


class TestAvgBan:
    """Test hidden average pattern detection."""

    def test_catches_avg_sharpe(self, hook: ScalarBanHook, temp_dir: Path):
        """avg_sharpe is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("avg_sharpe = np.mean(sharpe_array)")

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ avg_sharpe caught")

    def test_catches_mean_return(self, hook: ScalarBanHook, temp_dir: Path):
        """mean_return is caught."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("mean_return = returns.mean()")

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ mean_return caught")


# =============================================================================
# REPORT FORMAT
# =============================================================================


class TestReportFormat:
    """Test violation report formatting."""

    def test_report_includes_file(self, hook: ScalarBanHook, temp_dir: Path):
        """Report includes file path."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("scalar_score = 0.5")

        violations = hook.check_file(test_file)
        report = hook.format_report(violations)

        assert "bad_code.py" in report
        print("✓ Report includes file path")

    def test_report_includes_line_number(self, hook: ScalarBanHook, temp_dir: Path):
        """Report includes line number."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("x = 1\nscalar_score = 0.5\ny = 2")

        violations = hook.check_file(test_file)
        report = hook.format_report(violations)

        assert "L2" in report or ":2:" in report
        print("✓ Report includes line number")


# =============================================================================
# CHAOS: OBFUSCATION ATTEMPTS
# =============================================================================


class TestObfuscationChaos:
    """Chaos tests for obfuscation attempts."""

    def test_catches_in_docstring(self, hook: ScalarBanHook, temp_dir: Path):
        """Catches heresy in docstrings (still bad)."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text('"""Returns scalar_score for the strategy."""')

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ Caught in docstring")

    def test_catches_quality_metric_obfuscation(self, hook: ScalarBanHook, temp_dir: Path):
        """Catches quality_metric (obfuscated scalar)."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("quality_metric = compute_quality()")

        violations = hook.check_file(test_file)

        assert len(violations) >= 1
        print("✓ Caught quality_metric obfuscation")

    def test_multiple_violations_single_file(self, hook: ScalarBanHook, temp_dir: Path):
        """Catches multiple violations in single file."""
        test_file = temp_dir / "very_bad_code.py"
        test_file.write_text("""
scalar_score = 0.5
best_strategy = strategies[0]
quality_grade = "A"
avg_sharpe = 1.5
""")

        violations = hook.check_file(test_file)

        assert len(violations) >= 4
        print(f"✓ Caught {len(violations)} violations in single file")


# =============================================================================
# BLOCKING LOGIC
# =============================================================================


class TestBlockingLogic:
    """Test commit blocking logic."""

    def test_errors_block_commit(self, hook: ScalarBanHook, temp_dir: Path):
        """ERROR violations block commit."""
        test_file = temp_dir / "bad_code.py"
        test_file.write_text("scalar_score = 0.5")

        violations = hook.check_file(test_file)

        assert has_blocking_violations(violations)
        print("✓ ERROR violations block commit")

    def test_clean_code_doesnt_block(self, hook: ScalarBanHook, temp_dir: Path):
        """Clean code doesn't block commit."""
        test_file = temp_dir / "good_code.py"
        test_file.write_text("metrics = compute_decomposed_metrics()")

        violations = hook.check_file(test_file)

        assert not has_blocking_violations(violations)
        print("✓ Clean code doesn't block")
