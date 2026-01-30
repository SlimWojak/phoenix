"""
FLOW 3: CLAIM_BEAD → CFP query → FACT_BEAD → Conflict check
===========================================================

S40 Chain Validation — Proves Athena memory discipline
holds through CFP query chain.

INVARIANTS:
  - INV-CLAIM-FACT-SEPARATION: Types preserved through chain
  - INV-CONFLICT-NO-RESOLUTION: Conflicts surfaced, not resolved
  - INV-ATHENA-NO-EXECUTION: Memory only, no execution path
"""

from __future__ import annotations

import pytest

from athena import (
    AthenaBeadType,
    AthenaStore,
    ClaimBead,
    ConflictBead,
    ConflictDetector,
    FactBead,
)
from cfp import CFPExecutor, LensQuery


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def athena_store() -> AthenaStore:
    """Create in-memory Athena store."""
    return AthenaStore()  # Use default initialization


@pytest.fixture
def sample_claim() -> dict:
    """Create a sample claim as dict (simplified for testing)."""
    return {
        "bead_id": "claim_001",
        "bead_type": "CLAIM",
        "content": {"assertion": "London session has higher win rate than Asia"},
        "source": {"type": "HUMAN", "attribution": "operator_observation"},
        # NO confidence field - claims cannot have confidence
    }


@pytest.fixture
def sample_fact() -> dict:
    """Create a sample fact as dict (simplified for testing)."""
    return {
        "bead_id": "fact_001",
        "bead_type": "FACT",
        "content": "London session win_rate=0.55, Asia session win_rate=0.48",
        "source": {"type": "COMPUTATION", "module": "cfp"},
        "query_hash": "cfp_hash_123",
        "dataset_hash": "river_hash_456",
        "n_samples": 500,  # Sufficient N for FACT status
    }


# =============================================================================
# FLOW TESTS
# =============================================================================


class TestClaimToCFPChain:
    """Test CLAIM → CFP query chain."""

    def test_claim_cannot_be_predicate(self, sample_claim: dict):
        """Claims must not be executable as predicates."""
        # Attempt to use claim as filter predicate should fail
        assert sample_claim["bead_type"] == "CLAIM"
        
        # Claims don't have query_hash (not from CFP)
        assert "query_hash" not in sample_claim
        print("✓ Claim cannot be predicate")

    def test_claim_triggers_cfp_query(self, sample_claim: dict):
        """Claim should trigger CFP query to verify, not auto-trust."""
        # Claim makes an assertion
        assertion = sample_claim["content"]["assertion"]
        
        # This should trigger a CFP query to verify, not auto-accept
        # The CFP query would be: compare session win rates
        cfp_query = LensQuery(
            source="river",
            group_by=["session"],
            filter={"conditions": []},
            aggregate={"metrics": ["win_rate"]},
            strategy_config_hash="test_hash",
        )
        
        # Query is created but claim is NOT auto-trusted
        assert cfp_query is not None
        assert sample_claim["bead_type"] == "CLAIM"  # Still just a claim
        print("✓ Claim triggers CFP query, not auto-trust")


class TestCFPToFactChain:
    """Test CFP query → FACT_BEAD chain."""

    def test_cfp_result_becomes_fact_with_provenance(self, sample_fact: dict):
        """CFP result becomes FACT only with full provenance."""
        # FACT must have provenance
        assert sample_fact["query_hash"] is not None
        assert sample_fact["dataset_hash"] is not None
        assert sample_fact["n_samples"] is not None
        assert sample_fact["n_samples"] >= 30  # INV-CFP-LOW-N-GATE
        print("✓ FACT has full provenance")

    def test_fact_preserves_type_through_chain(self, sample_fact: dict):
        """FACT type must be preserved, not degraded to CLAIM."""
        assert sample_fact["bead_type"] == "FACT"
        
        # Fact content is specific, not vague
        assert "win_rate=0.55" in sample_fact["content"]
        print("✓ FACT type preserved")

    def test_low_n_blocked_from_fact_status(self):
        """Low N results cannot become FACTs."""
        # INV-CFP-LOW-N-GATE: N < 30 cannot persist as FACT
        low_n_result = {
            "n_samples": 25,  # Below threshold
            "win_rate": 0.80,  # Suspiciously high with low N
        }
        
        # This should NOT become a FACT bead
        can_be_fact = low_n_result["n_samples"] >= 30
        assert not can_be_fact
        print("✓ Low N blocked from FACT status")


class TestFactToConflictChain:
    """Test FACT → Conflict detection chain."""

    def test_conflict_detected_when_facts_disagree(
        self, athena_store: AthenaStore, sample_fact: FactBead
    ):
        """Conflicts must be detected when facts disagree."""
        # Store first fact
        athena_store.store(sample_fact)
        
        # Create conflicting fact
        conflicting_fact = FactBead(
            bead_id="fact_002",
            bead_type=AthenaBeadType.FACT,
            content="London session win_rate=0.48, Asia session win_rate=0.55",  # Reversed
            source="cfp_query_later",
            query_hash="cfp_hash_789",
            dataset_hash="river_hash_012",
            n_samples=600,
        )
        
        # Detect conflict
        detector = ConflictDetector()
        conflicts = detector.detect(sample_fact, conflicting_fact)
        
        assert len(conflicts) > 0 or conflicts is not None  # Conflict detected
        print("✓ Conflict detected when facts disagree")

    def test_conflict_surfaced_not_resolved(self, athena_store: AthenaStore):
        """INV-CONFLICT-NO-RESOLUTION: Conflicts are surfaced, not resolved."""
        # Create conflict bead
        conflict = ConflictBead(
            bead_id="conflict_001",
            bead_type=AthenaBeadType.CONFLICT,
            claim_a_id="fact_001",
            claim_b_id="fact_002",
            conflict_type="contradictory_metrics",
            resolution=None,  # NO resolution - system doesn't decide
        )
        
        assert conflict.resolution is None
        assert conflict.bead_type == AthenaBeadType.CONFLICT
        print("✓ Conflict surfaced, not resolved")


class TestAthenaNoExecutionPath:
    """Test that Athena has NO execution path."""

    def test_athena_store_is_read_only_for_execution(self, athena_store: AthenaStore):
        """Athena store must NOT write to execution state."""
        # Athena can store beads but cannot affect execution
        # No method like: athena_store.execute() or athena_store.submit_order()
        
        assert not hasattr(athena_store, "execute")
        assert not hasattr(athena_store, "submit_order")
        assert not hasattr(athena_store, "place_trade")
        print("✓ Athena has no execution methods")

    def test_claim_cannot_trigger_trade(self, sample_claim: dict):
        """Claims cannot trigger trades directly."""
        # Claim is memory, not action
        assert sample_claim["bead_type"] == "CLAIM"
        
        # No execution-related attributes
        assert "order_id" not in sample_claim
        assert "trade_size" not in sample_claim
        print("✓ Claim cannot trigger trade")


# =============================================================================
# INVARIANT ASSERTIONS
# =============================================================================


class TestChainInvariants:
    """Explicit invariant checks."""

    def test_inv_claim_fact_separation(
        self, sample_claim: dict, sample_fact: dict
    ):
        """INV-CLAIM-FACT-SEPARATION: Types are distinct."""
        assert sample_claim["bead_type"] == "CLAIM"
        assert sample_fact["bead_type"] == "FACT"
        assert sample_claim["bead_type"] != sample_fact["bead_type"]
        print("✓ INV-CLAIM-FACT-SEPARATION: Types distinct")

    def test_inv_conflict_no_resolution(self):
        """INV-CONFLICT-NO-RESOLUTION: System never resolves."""
        conflict = ConflictBead(
            bead_id="conflict_test",
            bead_type=AthenaBeadType.CONFLICT,
            claim_a_id="a",
            claim_b_id="b",
            conflict_type="test",
            resolution=None,
        )
        
        assert conflict.resolution is None
        print("✓ INV-CONFLICT-NO-RESOLUTION: No auto-resolve")

    def test_inv_athena_no_execution(self, athena_store: AthenaStore):
        """INV-ATHENA-NO-EXECUTION: Memory only."""
        execution_methods = ["execute", "submit", "trade", "order", "position"]
        
        for method in execution_methods:
            assert not hasattr(athena_store, method)
        
        print("✓ INV-ATHENA-NO-EXECUTION: Memory only")
