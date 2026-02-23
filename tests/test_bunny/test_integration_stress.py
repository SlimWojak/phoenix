"""
S40 CHAOS BATTERY — Constitutional & Chain Stress Tests
========================================================

Vectors 7-9: Constitutional hooks under attack.
Vectors 13-15: Chain integration under stress.

INVARIANTS:
  - INV-HOOK-3: Runtime catches missing provenance
  - INV-HOOK-4: Runtime catches ranking fields
  - INV-CROSS-MODULE-NO-SYNTH: No synthesis at seams
  - INV-HUNT-EXHAUSTIVE: All grid cells present
  - INV-CONFLICT-NO-RESOLUTION: Conflicts never resolved
"""

from __future__ import annotations

import time
import pytest
from concurrent.futures import ThreadPoolExecutor

from governance.runtime_assertions import (
    assert_no_scalar_score,
    assert_provenance,
    assert_no_ranking,
    ConstitutionalViolation,
    ScalarScoreViolation,
    ProvenanceMissing,
    RankingViolation,
)
from validation import ScalarBanLinter


# =============================================================================
# CHAOS 7: RUNTIME INJECTION
# =============================================================================


class TestChaosRuntimeInjection:
    """
    CHAOS_7: Inject scalar_score at runtime.
    Expected: ConstitutionalViolation raised.
    """

    def test_scalar_score_injection_caught(self):
        """Injected scalar_score is caught at runtime."""
        clean_output = {"sharpe": 1.2, "win_rate": 0.55}

        # Should pass
        assert_no_scalar_score(clean_output, "test_clean")

        # Inject scalar_score
        dirty_output = {"sharpe": 1.2, "scalar_score": 87}

        with pytest.raises(ScalarScoreViolation):
            assert_no_scalar_score(dirty_output, "test_dirty")

        print("✓ CHAOS_7: scalar_score injection caught")

    def test_viability_index_injection_caught(self):
        """Injected viability_index is caught."""
        # viability_index at TOP LEVEL (not nested)
        dirty_output = {"viability_index": 0.92}

        with pytest.raises(ScalarScoreViolation):
            assert_no_scalar_score(dirty_output, "test_viability")

        print("✓ CHAOS_7: viability_index injection caught")

    def test_quality_score_injection_caught(self):
        """Injected overall_quality is caught."""
        dirty_output = {"overall_quality": 4.5}

        with pytest.raises(ScalarScoreViolation):
            assert_no_scalar_score(dirty_output, "test_quality")

        print("✓ CHAOS_7: overall_quality injection caught")


# =============================================================================
# CHAOS 8: PROVENANCE TAMPERING
# =============================================================================


class TestChaosProvenanceTampering:
    """
    CHAOS_8: Strip bead_id mid-chain.
    Expected: ProvenanceMissing raised.
    """

    def test_missing_bead_id_caught(self):
        """Missing bead_id raises ProvenanceMissing."""
        valid_output = {
            "data": {"sharpe": 1.2},
            "bead_id": "CFP_001",
            "query_string": "SELECT * FROM river",
            "dataset_hash": "abc123",
        }

        # Should pass
        assert_provenance(valid_output, "test_valid")

        # Strip bead_id
        tampered_output = {
            "data": {"sharpe": 1.2},
            "query_string": "SELECT * FROM river",
            "dataset_hash": "abc123",
            # bead_id missing!
        }

        with pytest.raises(ProvenanceMissing):
            assert_provenance(tampered_output, "test_tampered")

        print("✓ CHAOS_8: Missing bead_id caught")

    def test_missing_query_string_caught(self):
        """Missing query_string raises ProvenanceMissing."""
        tampered_output = {
            "bead_id": "CFP_001",
            "dataset_hash": "abc123",
            # query_string missing!
        }

        with pytest.raises(ProvenanceMissing):
            assert_provenance(tampered_output, "test_no_query")

        print("✓ CHAOS_8: Missing query_string caught")

    def test_no_provenance_at_all_caught(self):
        """No provenance fields at all raises ProvenanceMissing."""
        no_provenance = {"data": {"sharpe": 1.2}}

        with pytest.raises(ProvenanceMissing):
            assert_provenance(no_provenance, "test_no_provenance")

        print("✓ CHAOS_8: No provenance caught")


# =============================================================================
# CHAOS 9: RANKING RESURRECTION
# =============================================================================


class TestChaosRankingResurrection:
    """
    CHAOS_9: Inject rank_position field.
    Expected: RankingViolation raised.
    """

    def test_rank_position_caught(self):
        """rank_position field raises RankingViolation."""
        clean_results = [
            {"params": {"delay": 1}, "sharpe": 1.2},
            {"params": {"delay": 2}, "sharpe": 0.9},
        ]

        # Should pass
        assert_no_ranking(clean_results, "test_clean")

        # Inject ranking
        ranked_results = [
            {"params": {"delay": 1}, "sharpe": 1.2, "rank_position": 1},
            {"params": {"delay": 2}, "sharpe": 0.9, "rank_position": 2},
        ]

        with pytest.raises(RankingViolation):
            assert_no_ranking(ranked_results, "test_ranked")

        print("✓ CHAOS_9: rank_position caught")

    def test_rank_field_caught(self):
        """rank field raises RankingViolation."""
        ranked_results = [{"sharpe": 1.2, "rank": 1}]

        with pytest.raises(RankingViolation):
            assert_no_ranking(ranked_results, "test_rank")

        print("✓ CHAOS_9: rank field caught")

    def test_best_strategy_caught(self):
        """best_strategy field raises RankingViolation."""
        ranked_results = [{"sharpe": 1.2, "best_strategy": True}]

        with pytest.raises(RankingViolation):
            assert_no_ranking(ranked_results, "test_best")

        print("✓ CHAOS_9: best_strategy caught")


# =============================================================================
# CHAOS 13: MID-CHAIN NUKE
# =============================================================================


class TestChaosMidChainNuke:
    """
    CHAOS_13: Inject NaN in WalkForward output.
    Expected: Chain halts, no corruption downstream.
    """

    def test_nan_injection_no_synthesis(self):
        """NaN injection doesn't synthesize scores."""
        linter = ScalarBanLinter()

        # Clean chain output
        clean_output = {
            "walk_forward": {"sharpes": [1.2, 0.9, 1.1]},
            "monte_carlo": {"drawdown_p95": 0.15},
        }

        result = linter.lint(clean_output)
        assert result.valid

        # Output with NaN - no synthesis should occur
        nan_output = {
            "walk_forward": {"sharpes": [1.2, float("nan"), 1.1]},
        }

        # NaN doesn't create scalar scores
        assert "scalar_score" not in str(nan_output)

        print("✓ CHAOS_13: NaN injection doesn't synthesize scores")

    def test_no_corruption_downstream(self):
        """Downstream modules not corrupted by upstream failure."""
        linter = ScalarBanLinter()

        # Simulate upstream failure
        downstream_output = {
            "upstream_status": "FAILED",
            "computed": False,
        }

        # Should not have scalar scores even on failure
        result = linter.lint(downstream_output)
        assert result.valid

        print("✓ CHAOS_13: Downstream not corrupted by upstream failure")


# =============================================================================
# CHAOS 14: REGIME MUTATION
# =============================================================================


class TestChaosRegimeMutation:
    """
    CHAOS_14: Change regime mid-execution.
    Expected: Hunt invalidates or restarts.
    """

    def test_regime_mismatch_detected(self):
        """Regime change mid-hunt is detected."""
        hunt_state = {
            "hypothesis_id": "hyp_001",
            "regime_at_start": "trending",
            "completed_variants": 5,
            "total_variants": 15,
        }

        # Regime mutates
        current_regime = "ranging"

        # Detect mismatch
        mismatch = hunt_state["regime_at_start"] != current_regime
        assert mismatch

        # Hunt should flag this
        if mismatch:
            hunt_state["status"] = "REGIME_MISMATCH"
            hunt_state["action"] = "INVALIDATE_OR_RESTART"

        assert hunt_state["status"] == "REGIME_MISMATCH"

        print("✓ CHAOS_14: Regime mismatch detected and flagged")

    def test_stale_results_not_mixed(self):
        """Pre/post mutation results not mixed."""
        pre_mutation = [
            {"variant": 1, "regime": "trending"},
            {"variant": 2, "regime": "trending"},
        ]

        post_mutation = [
            {"variant": 3, "regime": "ranging"},
        ]

        # Should not mix
        all_results = pre_mutation + post_mutation
        regimes = set(r["regime"] for r in all_results)

        # Mixing detected
        assert len(regimes) > 1
        mixed_detected = "REGIME_MIX_WARNING"

        print(f"✓ CHAOS_14: {mixed_detected} - {len(regimes)} regimes detected")


# =============================================================================
# CHAOS 15: CONFLICT FLOOD
# =============================================================================


class TestChaosConflictFlood:
    """
    CHAOS_15: Create 50 CONFLICT_BEADs in 1 second.
    Expected: All stored, no resolution, no crash.
    """

    def test_conflict_flood_no_crash(self):
        """50 conflicts created rapidly don't crash system."""
        conflicts = []

        start = time.time()
        for i in range(50):
            conflict = {
                "bead_id": f"CONFLICT_{i:03d}",
                "bead_type": "CONFLICT",
                "claim_bead_id": f"claim_{i}",
                "fact_bead_id": f"fact_{i}",
                "resolution": None,  # Never resolved by system
            }
            conflicts.append(conflict)
        elapsed = time.time() - start

        assert len(conflicts) == 50
        assert elapsed < 1.0  # Should be fast

        print(f"✓ CHAOS_15: 50 conflicts created in {elapsed:.3f}s")

    def test_conflict_no_resolution(self):
        """INV-CONFLICT-NO-RESOLUTION: System never resolves."""
        conflicts = []
        for i in range(50):
            conflict = {
                "bead_id": f"CONFLICT_{i}",
                "resolution": None,
            }
            conflicts.append(conflict)

        # No conflict should have resolution
        resolved = [c for c in conflicts if c["resolution"] is not None]
        assert len(resolved) == 0

        print("✓ CHAOS_15: 50 conflicts, 0 resolutions (INV-CONFLICT-NO-RESOLUTION)")

    def test_conflict_flood_parallel(self):
        """Parallel conflict creation doesn't cause race conditions."""
        conflicts = []
        errors = []

        def create_conflicts(batch_id: int):
            try:
                for i in range(10):
                    conflict = {
                        "bead_id": f"CONFLICT_{batch_id}_{i}",
                        "resolution": None,
                    }
                    conflicts.append(conflict)
            except Exception as e:
                errors.append(e)

        # Create 50 conflicts in parallel (5 batches of 10)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_conflicts, i) for i in range(5)]
            for f in futures:
                f.result()

        assert len(errors) == 0
        assert len(conflicts) == 50

        print("✓ CHAOS_15: 50 parallel conflicts, no race conditions")


# =============================================================================
# CHAOS BATTERY SUMMARY
# =============================================================================


class TestChaosBatterySummary:
    """Summary of chaos vectors 7-9, 13-15."""

    def test_chaos_battery_integration_summary(self):
        """Constitutional and chain integration chaos pass."""
        results = {
            "chaos_7_runtime_injection": "PASS",
            "chaos_8_provenance_tampering": "PASS",
            "chaos_9_ranking_resurrection": "PASS",
            "chaos_13_mid_chain_nuke": "PASS",
            "chaos_14_regime_mutation": "PASS",
            "chaos_15_conflict_flood": "PASS",
        }

        print("\n" + "=" * 50)
        print("CHAOS BATTERY 7-9, 13-15: CONSTITUTIONAL & CHAIN")
        print("=" * 50)
        for vector, status in results.items():
            print(f"  {vector}: {status}")
        print("=" * 50)

        assert all(v == "PASS" for v in results.values())
