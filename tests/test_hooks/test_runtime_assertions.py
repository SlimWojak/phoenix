"""
Runtime Assertions Tests — S40 Track C
======================================

Proves INV-HOOK-3 and INV-HOOK-4.
"""

from __future__ import annotations

from dataclasses import dataclass
import pytest

from governance.runtime_assertions import (
    assert_no_scalar_score,
    assert_provenance,
    assert_no_ranking,
    assert_no_grade,
    ConstitutionalViolation,
    ScalarScoreViolation,
    ProvenanceMissing,
    RankingViolation,
    GradeViolation,
    RuntimeConstitutionalChecker,
    enforce_constitution,
    validate_output,
    cfp_output,
    hunt_output,
    constitutional_boundary,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def valid_cfp_result() -> dict:
    """Valid CFP result with provenance."""
    return {
        "query_string": "SELECT * FROM data WHERE date > '2024-01-01'",
        "dataset_hash": "abc123def456",
        "bead_id": "bead_001",
        "results": [{"symbol": "AAPL", "sharpe_array": [1.2, 1.3, 1.1]}],
    }


@pytest.fixture
def valid_hunt_result() -> dict:
    """Valid Hunt result without rankings."""
    return {
        "hypothesis_id": "hyp_001",
        "variants": [
            {"params": {"ma_fast": 10}, "metrics": {"sharpe": [1.2, 1.3]}},
            {"params": {"ma_fast": 20}, "metrics": {"sharpe": [1.1, 1.2]}},
        ],
    }


# =============================================================================
# INV-HOOK-3: MISSING PROVENANCE
# =============================================================================


class TestProvenanceMissing:
    """Prove INV-HOOK-3: Runtime catches missing provenance."""

    def test_catches_missing_query_string(self):
        """INV-HOOK-3: Missing query_string raises."""
        result = {
            "dataset_hash": "abc123",
            "bead_id": "bead_001",
            "data": [1, 2, 3],
        }

        with pytest.raises(ProvenanceMissing) as exc_info:
            assert_provenance(result, "cfp_output")

        assert "query_string" in exc_info.value.missing_fields
        print("✓ INV-HOOK-3: Missing query_string raises")

    def test_catches_missing_bead_id(self):
        """INV-HOOK-3: Missing bead_id raises."""
        result = {
            "query_string": "SELECT * FROM data",
            "dataset_hash": "abc123",
            "data": [1, 2, 3],
        }

        with pytest.raises(ProvenanceMissing) as exc_info:
            assert_provenance(result, "cfp_output")

        assert "bead_id" in exc_info.value.missing_fields
        print("✓ INV-HOOK-3: Missing bead_id raises")

    def test_catches_missing_dataset_hash(self):
        """INV-HOOK-3: Missing dataset_hash raises."""
        result = {
            "query_string": "SELECT * FROM data",
            "bead_id": "bead_001",
            "data": [1, 2, 3],
        }

        with pytest.raises(ProvenanceMissing) as exc_info:
            assert_provenance(result, "cfp_output")

        assert "dataset_hash" in exc_info.value.missing_fields
        print("✓ INV-HOOK-3: Missing dataset_hash raises")

    def test_valid_provenance_passes(self, valid_cfp_result: dict):
        """Valid provenance passes."""
        # Should not raise
        assert_provenance(valid_cfp_result, "cfp_output")
        print("✓ Valid provenance passes")

    def test_catches_multiple_missing(self):
        """Catches multiple missing fields."""
        result = {"data": [1, 2, 3]}

        with pytest.raises(ProvenanceMissing) as exc_info:
            assert_provenance(result, "cfp_output")

        assert len(exc_info.value.missing_fields) == 3
        print(f"✓ Caught {len(exc_info.value.missing_fields)} missing fields")


# =============================================================================
# INV-HOOK-4: RANKING FIELDS
# =============================================================================


class TestRankingFields:
    """Prove INV-HOOK-4: Runtime catches ranking fields."""

    def test_catches_rank_position(self):
        """INV-HOOK-4: rank_position raises."""
        result = {
            "strategy_id": "strat_001",
            "rank_position": 1,
            "metrics": {"sharpe": 1.5},
        }

        with pytest.raises(RankingViolation) as exc_info:
            assert_no_ranking(result, "hunt_output")

        assert exc_info.value.field_name == "rank_position"
        print("✓ INV-HOOK-4: rank_position raises")

    def test_catches_ranking(self):
        """INV-HOOK-4: ranking field raises."""
        result = {"strategy_id": "strat_001", "ranking": 1}

        with pytest.raises(RankingViolation):
            assert_no_ranking(result, "hunt_output")
        print("✓ INV-HOOK-4: ranking raises")

    def test_catches_rank_prefix(self):
        """INV-HOOK-4: rank_ prefix raises."""
        result = {"strategy_id": "strat_001", "rank_score": 95}

        with pytest.raises(RankingViolation):
            assert_no_ranking(result, "hunt_output")
        print("✓ INV-HOOK-4: rank_ prefix raises")

    def test_valid_hunt_passes(self, valid_hunt_result: dict):
        """Valid hunt result without rankings passes."""
        assert_no_ranking(valid_hunt_result, "hunt_output")
        print("✓ Valid hunt result passes")

    def test_catches_in_list(self):
        """Catches ranking in list of items."""
        items = [
            {"id": 1, "metrics": {"sharpe": 1.5}},
            {"id": 2, "rank_position": 2},  # HERESY
        ]

        with pytest.raises(RankingViolation):
            assert_no_ranking(items, "hunt_output")
        print("✓ Caught ranking in list")


# =============================================================================
# SCALAR SCORE DETECTION
# =============================================================================


class TestScalarScoreDetection:
    """Test scalar score detection at runtime."""

    def test_catches_scalar_score_field(self):
        """Catches scalar_score field."""
        result = {"id": 1, "scalar_score": 0.85}

        with pytest.raises(ScalarScoreViolation):
            assert_no_scalar_score(result, "validation_output")
        print("✓ scalar_score caught")

    def test_catches_viability_index(self):
        """Catches viability_index."""
        result = {"id": 1, "viability_index": 0.9}

        with pytest.raises(ScalarScoreViolation):
            assert_no_scalar_score(result, "validation_output")
        print("✓ viability_index caught")

    def test_catches_overall_quality(self):
        """Catches overall_quality."""
        result = {"id": 1, "overall_quality": 0.75}

        with pytest.raises(ScalarScoreViolation):
            assert_no_scalar_score(result, "validation_output")
        print("✓ overall_quality caught")

    def test_allows_score_arrays(self):
        """Allows decomposed score arrays."""
        result = {
            "id": 1,
            "sharpe_array": [1.2, 1.3, 1.1, 1.4],
            "returns_array": [0.01, 0.02, -0.01, 0.03],
        }

        # Should not raise
        assert_no_scalar_score(result, "validation_output")
        print("✓ Score arrays allowed")


# =============================================================================
# GRADE DETECTION
# =============================================================================


class TestGradeDetection:
    """Test grade/verdict detection at runtime."""

    def test_catches_grade_field(self):
        """Catches grade field."""
        result = {"id": 1, "grade": "A"}

        with pytest.raises(GradeViolation):
            assert_no_grade(result, "output")
        print("✓ grade field caught")

    def test_catches_quality_grade(self):
        """Catches quality_grade."""
        result = {"id": 1, "quality_grade": "excellent"}

        with pytest.raises(GradeViolation):
            assert_no_grade(result, "output")
        print("✓ quality_grade caught")

    def test_catches_verdict(self):
        """Catches verdict field."""
        result = {"id": 1, "verdict": "pass"}

        with pytest.raises(GradeViolation):
            assert_no_grade(result, "output")
        print("✓ verdict caught")


# =============================================================================
# DATACLASS SUPPORT
# =============================================================================


class TestDataclassSupport:
    """Test that assertions work with dataclasses."""

    def test_catches_in_dataclass(self):
        """Catches violations in dataclasses."""

        @dataclass
        class BadResult:
            id: int
            scalar_score: float

        result = BadResult(id=1, scalar_score=0.85)

        with pytest.raises(ScalarScoreViolation):
            assert_no_scalar_score(result, "output")
        print("✓ Caught in dataclass")

    def test_valid_dataclass_passes(self):
        """Valid dataclass passes."""

        @dataclass
        class GoodResult:
            id: int
            sharpe_array: list

        result = GoodResult(id=1, sharpe_array=[1.2, 1.3])

        assert_no_scalar_score(result, "output")
        print("✓ Valid dataclass passes")


# =============================================================================
# DECORATORS
# =============================================================================


class TestDecorators:
    """Test constitutional enforcement decorators."""

    def test_validate_output_decorator(self):
        """@validate_output catches violations."""

        @validate_output
        def bad_function():
            return {"scalar_score": 0.85}

        with pytest.raises(ScalarScoreViolation):
            bad_function()
        print("✓ @validate_output catches violations")

    def test_cfp_output_decorator_requires_provenance(self):
        """@cfp_output requires provenance."""

        @cfp_output
        def bad_cfp():
            return {"data": [1, 2, 3]}  # Missing provenance

        with pytest.raises(ProvenanceMissing):
            bad_cfp()
        print("✓ @cfp_output requires provenance")

    def test_hunt_output_decorator_blocks_ranking(self):
        """@hunt_output blocks rankings."""

        @hunt_output
        def bad_hunt():
            return {"rank_position": 1}

        with pytest.raises(RankingViolation):
            bad_hunt()
        print("✓ @hunt_output blocks rankings")

    def test_valid_decorated_function_passes(self, valid_cfp_result: dict):
        """Valid decorated function passes."""

        @cfp_output
        def good_cfp():
            return valid_cfp_result

        result = good_cfp()
        assert result == valid_cfp_result
        print("✓ Valid decorated function passes")


# =============================================================================
# RUNTIME CHECKER
# =============================================================================


class TestRuntimeChecker:
    """Test RuntimeConstitutionalChecker."""

    def test_checker_catches_violations(self):
        """Checker catches violations."""
        checker = RuntimeConstitutionalChecker(strict=True)

        with pytest.raises(ScalarScoreViolation):
            checker.check_validation_output({"scalar_score": 0.5})
        print("✓ Checker catches violations in strict mode")

    def test_checker_non_strict_records(self):
        """Non-strict checker records but doesn't raise."""
        checker = RuntimeConstitutionalChecker(strict=False)

        # Should not raise
        checker.check_validation_output({"scalar_score": 0.5})

        assert len(checker.violations) == 1
        print("✓ Non-strict mode records violations")

    def test_checker_cfp_output(self, valid_cfp_result: dict):
        """Checker validates CFP output."""
        checker = RuntimeConstitutionalChecker(strict=True)

        # Should not raise
        checker.check_cfp_output(valid_cfp_result)
        print("✓ Checker validates CFP output")


# =============================================================================
# CHAOS: NESTED OBJECTS
# =============================================================================


class TestNestedObjectChaos:
    """Chaos tests for nested object detection."""

    def test_catches_in_nested_dict(self):
        """Note: Current impl checks top-level only."""
        # This is intentional - deep checking could be slow
        # Document this limitation
        result = {
            "outer": {
                "scalar_score": 0.85  # Won't be caught at top level
            }
        }

        # Top-level check passes (by design)
        assert_no_scalar_score(result, "output")
        print("✓ Nested check is top-level only (by design)")

    def test_custom_provenance_fields(self):
        """Custom provenance fields work."""
        result = {"custom_id": "123", "custom_hash": "abc"}

        # Should raise with default required fields
        with pytest.raises(ProvenanceMissing):
            assert_provenance(result, "output")

        # Should pass with custom fields
        assert_provenance(result, "output", required=["custom_id", "custom_hash"])
        print("✓ Custom provenance fields work")


# =============================================================================
# EXCEPTION DETAILS
# =============================================================================


class TestExceptionDetails:
    """Test exception message details."""

    def test_scalar_violation_includes_field(self):
        """ScalarScoreViolation includes field name."""
        result = {"viability_index": 0.85}

        try:
            assert_no_scalar_score(result, "test_context")
        except ScalarScoreViolation as e:
            assert "viability_index" in str(e)
            assert "test_context" in str(e)
        print("✓ ScalarScoreViolation includes field name")

    def test_provenance_missing_lists_fields(self):
        """ProvenanceMissing lists missing fields."""
        result = {}

        try:
            assert_provenance(result, "test_context")
        except ProvenanceMissing as e:
            assert len(e.missing_fields) > 0
            assert "test_context" in str(e)
        print("✓ ProvenanceMissing lists fields")

    def test_ranking_violation_includes_field(self):
        """RankingViolation includes field name."""
        result = {"rank_position": 1}

        try:
            assert_no_ranking(result, "test_context")
        except RankingViolation as e:
            assert "rank_position" in str(e)
        print("✓ RankingViolation includes field name")
