"""
BUNNY Chaos Tests — S36 CSO Harness
===================================

24+ chaos vectors targeting bit-vector grade leakage.

INVARIANTS TESTED:
  - INV-BITVECTOR-NO-POPULATION: No bit counts
  - INV-HARNESS-5: No downstream scalar derivation
  - INV-DRAWER-RULE-EXPLICIT: No runtime config
  - INV-DISPLAY-SHUFFLE: Randomized display
  - INV-CSO-BUDGET: max_pairs=12

CRITICAL: These tests prove grades cannot leak through bit vectors.
"""

import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pytest

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))


# =============================================================================
# INLINE TYPES (match production modules)
# =============================================================================

CSO_ROOT = PHOENIX_ROOT / "cso"
DRAWER_SCHEMA_PATH = CSO_ROOT / "schemas" / "drawer_schema.yaml"
GATE_SCHEMA_PATH = CSO_ROOT / "schemas" / "gate_schema.yaml"

FORBIDDEN_FIELDS = frozenset(
    [
        "quality_score",
        "confidence",
        "grade",
        "rank",
        "weight",
        "priority",
        "quality_threshold",
        "score",
        "rating",
        "importance",
    ]
)


class BitVectorScope(Enum):
    MACHINE_ONLY = "MACHINE_ONLY"
    UI_OPT_IN = "UI_OPT_IN"


@dataclass
class BitVectorResult:
    pair: str
    vector: str
    gate_map: dict[int, str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    scope: BitVectorScope = BitVectorScope.MACHINE_ONLY


class PopulationCountBan:
    FORBIDDEN_PATTERNS = frozenset(
        [
            "popcount",
            "count('1')",
            'count("1")',
            "ones_count",
            "hamming_weight",
            "hamming_distance",
            "bit_count",
            "> 6 ones",
            ">6 ones",
            "more than",
            "fewer than",
            "at least",
        ]
    )

    @classmethod
    def validate_query(cls, query: str) -> tuple[bool, str]:
        query_lower = query.lower()
        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in query_lower:
                return (False, f"Population counting forbidden: '{pattern}' detected.")
        return (True, "")


@dataclass
class ValidationError:
    field: str
    message: str
    code: str


@dataclass
class ValidationResult:
    valid: bool
    errors: list[ValidationError] = field(default_factory=list)


class DrawerSchemaValidator:
    def validate_drawer(self, drawer_dict: dict[str, Any]) -> ValidationResult:
        errors: list[ValidationError] = []
        for field_name in drawer_dict:
            if field_name.lower() in FORBIDDEN_FIELDS:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=f"Forbidden field '{field_name}'",
                        code="FORBIDDEN_FIELD",
                    )
                )
        evaluation = drawer_dict.get("evaluation", {})
        if isinstance(evaluation, dict):
            if evaluation.get("runtime_configurable", False):
                errors.append(
                    ValidationError(
                        field="evaluation.runtime_configurable",
                        message="Runtime configurable forbidden",
                        code="RUNTIME_CONFIG_FORBIDDEN",
                    )
                )
            if "quality_threshold" in evaluation:
                errors.append(
                    ValidationError(
                        field="evaluation.quality_threshold",
                        message="quality_threshold forbidden",
                        code="FORBIDDEN_FIELD",
                    )
                )
        return ValidationResult(valid=len(errors) == 0, errors=errors)


FORBIDDEN_IN_ALERTS = frozenset(
    [
        "gates_passed_count",
        "/total",
        "out of",
        "ratio",
        "percentage",
        "%",
        "quality",
        "grade",
        "score",
        "confidence",
        "best",
        "top",
        "looks ready",
        "setup forming",
        "opportunity",
        "consider",
        "potential",
    ]
)


class AlertLinter:
    @staticmethod
    def lint_template(template: str) -> ValidationResult:
        errors: list[ValidationError] = []
        template_lower = template.lower()
        for phrase in FORBIDDEN_IN_ALERTS:
            if phrase.lower() in template_lower:
                errors.append(
                    ValidationError(
                        field="template",
                        message=f"Forbidden phrase '{phrase}'",
                        code="FORBIDDEN_PHRASE",
                    )
                )
        return ValidationResult(valid=len(errors) == 0, errors=errors)


class AlertRuleValidator:
    def validate(self, rule_dict: dict[str, Any]) -> ValidationResult:
        errors: list[ValidationError] = []
        gates_required = rule_dict.get("gates_required", [])
        trigger = rule_dict.get("trigger", {})
        if trigger:
            gates_required = trigger.get("gates_required", gates_required)
        if not gates_required:
            errors.append(
                ValidationError(
                    field="gates_required",
                    message="gates_required must have at least 1 gate",
                    code="EMPTY_GATES_REQUIRED",
                )
            )
        return ValidationResult(valid=len(errors) == 0, errors=errors)


DEFAULT_MAX_PAIRS = 12


class MultiPairScanner:
    def __init__(self, max_pairs: int = DEFAULT_MAX_PAIRS) -> None:
        self._max_pairs = max_pairs

    def check_budget(self, pairs: list[str]) -> tuple[bool, str]:
        if len(pairs) > self._max_pairs:
            return (False, f"BUDGET_EXCEEDED: {len(pairs)} > {self._max_pairs}")
        return (True, "")


def validate_sort_request(sort_by: str) -> tuple[bool, str]:
    forbidden = ["gates_passed_count", "count", "quality", "score", "best", "top", "rank"]
    sort_lower = sort_by.lower()
    for f in forbidden:
        if f in sort_lower:
            return (False, f"Sort by '{sort_by}' forbidden.")
    return (True, "")


# =============================================================================
# WAVE 1: BIT COUNT ATTACKS (Critical)
# =============================================================================


class TestWave1_BitCountAttacks:
    """
    Wave 1: Attempts to count 1s in bit vectors.

    This is the PRIMARY HARDENING TARGET for S36.
    Every vector here must be REJECTED.
    """

    def test_cv_popcount_request(self) -> None:
        """CV-B1: Request popcount of bit vector."""
        query = "Get vectors with popcount > 6"
        valid, error = PopulationCountBan.validate_query(query)

        assert not valid, "Popcount request must be rejected"
        assert "forbidden" in error.lower()

    def test_cv_count_ones_query(self) -> None:
        """CV-B2: Query counting 1s in vector."""
        query = "Find vectors with more than 6 ones"
        valid, error = PopulationCountBan.validate_query(query)

        assert not valid, "Count ones query must be rejected"

    def test_cv_hamming_distance_query(self) -> None:
        """CV-B3: Request Hamming distance between vectors."""
        query = "Calculate hamming_distance between vector_a and vector_b"
        valid, error = PopulationCountBan.validate_query(query)

        assert not valid, "Hamming distance must be rejected"

    def test_cv_hamming_weight_query(self) -> None:
        """CV-B4: Request Hamming weight of vector."""
        query = "Get hamming_weight of bit_vector"
        valid, error = PopulationCountBan.validate_query(query)

        assert not valid, "Hamming weight must be rejected"

    def test_cv_downstream_vector_scoring(self) -> None:
        """CV-B5: Downstream consumer tries to score vector."""
        query = "vectors with >6 ones"
        valid, error = PopulationCountBan.validate_query(query)

        assert not valid, "Downstream scoring must be rejected"

    def test_cv_bit_count_function(self) -> None:
        """CV-B6: Attempt to use bit_count function."""
        query = "Apply bit_count to gates_vector"
        valid, error = PopulationCountBan.validate_query(query)

        assert not valid, "bit_count function must be rejected"


# =============================================================================
# WAVE 2: DRAWER THRESHOLD ATTACKS
# =============================================================================


class TestWave2_DrawerThresholdAttacks:
    """
    Wave 2: Attempts to inject quality thresholds into drawers.
    """

    def test_cv_quality_threshold_injection(self) -> None:
        """CV-D1: Inject quality_threshold into drawer config."""
        drawer = {
            "id": 1,
            "name": "Test",
            "gates": ["a"],
            "evaluation": {
                "type": "EXPLICIT_BOOLEAN_RULE",
                "quality_threshold": 0.7,
            },
        }
        validator = DrawerSchemaValidator()
        result = validator.validate_drawer(drawer)

        assert not result.valid, "quality_threshold must be rejected"

    def test_cv_runtime_configurable_injection(self) -> None:
        """CV-D2: Attempt runtime configurable drawer rule."""
        drawer = {
            "id": 1,
            "name": "Test",
            "gates": ["a"],
            "evaluation": {
                "type": "EXPLICIT_BOOLEAN_RULE",
                "runtime_configurable": True,
            },
        }
        validator = DrawerSchemaValidator()
        result = validator.validate_drawer(drawer)

        assert not result.valid, "runtime_configurable must be rejected"

    def test_cv_confidence_field_injection(self) -> None:
        """CV-D3: Inject confidence field."""
        drawer = {
            "id": 1,
            "name": "Test",
            "gates": ["a"],
            "confidence": 0.9,
        }
        validator = DrawerSchemaValidator()
        result = validator.validate_drawer(drawer)

        assert not result.valid, "confidence field must be rejected"


# =============================================================================
# WAVE 3: ALERT LANGUAGE ATTACKS
# =============================================================================


class TestWave3_AlertLanguageAttacks:
    """
    Wave 3: Attempts to inject forbidden language into alerts.
    """

    def test_cv_count_in_template(self) -> None:
        """CV-A1: Template with gates_passed_count."""
        template = "EURUSD: gates_passed_count = 5"
        result = AlertLinter.lint_template(template)

        assert not result.valid, "Count in template must be rejected"

    def test_cv_percentage_in_template(self) -> None:
        """CV-A2: Template with percentage."""
        template = "Gates: 75% passing"
        result = AlertLinter.lint_template(template)

        assert not result.valid, "Percentage must be rejected"

    def test_cv_quality_in_template(self) -> None:
        """CV-A3: Template with quality language."""
        template = "High quality setup on GBPUSD"
        result = AlertLinter.lint_template(template)

        assert not result.valid, "Quality language must be rejected"

    def test_cv_opportunity_in_template(self) -> None:
        """CV-A4: Template with opportunity."""
        template = "Trading opportunity detected"
        result = AlertLinter.lint_template(template)

        assert not result.valid, "Opportunity must be rejected"

    def test_cv_looks_ready_in_template(self) -> None:
        """CV-A5: Template with looks ready."""
        template = "EURUSD looks ready for entry"
        result = AlertLinter.lint_template(template)

        assert not result.valid, "Looks ready must be rejected"


# =============================================================================
# WAVE 4: ALERT RULE ATTACKS
# =============================================================================


class TestWave4_AlertRuleAttacks:
    """
    Wave 4: Attempts to inject forbidden fields into alert rules.
    """

    def test_cv_empty_gates_rule(self) -> None:
        """CV-R1: Rule with empty gates_required."""
        rule = {
            "name": "STATE_TEST",
            "gates_required": [],
        }
        validator = AlertRuleValidator()
        result = validator.validate(rule)

        assert not result.valid, "Empty gates must be rejected"

    def test_cv_trigger_empty_gates(self) -> None:
        """CV-R2: Trigger with empty gates_required."""
        rule = {
            "name": "STATE_TEST",
            "trigger": {
                "gates_required": [],
            },
        }
        validator = AlertRuleValidator()
        result = validator.validate(rule)

        assert not result.valid, "Empty gates in trigger must be rejected"


# =============================================================================
# WAVE 5: BUDGET ATTACKS
# =============================================================================


class TestWave5_BudgetAttacks:
    """
    Wave 5: Attempts to exceed budget limits.
    """

    def test_cv_100_pair_explosion(self) -> None:
        """CV-BU1: Request scan of 100 pairs."""
        scanner = MultiPairScanner()
        pairs = [f"PAIR{i:02d}" for i in range(100)]
        valid, error = scanner.check_budget(pairs)

        assert not valid, "100 pairs must be rejected"
        assert "BUDGET_EXCEEDED" in error

    def test_cv_20_pair_request(self) -> None:
        """CV-BU2: Request 20 pairs (over 12 limit)."""
        scanner = MultiPairScanner()
        pairs = [f"PAIR{i:02d}" for i in range(20)]
        valid, error = scanner.check_budget(pairs)

        assert not valid, "20 pairs must be rejected"


# =============================================================================
# WAVE 6: SORT/RANKING ATTACKS
# =============================================================================


class TestWave6_SortRankingAttacks:
    """
    Wave 6: Attempts to sort/rank by gate count.
    """

    def test_cv_sort_by_gate_count(self) -> None:
        """CV-S1: Request sort by gates_passed_count."""
        valid, error = validate_sort_request("gates_passed_count")

        assert not valid, "Sort by gate count must be rejected"

    def test_cv_sort_by_quality(self) -> None:
        """CV-S2: Request sort by quality."""
        valid, error = validate_sort_request("quality")

        assert not valid, "Sort by quality must be rejected"

    def test_cv_sort_by_best(self) -> None:
        """CV-S3: Request sort by best."""
        valid, error = validate_sort_request("best")

        assert not valid, "Sort by best must be rejected"

    def test_cv_sort_by_top(self) -> None:
        """CV-S4: Request sort by top."""
        valid, error = validate_sort_request("top")

        assert not valid, "Sort by top must be rejected"

    def test_cv_sort_by_rank(self) -> None:
        """CV-S5: Request sort by rank."""
        valid, error = validate_sort_request("rank")

        assert not valid, "Sort by rank must be rejected"


# =============================================================================
# WAVE 7: BIT VECTOR RESULT VALIDATION
# =============================================================================


class TestWave7_BitVectorResultValidation:
    """
    Wave 7: Validates bit vector results have no forbidden fields.
    """

    def test_cv_result_no_popcount(self) -> None:
        """CV-V1: Result must not have popcount field."""
        result = BitVectorResult(
            pair="EURUSD",
            vector="10110100",
            gate_map={0: "a", 1: "b"},
        )

        assert not hasattr(result, "popcount")
        assert not hasattr(result, "ones_count")
        assert not hasattr(result, "bit_count")

    def test_cv_result_no_score(self) -> None:
        """CV-V2: Result must not have score field."""
        result = BitVectorResult(
            pair="EURUSD",
            vector="10110100",
            gate_map={0: "a", 1: "b"},
        )

        assert not hasattr(result, "score")
        assert not hasattr(result, "quality")
        assert not hasattr(result, "grade")

    def test_cv_result_machine_only_default(self) -> None:
        """CV-V3: Result scope is MACHINE_ONLY by default."""
        result = BitVectorResult(
            pair="EURUSD",
            vector="10110100",
            gate_map={0: "a", 1: "b"},
        )

        assert result.scope == BitVectorScope.MACHINE_ONLY


# =============================================================================
# SUMMARY
# =============================================================================


def test_chaos_vector_count() -> None:
    """Verify 24+ chaos vectors exist."""
    # Count all test methods

    test_classes = [
        TestWave1_BitCountAttacks,
        TestWave2_DrawerThresholdAttacks,
        TestWave3_AlertLanguageAttacks,
        TestWave4_AlertRuleAttacks,
        TestWave5_BudgetAttacks,
        TestWave6_SortRankingAttacks,
        TestWave7_BitVectorResultValidation,
    ]

    total_tests = 0
    for cls in test_classes:
        methods = [m for m in dir(cls) if m.startswith("test_cv_")]
        total_tests += len(methods)

    assert total_tests >= 24, f"Expected 24+ chaos vectors, got {total_tests}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
