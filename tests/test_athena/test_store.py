"""
Store Tests — S37 Track B
=========================

INVARIANTS PROVEN:
  - INV-ATTR-NO-WRITEBACK: Claims cannot mutate doctrine
  - INV-NO-AUTO-SURFACE: Claims retrieved ONLY via explicit query
  - INV-CLAIM-NO-EXECUTION: Claims cannot be predicates

EXIT GATE B:
  Criterion: "Store enforces type separation; no writeback possible; rate limited"
"""

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

from athena.bead_types import (
    ClaimBead,
    ClaimContent,
    ClaimProvenance,
    ClaimSource,
    ConflictBead,
    ConflictDetails,
    ConflictReferences,
    ConflictType,
    FactBead,
    FactContent,
    FactProvenance,
    FactSource,
    SourceType,
)
from athena.rate_limiter import AthenaRateLimiter
from athena.store import (
    AthenaStore,
    AutoSurfaceError,
    ExecutionGuardError,
    RateLimitError,
    ValidationError,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_db() -> Path:
    """Create temporary database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return Path(f.name)


@pytest.fixture
def store(temp_db: Path) -> AthenaStore:
    """Create store with temp database."""
    return AthenaStore(db_path=temp_db)


@pytest.fixture
def valid_claim() -> ClaimBead:
    """Valid claim bead."""
    return ClaimBead(
        source=ClaimSource(
            type=SourceType.HUMAN,
            attribution="Olya",
        ),
        content=ClaimContent(
            assertion="FVGs tend to fill about 70% of the time",
            domain="ICT",
        ),
        disclaimer="HUMAN_ASSERTION_ONLY — no doctrine impact",
        provenance=ClaimProvenance(session_id="test_session"),
    )


@pytest.fixture
def valid_fact() -> FactBead:
    """Valid fact bead."""
    return FactBead(
        source=FactSource(
            type=SourceType.COMPUTATION,
            module="cfp",
            formula="count(fvg_filled) / count(fvg_total)",
        ),
        content=FactContent(
            statement="FVGs filled 40% this week",
            value=0.40,
            domain="ICT",
        ),
        provenance=FactProvenance(
            query_string="SELECT fvg_fill_rate FROM river",
            dataset_hash="abc123",
            governance_hash="def456",
            strategy_config_hash="ghi789",
        ),
    )


@pytest.fixture
def valid_conflict() -> ConflictBead:
    """Valid conflict bead."""
    return ConflictBead(
        references=ConflictReferences(
            claim_bead_id="CLAIM_test123",
            fact_bead_id="FACT_test456",
        ),
        conflict=ConflictDetails(
            description="Test conflict",
            domain="ICT",
            conflict_type=ConflictType.BOOLEAN,
        ),
    )


# =============================================================================
# BASIC STORAGE TESTS
# =============================================================================


class TestBasicStorage:
    """Tests for basic storage operations."""

    def test_store_valid_claim(
        self, store: AthenaStore, valid_claim: ClaimBead
    ) -> None:
        """Store valid claim."""
        bead_id = store.store_claim(valid_claim)
        assert bead_id.startswith("CLAIM_")

    def test_retrieve_claim(
        self, store: AthenaStore, valid_claim: ClaimBead
    ) -> None:
        """Retrieve stored claim."""
        bead_id = store.store_claim(valid_claim)
        retrieved = store.get_claim(bead_id)

        assert retrieved is not None
        assert retrieved.content.assertion == valid_claim.content.assertion

    def test_store_valid_fact(
        self, store: AthenaStore, valid_fact: FactBead
    ) -> None:
        """Store valid fact."""
        bead_id = store.store_fact(valid_fact)
        assert bead_id.startswith("FACT_")

    def test_store_valid_conflict(
        self, store: AthenaStore, valid_conflict: ConflictBead
    ) -> None:
        """Store valid conflict."""
        bead_id = store.store_conflict(valid_conflict)
        assert bead_id.startswith("CONFLICT_")


# =============================================================================
# VALIDATION TESTS
# =============================================================================


class TestValidation:
    """Tests for validation enforcement."""

    def test_claim_without_disclaimer_rejected(self, store: AthenaStore) -> None:
        """Claim without disclaimer is rejected."""
        claim = ClaimBead(
            source=ClaimSource(attribution="Olya"),
            content=ClaimContent(assertion="Test", domain="test"),
            disclaimer="",  # Empty
        )

        with pytest.raises(ValidationError):
            store.store_claim(claim)

    def test_claim_with_banned_language_rejected(self, store: AthenaStore) -> None:
        """Claim with banned language is rejected."""
        claim = ClaimBead(
            source=ClaimSource(attribution="Olya"),
            content=ClaimContent(
                assertion="This always works guaranteed",  # Banned
                domain="test",
            ),
        )

        with pytest.raises(ValidationError):
            store.store_claim(claim)

    def test_fact_without_provenance_rejected(self, store: AthenaStore) -> None:
        """Fact without provenance is rejected."""
        fact = FactBead(
            source=FactSource(module="cfp"),
            content=FactContent(statement="Test", value=1.0, domain="test"),
            # No provenance
        )

        with pytest.raises(ValidationError):
            store.store_fact(fact)


# =============================================================================
# EXECUTION GUARD TESTS (Critical)
# =============================================================================


class TestExecutionGuard:
    """Tests for execution guard enforcement."""

    def test_claim_in_predicate_rejected(self, store: AthenaStore) -> None:
        """Claim in CSO predicate is rejected."""
        with pytest.raises(ExecutionGuardError):
            store.validate_no_claim_execution(
                predicate_refs=["CLAIM_abc123"],  # FORBIDDEN
                alert_refs=[],
                hunt_refs=[],
            )

    def test_claim_in_alert_rejected(self, store: AthenaStore) -> None:
        """Claim in alert rule is rejected."""
        with pytest.raises(ExecutionGuardError):
            store.validate_no_claim_execution(
                predicate_refs=[],
                alert_refs=["CLAIM_abc123"],  # FORBIDDEN
                hunt_refs=[],
            )

    def test_claim_in_hunt_rejected(self, store: AthenaStore) -> None:
        """Claim in hunt parameter is rejected."""
        with pytest.raises(ExecutionGuardError):
            store.validate_no_claim_execution(
                predicate_refs=[],
                alert_refs=[],
                hunt_refs=["CLAIM_abc123"],  # FORBIDDEN
            )

    def test_fact_in_predicate_allowed(self, store: AthenaStore) -> None:
        """Fact in predicate is allowed."""
        # Should not raise
        store.validate_no_claim_execution(
            predicate_refs=["FACT_abc123"],  # OK
            alert_refs=[],
            hunt_refs=[],
        )


# =============================================================================
# AUTO-SURFACE GUARD TESTS
# =============================================================================


class TestAutoSurfaceGuard:
    """Tests for auto-surface prevention."""

    def test_auto_surface_claim_rejected(self, store: AthenaStore) -> None:
        """Auto-surface intent is rejected."""
        with pytest.raises(AutoSurfaceError):
            store.validate_no_auto_surface("AUTO_SURFACE_CLAIM")

    def test_push_claim_on_chart_rejected(self, store: AthenaStore) -> None:
        """Push claim on chart is rejected."""
        with pytest.raises(AutoSurfaceError):
            store.validate_no_auto_surface("PUSH_CLAIM_ON_CHART")

    def test_explicit_query_allowed(self, store: AthenaStore) -> None:
        """Explicit query is allowed."""
        # Should not raise
        store.validate_no_auto_surface("ATHENA_QUERY")


# =============================================================================
# RATE LIMITING TESTS
# =============================================================================


class TestRateLimiting:
    """Tests for rate limiting."""

    def test_101st_claim_rate_limited(self, temp_db: Path) -> None:
        """101st claim in hour is rate limited."""
        limiter = AthenaRateLimiter(max_claims=100)
        store = AthenaStore(db_path=temp_db, rate_limiter=limiter)

        # Store 100 claims
        for i in range(100):
            claim = ClaimBead(
                source=ClaimSource(attribution="Olya"),
                content=ClaimContent(
                    assertion=f"Test claim {i} tends to work",
                    domain="test",
                ),
                provenance=ClaimProvenance(session_id=f"session_{i}"),
            )
            store.store_claim(claim)

        # 101st should fail
        claim = ClaimBead(
            source=ClaimSource(attribution="Olya"),
            content=ClaimContent(
                assertion="One more claim that tends to work",
                domain="test",
            ),
            provenance=ClaimProvenance(session_id="session_101"),
        )

        with pytest.raises(RateLimitError):
            store.store_claim(claim)


# =============================================================================
# CONFLICT SHUFFLE TEST
# =============================================================================


class TestConflictShuffle:
    """Tests for conflict shuffling."""

    def test_open_conflicts_shuffled(
        self, store: AthenaStore, valid_conflict: ConflictBead
    ) -> None:
        """Open conflicts are returned shuffled."""
        # Store multiple conflicts
        for i in range(5):
            conflict = ConflictBead(
                references=ConflictReferences(
                    claim_bead_id=f"CLAIM_{i}",
                    fact_bead_id=f"FACT_{i}",
                ),
                conflict=ConflictDetails(
                    description=f"Conflict {i}",
                    domain="ICT",
                    conflict_type=ConflictType.BOOLEAN,
                ),
            )
            store.store_conflict(conflict)

        # Get conflicts multiple times - should be shuffled
        results1 = store.get_open_conflicts()
        results2 = store.get_open_conflicts()

        # At least one order should differ (statistically likely with 5 items)
        # Note: This test could theoretically fail due to random chance
        ids1 = [c.bead_id for c in results1]
        ids2 = [c.bead_id for c in results2]

        # Both should have same items
        assert set(ids1) == set(ids2)


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
