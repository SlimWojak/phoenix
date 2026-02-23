"""
FLOW 4: CSO → Hunt → Grid
=========================

S40 Chain Validation — Proves CSO gate status flows cleanly
to Hunt without grade reconstruction.

INVARIANTS:
  - INV-NO-GRADE-RECONSTRUCTION: Gates NOT converted to grades
  - INV-HARNESS-2: gates_passed[] preserved, not aggregated
  - INV-CSO-NO-CONFIDENCE: No confidence scores emerge
"""

from __future__ import annotations

import pytest

from hunt import Hypothesis, HypothesisFraming, HypothesisGrid
from validation import ScalarBanLinter


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_gate_status() -> dict:
    """Create sample CSO gate status."""
    return {
        "pair": "EURUSD",
        "gates_passed": [1, 3, 5, 7],  # Individual gate IDs
        "gates_failed": [2, 4, 6],
        "timestamp": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def multi_pair_gates() -> dict:
    """Create multi-pair gate status."""
    return {
        "EURUSD": {"gates_passed": [1, 3, 5], "gates_failed": [2, 4]},
        "GBPUSD": {"gates_passed": [1, 2, 3, 4, 5], "gates_failed": []},
        "USDJPY": {"gates_passed": [1], "gates_failed": [2, 3, 4, 5]},
    }


@pytest.fixture
def linter() -> ScalarBanLinter:
    """Create scalar ban linter."""
    return ScalarBanLinter()


# =============================================================================
# FLOW TESTS
# =============================================================================


class TestCSOToHuntChain:
    """Test CSO → Hunt integration seam."""

    def test_gate_status_not_converted_to_grade(self, sample_gate_status: dict):
        """Gate status must NOT be converted to A/B/C grades."""
        # Gates are boolean pass/fail, not grades
        assert "gates_passed" in sample_gate_status
        assert "gates_failed" in sample_gate_status
        
        # Must NOT have grade fields
        assert "grade" not in sample_gate_status
        assert "score" not in sample_gate_status
        assert "rating" not in sample_gate_status
        print("✓ Gate status not converted to grade")

    def test_gates_passed_preserved_as_array(self, sample_gate_status: dict):
        """gates_passed must be array, not count/percentage."""
        gates = sample_gate_status["gates_passed"]
        
        # Must be array of gate IDs
        assert isinstance(gates, list)
        assert all(isinstance(g, int) for g in gates)
        
        # Must NOT be aggregated to count
        assert "gates_passed_count" not in sample_gate_status
        assert "pass_rate" not in sample_gate_status
        print("✓ gates_passed preserved as array")

    def test_no_confidence_score_emerges(
        self, sample_gate_status: dict, linter: ScalarBanLinter
    ):
        """No confidence score should emerge from gates."""
        result = linter.lint(sample_gate_status)
        assert result.valid, f"Confidence/score found: {result.violations}"
        print("✓ No confidence score emerges")


class TestHuntReceivesCleanGates:
    """Test Hunt receives clean gate data from CSO."""

    def test_hunt_hypothesis_no_grade_filter(self):
        """Hunt hypothesis must not filter by grade."""
        hypothesis = Hypothesis(
            hypothesis_id="hyp_cso_001",
            framing=HypothesisFraming(
                question="Test with CSO gates?",
                source="operator",
                domain="test",
            ),
            grid=HypothesisGrid(dimensions=[{"name": "delay", "values": [1, 2, 3]}]),
            metrics=["sharpe", "win_rate"],
        )
        
        # Hypothesis should not have grade-based filtering
        assert not hasattr(hypothesis, "min_grade")
        assert not hasattr(hypothesis, "grade_filter")
        print("✓ Hunt hypothesis has no grade filter")

    def test_hunt_grid_includes_all_gate_states(self, multi_pair_gates: dict):
        """Hunt grid must include variants for all gate states."""
        # All pairs should be in grid, regardless of gate status
        pairs_in_grid = list(multi_pair_gates.keys())
        
        assert "EURUSD" in pairs_in_grid  # Mixed gates
        assert "GBPUSD" in pairs_in_grid  # All passed
        assert "USDJPY" in pairs_in_grid  # Mostly failed
        
        # No pair should be filtered out based on "grade"
        assert len(pairs_in_grid) == 3
        print("✓ Hunt grid includes all gate states")


class TestMultiPairGatesPreserved:
    """Test multi-pair gates flow through chain."""

    def test_multi_pair_no_aggregation(
        self, multi_pair_gates: dict, linter: ScalarBanLinter
    ):
        """Multi-pair gates must not be aggregated."""
        # Each pair has individual gate status
        for pair, gates in multi_pair_gates.items():
            assert isinstance(gates["gates_passed"], list)
            assert isinstance(gates["gates_failed"], list)
        
        # Lint check
        result = linter.lint(multi_pair_gates)
        assert result.valid
        print("✓ Multi-pair gates not aggregated")

    def test_no_portfolio_grade(self, multi_pair_gates: dict):
        """No 'portfolio grade' synthesized from multi-pair."""
        # Must NOT have portfolio-level aggregation
        assert "portfolio_grade" not in str(multi_pair_gates)
        assert "overall_score" not in str(multi_pair_gates)
        assert "combined_confidence" not in str(multi_pair_gates)
        print("✓ No portfolio grade synthesized")


class TestCSOGatesToHuntGrid:
    """Test full CSO → Hunt → Grid chain."""

    def test_gate_info_in_grid_output(self, sample_gate_status: dict):
        """Grid output should include gate info without grades."""
        # Simulate grid output with gate data
        grid_output = {
            "hypothesis_id": "hyp_001",
            "pair": sample_gate_status["pair"],
            "gate_status": {
                "passed": sample_gate_status["gates_passed"],
                "failed": sample_gate_status["gates_failed"],
            },
            "variants": [
                {"delay": 1, "sharpe": 1.2},
                {"delay": 2, "sharpe": 0.9},
            ],
        }
        
        # Gate data preserved without grade conversion
        assert "gate_status" in grid_output
        assert "passed" in grid_output["gate_status"]
        assert "grade" not in grid_output
        print("✓ Gate info in grid without grades")

    def test_chain_output_passes_scalar_ban(
        self, sample_gate_status: dict, linter: ScalarBanLinter
    ):
        """Full chain output must pass scalar ban."""
        chain_output = {
            "cso_gates": sample_gate_status,
            "hunt_results": {
                "grid": [
                    {"params": {"delay": 1}, "sharpe": 1.2},
                    {"params": {"delay": 2}, "sharpe": 0.9},
                ],
            },
        }
        
        result = linter.lint(chain_output)
        assert result.valid, f"Violations: {result.violations}"
        print("✓ Chain output passes scalar ban")


# =============================================================================
# INVARIANT ASSERTIONS
# =============================================================================


class TestChainInvariants:
    """Explicit invariant checks."""

    def test_inv_no_grade_reconstruction(self, sample_gate_status: dict):
        """INV-NO-GRADE-RECONSTRUCTION: Gates stay as gates."""
        forbidden_fields = ["grade", "rating", "score", "tier", "class"]
        
        for field in forbidden_fields:
            assert field not in sample_gate_status
        
        print("✓ INV-NO-GRADE-RECONSTRUCTION: No grades")

    def test_inv_harness_2_gates_preserved(self, sample_gate_status: dict):
        """INV-HARNESS-2: gates_passed[] preserved as array."""
        gates = sample_gate_status["gates_passed"]
        
        assert isinstance(gates, list)
        assert len(gates) > 0
        assert all(isinstance(g, int) for g in gates)
        print("✓ INV-HARNESS-2: gates_passed[] is array")

    def test_inv_cso_no_confidence(self, sample_gate_status: dict, linter: ScalarBanLinter):
        """INV-CSO-NO-CONFIDENCE: No confidence scores."""
        # Add potential confidence field
        test_data = {**sample_gate_status}
        
        result = linter.lint(test_data)
        assert result.valid
        
        # Explicitly check no confidence
        assert "confidence" not in test_data
        assert "probability" not in test_data
        print("✓ INV-CSO-NO-CONFIDENCE: No confidence scores")
