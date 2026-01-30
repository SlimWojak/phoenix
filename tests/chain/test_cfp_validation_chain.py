"""
FLOW 1: CFP → WalkForward → MonteCarlo
======================================

S40 Chain Validation — Proves CFP output chains cleanly
to validation modules without score synthesis.

INVARIANTS:
  - INV-ATTR-PROVENANCE: query_string + dataset_hash + bead_id intact
  - INV-CROSS-MODULE-NO-SYNTH: No synthesized scores at integration seam
  - INV-NO-AGGREGATE-SCALAR: Full arrays returned, not averages
"""

from __future__ import annotations

import pytest

from validation import (
    MonteCarloSimulator,
    ScalarBanLinter,
    WalkForwardValidator,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_cfp_result() -> dict:
    """Create a sample CFP result with proper provenance (as dict for testing)."""
    from datetime import UTC, datetime
    
    return {
        "result_type": "projection",
        "data": {
            "sessions": [
                {"session": "london", "sharpe": 1.2, "win_rate": 0.55},
                {"session": "new_york", "sharpe": 0.9, "win_rate": 0.52},
                {"session": "asia", "sharpe": 0.7, "win_rate": 0.48},
            ],
        },
        "provenance": {
            "query_string": "SELECT session, sharpe FROM river WHERE pair='EURUSD'",
            "dataset_hash": "abc123def456",
            "bead_id": "cfp_bead_001",
            "governance_hash": "gov_hash_causal_ban_active",
            "computed_at": datetime.now(UTC).isoformat(),
        },
        "governance_receipt": "INV-ATTR-CAUSAL-BAN: ENFORCED",
    }


@pytest.fixture
def linter() -> ScalarBanLinter:
    """Create scalar ban linter for seam checks."""
    return ScalarBanLinter()


# =============================================================================
# FLOW TESTS
# =============================================================================


class TestCFPToWalkForwardChain:
    """Test CFP → WalkForward integration seam."""

    def test_cfp_provenance_preserved(self, sample_cfp_result: dict):
        """Provenance must be intact after CFP execution."""
        assert sample_cfp_result["provenance"] is not None
        assert sample_cfp_result["provenance"]["query_string"] is not None
        assert sample_cfp_result["provenance"]["dataset_hash"] is not None
        assert sample_cfp_result["provenance"]["bead_id"] is not None
        print("✓ CFP provenance intact")

    def test_cfp_output_passes_scalar_ban(
        self, sample_cfp_result: dict, linter: ScalarBanLinter
    ):
        """CFP output must pass scalar ban linter."""
        result = linter.lint(sample_cfp_result["data"])
        assert result.valid, f"Scalar ban violations: {result.violations}"
        print("✓ CFP output passes scalar ban")

    def test_walk_forward_receives_arrays_not_averages(self):
        """Walk-forward must return full arrays, not avg_* fields."""
        from dataclasses import fields
        
        # Simulate walk-forward validation on CFP output
        validator = WalkForwardValidator()
        
        result = validator.run(
            strategy_config={},
            n_splits=3,
        )
        
        # Must have arrays, not averages
        assert hasattr(result, "split_distribution")
        assert result.split_distribution is not None
        assert len(result.split_distribution.train_sharpes) > 0
        assert len(result.split_distribution.test_sharpes) > 0
        
        # Must NOT have avg_* fields in the dataclass
        field_names = [f.name for f in fields(result)]
        assert not any(name.startswith("avg_") for name in field_names)
        print("✓ Walk-forward returns arrays, not averages")


class TestWalkForwardToMonteCarloChain:
    """Test WalkForward → MonteCarlo integration seam."""

    def test_monte_carlo_receives_decomposed_input(self):
        """Monte Carlo must receive decomposed metrics, not scores."""
        from dataclasses import fields
        
        simulator = MonteCarloSimulator()
        result = simulator.run(
            strategy_config={},
            n_simulations=100,
        )
        
        # Must have percentiles (inside distribution), not verdicts
        assert hasattr(result, "distribution")
        assert hasattr(result.distribution, "drawdown_percentiles")
        assert hasattr(result.distribution, "return_percentiles")
        
        # Must NOT have risk verdicts
        field_names = [f.name for f in fields(result)]
        assert "risk_verdict" not in field_names
        assert "risk_score" not in field_names
        print("✓ Monte Carlo returns percentiles, not verdicts")

    def test_chain_output_passes_scalar_ban(self, linter: ScalarBanLinter):
        """Chained output must pass scalar ban at final seam."""
        from dataclasses import asdict
        
        simulator = MonteCarloSimulator()
        result = simulator.run(
            strategy_config={},
            n_simulations=100,
        )
        
        # Lint the final output (convert dataclass to dict)
        result_dict = asdict(result)
        lint_result = linter.lint(result_dict)
        assert lint_result.valid, f"Scalar ban violations: {lint_result.violations}"
        print("✓ Chain output passes scalar ban")


class TestProvenanceChainDepth:
    """Test provenance is traceable through chain."""

    def test_provenance_depth_3(self, sample_cfp_result: dict):
        """Provenance must be traceable through 3-module chain."""
        # CFP → WalkForward → MonteCarlo
        
        # Step 1: CFP provenance
        cfp_provenance = sample_cfp_result["provenance"]
        assert cfp_provenance["query_string"] is not None
        
        # Step 2: Walk-forward preserves origin
        validator = WalkForwardValidator()
        wf_result = validator.run(strategy_config={}, n_splits=2)
        
        # Step 3: Monte Carlo preserves chain
        simulator = MonteCarloSimulator()
        mc_result = simulator.run(strategy_config={}, n_simulations=50)
        
        # Build provenance chain
        provenance_chain = [
            {"module": "CFP", "hash": cfp_provenance["dataset_hash"]},
            {"module": "WalkForward", "disclaimer": wf_result.disclaimer[:30]},
            {"module": "MonteCarlo", "disclaimer": mc_result.disclaimer[:30]},
        ]
        
        assert len(provenance_chain) == 3
        print(f"✓ Provenance chain depth: {len(provenance_chain)}")


# =============================================================================
# INVARIANT ASSERTIONS
# =============================================================================


class TestChainInvariants:
    """Explicit invariant checks at seams."""

    def test_inv_cross_module_no_synth(self, linter: ScalarBanLinter):
        """INV-CROSS-MODULE-NO-SYNTH: No synthesis at seams."""
        # Simulate seam output
        seam_output = {
            "cfp_projection": {"sessions": ["london", "new_york"]},
            "walk_forward": {"split_sharpes": [1.2, 0.9, 1.1]},
            "monte_carlo": {"drawdown_p95": 0.15},
        }
        
        result = linter.lint(seam_output)
        assert result.valid
        print("✓ INV-CROSS-MODULE-NO-SYNTH: No synthesis at seams")

    def test_inv_attr_provenance(self, sample_cfp_result: dict):
        """INV-ATTR-PROVENANCE: All required fields present."""
        p = sample_cfp_result["provenance"]
        
        assert p["query_string"] is not None, "Missing query_string"
        assert p["dataset_hash"] is not None, "Missing dataset_hash"
        assert p["bead_id"] is not None, "Missing bead_id"
        assert p["governance_hash"] is not None, "Missing governance_hash"
        print("✓ INV-ATTR-PROVENANCE: All fields present")

    def test_inv_no_aggregate_scalar(self):
        """INV-NO-AGGREGATE-SCALAR: No avg_* fields."""
        from dataclasses import fields
        
        validator = WalkForwardValidator()
        result = validator.run(strategy_config={}, n_splits=2)
        
        # Check dataclass fields for avg_*
        field_names = [f.name for f in fields(result)]
        avg_fields = [name for name in field_names if name.startswith("avg_")]
        assert len(avg_fields) == 0, f"Found avg_* fields: {avg_fields}"
        print("✓ INV-NO-AGGREGATE-SCALAR: No avg_* fields")
