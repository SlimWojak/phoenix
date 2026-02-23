"""
Causal Ban Linter Tests — S35 Track D
=====================================

INVARIANT PROVEN: INV-ATTR-CAUSAL-BAN
  Rule: No causal claims ("factor X contributed Y%")

EXIT GATE D:
  Criterion: "Linter catches all causal patterns; allows all conditional patterns"
  Proof: "30+ causal phrases FAIL, 20+ conditional phrases PASS"
"""

import pytest

from cfp.linter import CausalBanLinter, ViolationType

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def linter() -> CausalBanLinter:
    """Create linter instance."""
    return CausalBanLinter()


# =============================================================================
# BANNED PHRASES (20+ tests)
# =============================================================================


class TestBannedPhrases:
    """Tests for banned phrase detection."""

    def test_contributed_fails(self, linter: CausalBanLinter) -> None:
        """'contributed' is banned."""
        result = linter.lint("London contributed 40% to performance")
        assert not result.passed
        assert any(v.pattern == "contributed" for v in result.violations)

    def test_caused_fails(self, linter: CausalBanLinter) -> None:
        """'caused' is banned."""
        result = linter.lint("This caused the drawdown")
        assert not result.passed

    def test_because_fails(self, linter: CausalBanLinter) -> None:
        """'because' is banned."""
        result = linter.lint("Performance improved because of timing")
        assert not result.passed

    def test_explains_fails(self, linter: CausalBanLinter) -> None:
        """'explains' is banned."""
        result = linter.lint("Session timing explains the difference")
        assert not result.passed

    def test_factor_fails(self, linter: CausalBanLinter) -> None:
        """'factor' is banned."""
        result = linter.lint("Key factor in success")
        assert not result.passed

    def test_drove_fails(self, linter: CausalBanLinter) -> None:
        """'drove' is banned."""
        result = linter.lint("London sessions drove performance")
        assert not result.passed

    def test_predicts_fails(self, linter: CausalBanLinter) -> None:
        """'predicts' is banned (GPT v0.2)."""
        result = linter.lint("This pattern predicts outcomes")
        assert not result.passed

    def test_leads_to_fails(self, linter: CausalBanLinter) -> None:
        """'leads to' is banned (GPT v0.2)."""
        result = linter.lint("This leads to better results")
        assert not result.passed

    def test_signal_fails(self, linter: CausalBanLinter) -> None:
        """'signal' is banned (GPT v0.2)."""
        result = linter.lint("Strong signal for entry")
        assert not result.passed

    def test_edge_fails(self, linter: CausalBanLinter) -> None:
        """'edge' is banned (GPT v0.2)."""
        result = linter.lint("This provides an edge")
        assert not result.passed

    def test_alpha_fails(self, linter: CausalBanLinter) -> None:
        """'alpha' is banned (GPT v0.2)."""
        result = linter.lint("Generates significant alpha")
        assert not result.passed

    def test_impact_fails(self, linter: CausalBanLinter) -> None:
        """'impact' is banned."""
        result = linter.lint("News impact on price")
        assert not result.passed

    def test_influence_fails(self, linter: CausalBanLinter) -> None:
        """'influence' is banned."""
        result = linter.lint("Session influence on performance")
        assert not result.passed

    def test_affect_fails(self, linter: CausalBanLinter) -> None:
        """'affect' is banned."""
        result = linter.lint("This doesn't affect results")
        assert not result.passed

    def test_result_of_fails(self, linter: CausalBanLinter) -> None:
        """'result of' is banned."""
        result = linter.lint("This is a result of timing")
        assert not result.passed

    def test_due_to_fails(self, linter: CausalBanLinter) -> None:
        """'due to' is banned."""
        result = linter.lint("Performance due to timing")
        assert not result.passed

    def test_responsible_fails(self, linter: CausalBanLinter) -> None:
        """'responsible' is banned."""
        result = linter.lint("London is responsible for gains")
        assert not result.passed

    def test_determine_fails(self, linter: CausalBanLinter) -> None:
        """'determine' is banned."""
        result = linter.lint("Timing determines outcome")
        assert not result.passed

    def test_outperforms_fails(self, linter: CausalBanLinter) -> None:
        """'outperforms' is banned (GPT v0.2)."""
        result = linter.lint("Strategy A outperforms B")
        assert not result.passed


# =============================================================================
# METRIC + AGENT TESTS (GPT v0.2)
# =============================================================================


class TestMetricAgent:
    """Tests for metric + agent verb violations."""

    def test_sharpe_improved_fails(self, linter: CausalBanLinter) -> None:
        """'Sharpe improved' implies causality."""
        result = linter.lint("Sharpe improved after London open")
        assert not result.passed
        assert any(v.violation_type == ViolationType.METRIC_AGENT for v in result.violations)

    def test_win_rate_increased_fails(self, linter: CausalBanLinter) -> None:
        """'win_rate increased' implies causality."""
        result = linter.lint("Win_rate increased during NY session")
        assert not result.passed

    def test_pnl_decreased_fails(self, linter: CausalBanLinter) -> None:
        """'PnL decreased' implies causality."""
        result = linter.lint("PnL decreased following news")
        assert not result.passed

    def test_performance_changed_fails(self, linter: CausalBanLinter) -> None:
        """'performance changed' implies causality."""
        result = linter.lint("Performance changed after implementation")
        assert not result.passed


# =============================================================================
# TEMPORAL IMPLICATION TESTS (OWL v0.2)
# =============================================================================


class TestTemporalImplication:
    """Tests for temporal implication violations."""

    def test_after_without_anchor_fails(self, linter: CausalBanLinter) -> None:
        """'after' without anchor fails."""
        result = linter.lint("Result after news event")
        assert not result.passed
        assert any(
            v.violation_type == ViolationType.TEMPORAL_IMPLICATION for v in result.violations
        )

    def test_following_without_anchor_fails(self, linter: CausalBanLinter) -> None:
        """'following' without anchor fails."""
        result = linter.lint("Following the breakout")
        assert not result.passed

    def test_after_with_time_range_passes(self, linter: CausalBanLinter) -> None:
        """'after' with time_range anchor passes."""
        result = linter.lint("Result after time_range=[08:30, 09:00]")
        assert result.passed

    def test_after_with_session_passes(self, linter: CausalBanLinter) -> None:
        """'after' with session anchor passes."""
        result = linter.lint("Result after session=London filter applied")
        assert result.passed


# =============================================================================
# ALLOWED PATTERNS (20+ tests)
# =============================================================================


class TestAllowedPatterns:
    """Tests for allowed conditional patterns."""

    def test_when_condition_passes(self, linter: CausalBanLinter) -> None:
        """'when [condition]' is allowed."""
        result = linter.lint("Sharpe when session=London")
        assert result.passed

    def test_conditional_on_passes(self, linter: CausalBanLinter) -> None:
        """'conditional on' is allowed."""
        result = linter.lint("Conditional on regime=trending")
        assert result.passed

    def test_given_that_passes(self, linter: CausalBanLinter) -> None:
        """'given that' is allowed."""
        result = linter.lint("Given that gates_passed >= 3")
        assert result.passed

    def test_filtered_by_passes(self, linter: CausalBanLinter) -> None:
        """'filtered by' is allowed."""
        result = linter.lint("Results filtered by pair=EURUSD")
        assert result.passed

    def test_where_passes(self, linter: CausalBanLinter) -> None:
        """'where' is allowed."""
        result = linter.lint("Performance where direction=LONG")
        assert result.passed

    def test_pnl_when_condition_passes(self, linter: CausalBanLinter) -> None:
        """'P&L when [condition]' is allowed."""
        result = linter.lint("P&L when kill_zone=LondonOpen")
        assert result.passed

    def test_sharpe_conditional_on_passes(self, linter: CausalBanLinter) -> None:
        """'Sharpe conditional on [predicate]' is allowed."""
        result = linter.lint("Sharpe conditional on htf_alignment=true")
        assert result.passed

    def test_win_rate_where_passes(self, linter: CausalBanLinter) -> None:
        """'Win rate where [filter]' is allowed."""
        result = linter.lint("Win rate where zone=discount")
        assert result.passed

    def test_during_passes(self, linter: CausalBanLinter) -> None:
        """'during' is allowed."""
        result = linter.lint("Performance during London session")
        assert result.passed

    def test_within_passes(self, linter: CausalBanLinter) -> None:
        """'within' is allowed."""
        result = linter.lint("Trades within time range")
        assert result.passed

    def test_pure_metric_value_passes(self, linter: CausalBanLinter) -> None:
        """Pure metric values pass."""
        result = linter.lint("Sharpe: 1.6")
        assert result.passed

    def test_metric_equals_value_passes(self, linter: CausalBanLinter) -> None:
        """'metric = value' passes."""
        result = linter.lint("win_rate = 0.61")
        assert result.passed

    def test_comparison_passes(self, linter: CausalBanLinter) -> None:
        """Comparisons pass."""
        result = linter.lint("London: 1.6, Tokyo: 0.8")
        assert result.passed

    def test_conditional_fact_passes(self, linter: CausalBanLinter) -> None:
        """Conditional fact format passes."""
        result = linter.lint("When session=London AND gates_passed>=3: Sharpe=1.8")
        assert result.passed

    def test_sample_size_passes(self, linter: CausalBanLinter) -> None:
        """Sample size notation passes."""
        result = linter.lint("N=47, Sharpe=1.6")
        assert result.passed

    def test_time_range_query_passes(self, linter: CausalBanLinter) -> None:
        """Time range query passes."""
        result = linter.lint("time_range=[2025-01-01, 2026-01-01]")
        assert result.passed

    def test_group_by_passes(self, linter: CausalBanLinter) -> None:
        """group_by notation passes."""
        result = linter.lint("group_by: [session, pair]")
        assert result.passed

    def test_filter_condition_passes(self, linter: CausalBanLinter) -> None:
        """Filter condition passes."""
        result = linter.lint("filter: pair == EURUSD")
        assert result.passed


# =============================================================================
# FALSE POSITIVE PROTECTION
# =============================================================================


class TestFalsePositives:
    """Tests for false positive protection."""

    def test_conditional_attribution_passes(self, linter: CausalBanLinter) -> None:
        """'conditional attribution' is exception."""
        result = linter.lint("This is conditional attribution, not causal")
        assert result.passed

    def test_no_causal_passes(self, linter: CausalBanLinter) -> None:
        """'no causal' is exception."""
        result = linter.lint("There is no causal relationship")
        assert result.passed


# =============================================================================
# QUERY LINTING
# =============================================================================


class TestQueryLinting:
    """Tests for query dictionary linting."""

    def test_lint_query_with_causal_value_fails(self, linter: CausalBanLinter) -> None:
        """Query with causal value in predicate fails."""
        query = {
            "filter": {
                "conditions": [{"field": "note", "op": "==", "value": "This caused the drawdown"}]
            }
        }
        result = linter.lint_query(query)
        assert not result.passed

    def test_lint_query_clean_passes(self, linter: CausalBanLinter) -> None:
        """Clean query passes."""
        query = {"filter": {"conditions": [{"field": "session", "op": "==", "value": "London"}]}}
        result = linter.lint_query(query)
        assert result.passed


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_string_passes(self, linter: CausalBanLinter) -> None:
        """Empty string passes."""
        result = linter.lint("")
        assert result.passed

    def test_none_equivalent_passes(self, linter: CausalBanLinter) -> None:
        """Whitespace-only passes."""
        result = linter.lint("   ")
        assert result.passed

    def test_case_insensitive(self, linter: CausalBanLinter) -> None:
        """Detection is case-insensitive."""
        result = linter.lint("CONTRIBUTED")
        assert not result.passed

    def test_multiple_violations_detected(self, linter: CausalBanLinter) -> None:
        """Multiple violations in one text detected."""
        result = linter.lint("This caused and contributed to the impact")
        assert not result.passed
        assert len(result.violations) >= 2


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
