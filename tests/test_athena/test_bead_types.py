"""
Bead Types Tests — S37 Track A
==============================

INVARIANTS PROVEN:
  - INV-CLAIM-NO-EXECUTION: Claims cannot be predicates
  - INV-ATTR-SILENCE: Conflicts have no resolution authority
  - INV-ATTR-PROVENANCE: Facts require full provenance

EXIT GATE A:
  Criterion: "Three bead types validated; forbidden fields rejected; disclaimer mandatory"
  Proof: "Schema rejects any bead with forbidden fields"
"""

import sys
from pathlib import Path

import pytest

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

from athena.bead_types import (
    AthenaBeadType,
    BeadValidator,
    ClaimBead,
    ClaimContent,
    ClaimProvenance,
    ClaimSource,
    ClaimStatus,
    ConflictBead,
    ConflictDetails,
    ConflictReferences,
    ConflictStatus,
    ConflictType,
    FactBead,
    FactContent,
    FactProvenance,
    FactSource,
    SourceType,
    StatisticalParameters,
    StatisticalType,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def validator() -> BeadValidator:
    """Create validator instance."""
    return BeadValidator()


@pytest.fixture
def valid_claim() -> ClaimBead:
    """Valid claim bead."""
    return ClaimBead(
        source=ClaimSource(
            type=SourceType.HUMAN,
            attribution="Olya",
            context="Morning session",
        ),
        content=ClaimContent(
            assertion="FVGs tend to fill about 70% of the time",
            domain="ICT",
        ),
        disclaimer="HUMAN_ASSERTION_ONLY — no doctrine impact",
        provenance=ClaimProvenance(
            session_id="session_123",
        ),
    )


@pytest.fixture
def valid_fact() -> FactBead:
    """Valid fact bead with full provenance."""
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
            query_string="SELECT fvg_fill_rate FROM river WHERE week=current",
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
            claim_bead_id="CLAIM_abc123",
            fact_bead_id="FACT_def456",
        ),
        conflict=ConflictDetails(
            description="CLAIM asserts 70%, FACT shows 40%",
            domain="ICT",
            conflict_type=ConflictType.STATISTICAL,
        ),
    )


# =============================================================================
# CLAIM VALIDATION TESTS
# =============================================================================


class TestClaimValidation:
    """Tests for claim bead validation."""

    def test_valid_claim_passes(
        self,
        validator: BeadValidator,
        valid_claim: ClaimBead,
    ) -> None:
        """Valid claim passes validation."""
        result = validator.validate_claim(valid_claim)
        assert result.valid

    def test_claim_without_disclaimer_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Claim without disclaimer is rejected."""
        claim = ClaimBead(
            source=ClaimSource(attribution="Olya"),
            content=ClaimContent(assertion="Test"),
            disclaimer="",  # Empty disclaimer
        )
        result = validator.validate_claim(claim)

        assert not result.valid
        assert any(e.code == "MISSING_DISCLAIMER" for e in result.errors)

    def test_claim_without_attribution_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Claim without attribution is rejected."""
        claim = ClaimBead(
            source=ClaimSource(attribution=""),  # No attribution
            content=ClaimContent(assertion="Test"),
        )
        result = validator.validate_claim(claim)

        assert not result.valid
        assert any(e.code == "MISSING_ATTRIBUTION" for e in result.errors)

    def test_claim_with_verified_true_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Claim with verified=true is rejected."""
        claim = ClaimBead(
            source=ClaimSource(attribution="Olya"),
            content=ClaimContent(assertion="Test"),
            status=ClaimStatus(verified=True),  # FORBIDDEN
        )
        result = validator.validate_claim(claim)

        assert not result.valid
        assert any(e.code == "VERIFIED_FORBIDDEN" for e in result.errors)

    def test_claim_default_verified_is_false(self) -> None:
        """Claim default verified is False."""
        claim = ClaimBead()
        assert claim.status.verified is False

    def test_claim_bead_type_is_claim(self) -> None:
        """Claim bead type is CLAIM."""
        claim = ClaimBead()
        assert claim.bead_type == AthenaBeadType.CLAIM

    def test_claim_source_type_is_human(self) -> None:
        """Claim source type is HUMAN."""
        claim = ClaimBead()
        assert claim.source.type == SourceType.HUMAN

    def test_claim_with_statistical_parameters(
        self,
        validator: BeadValidator,
    ) -> None:
        """Claim with statistical parameters is valid."""
        claim = ClaimBead(
            source=ClaimSource(attribution="Olya"),
            content=ClaimContent(
                assertion="FVGs work about 70% of the time",
                domain="ICT",
            ),
            statistical_parameters=StatisticalParameters(
                type=StatisticalType.PERCENTAGE,
                value=0.70,
                bounds_lower=0.60,
                bounds_upper=0.80,
            ),
        )
        result = validator.validate_claim(claim)
        assert result.valid


# =============================================================================
# FACT VALIDATION TESTS
# =============================================================================


class TestFactValidation:
    """Tests for fact bead validation."""

    def test_valid_fact_passes(
        self,
        validator: BeadValidator,
        valid_fact: FactBead,
    ) -> None:
        """Valid fact passes validation."""
        result = validator.validate_fact(valid_fact)
        assert result.valid

    def test_fact_without_provenance_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Fact without provenance is rejected."""
        fact = FactBead(
            source=FactSource(module="cfp"),
            content=FactContent(statement="Test", value=1.0, domain="test"),
            provenance=FactProvenance(),  # Empty provenance
        )
        result = validator.validate_fact(fact)

        assert not result.valid
        assert any(e.code == "INCOMPLETE_PROVENANCE" for e in result.errors)

    def test_fact_without_module_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Fact without source module is rejected."""
        fact = FactBead(
            source=FactSource(module=""),  # No module
            content=FactContent(statement="Test", value=1.0, domain="test"),
            provenance=FactProvenance(
                query_string="q",
                dataset_hash="a",
                governance_hash="b",
                strategy_config_hash="c",
            ),
        )
        result = validator.validate_fact(fact)

        assert not result.valid
        assert any(e.code == "MISSING_MODULE" for e in result.errors)

    def test_fact_bead_type_is_fact(self) -> None:
        """Fact bead type is FACT."""
        fact = FactBead()
        assert fact.bead_type == AthenaBeadType.FACT

    def test_fact_source_type_is_computation(self) -> None:
        """Fact source type is COMPUTATION."""
        fact = FactBead()
        assert fact.source.type == SourceType.COMPUTATION


# =============================================================================
# CONFLICT VALIDATION TESTS
# =============================================================================


class TestConflictValidation:
    """Tests for conflict bead validation."""

    def test_valid_conflict_passes(
        self,
        validator: BeadValidator,
        valid_conflict: ConflictBead,
    ) -> None:
        """Valid conflict passes validation."""
        result = validator.validate_conflict(valid_conflict)
        assert result.valid

    def test_conflict_without_claim_ref_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Conflict without claim reference is rejected."""
        conflict = ConflictBead(
            references=ConflictReferences(
                claim_bead_id="",  # Missing
                fact_bead_id="FACT_123",
            ),
        )
        result = validator.validate_conflict(conflict)

        assert not result.valid
        assert any(e.code == "MISSING_CLAIM_REF" for e in result.errors)

    def test_conflict_without_fact_ref_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Conflict without fact reference is rejected."""
        conflict = ConflictBead(
            references=ConflictReferences(
                claim_bead_id="CLAIM_123",
                fact_bead_id="",  # Missing
            ),
        )
        result = validator.validate_conflict(conflict)

        assert not result.valid
        assert any(e.code == "MISSING_FACT_REF" for e in result.errors)

    def test_conflict_bead_type_is_conflict(self) -> None:
        """Conflict bead type is CONFLICT."""
        conflict = ConflictBead()
        assert conflict.bead_type == AthenaBeadType.CONFLICT

    def test_conflict_default_status_is_open(self) -> None:
        """Conflict default status is OPEN."""
        conflict = ConflictBead()
        assert conflict.resolution.status == ConflictStatus.OPEN


# =============================================================================
# FORBIDDEN FIELDS TESTS
# =============================================================================


class TestForbiddenFields:
    """Tests for forbidden field rejection."""

    def test_dict_with_severity_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Dict with severity field is rejected."""
        bead_dict = {
            "bead_id": "test",
            "severity": "HIGH",  # FORBIDDEN
        }
        result = validator.validate_dict(bead_dict)

        assert not result.valid
        assert any(e.code == "FORBIDDEN_FIELD" for e in result.errors)

    def test_dict_with_importance_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Dict with importance field is rejected."""
        bead_dict = {
            "bead_id": "test",
            "importance": 5,  # FORBIDDEN
        }
        result = validator.validate_dict(bead_dict)

        assert not result.valid

    def test_dict_with_confidence_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Dict with confidence field is rejected."""
        bead_dict = {
            "bead_id": "test",
            "confidence": 0.9,  # FORBIDDEN
        }
        result = validator.validate_dict(bead_dict)

        assert not result.valid

    def test_dict_with_score_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Dict with score field is rejected."""
        bead_dict = {
            "bead_id": "test",
            "score": 85,  # FORBIDDEN
        }
        result = validator.validate_dict(bead_dict)

        assert not result.valid

    def test_nested_forbidden_field_rejected(
        self,
        validator: BeadValidator,
    ) -> None:
        """Nested forbidden field is rejected."""
        bead_dict = {
            "bead_id": "test",
            "content": {
                "quality": "high",  # FORBIDDEN (nested)
            },
        }
        result = validator.validate_dict(bead_dict)

        assert not result.valid


# =============================================================================
# BEAD ID GENERATION TESTS
# =============================================================================


class TestBeadIdGeneration:
    """Tests for automatic bead ID generation."""

    def test_claim_generates_bead_id(self) -> None:
        """Claim generates bead_id if not provided."""
        claim = ClaimBead()
        assert claim.bead_id.startswith("CLAIM_")

    def test_fact_generates_bead_id(self) -> None:
        """Fact generates bead_id if not provided."""
        fact = FactBead()
        assert fact.bead_id.startswith("FACT_")

    def test_conflict_generates_bead_id(self) -> None:
        """Conflict generates bead_id if not provided."""
        conflict = ConflictBead()
        assert conflict.bead_id.startswith("CONFLICT_")


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
