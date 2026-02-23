"""
Drawer Schema Tests — S36 Track A
=================================

INVARIANTS PROVEN:
  - INV-HARNESS-1: Gate status only, never grades
  - INV-DRAWER-RULE-EXPLICIT: Rules declared in schema, not runtime

EXIT GATE A:
  Criterion: "5-drawer schema validates; no forbidden fields accepted"
  Proof: "Schema rejects any gate with quality/confidence/grade fields"
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Direct import to avoid pandas dependency in cso/__init__.py
PHOENIX_ROOT = Path(__file__).parent.parent.parent
DRAWER_PATH = PHOENIX_ROOT / "cso" / "drawer.py"

spec = importlib.util.spec_from_file_location("drawer", DRAWER_PATH)
drawer_module = importlib.util.module_from_spec(spec)
sys.modules["drawer"] = drawer_module
spec.loader.exec_module(drawer_module)

FORBIDDEN_FIELDS = drawer_module.FORBIDDEN_FIELDS
DrawerEvaluationResult = drawer_module.DrawerEvaluationResult
DrawerRuleType = drawer_module.DrawerRuleType
DrawerSchemaValidator = drawer_module.DrawerSchemaValidator
GateDefinition = drawer_module.GateDefinition
GateEvaluationResult = drawer_module.GateEvaluationResult
ValidationError = drawer_module.ValidationError
evaluate_drawer_rule = drawer_module.evaluate_drawer_rule


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def validator() -> DrawerSchemaValidator:
    """Create validator instance."""
    return DrawerSchemaValidator()


@pytest.fixture
def valid_gate() -> dict:
    """Valid gate definition."""
    return {
        "id": "test_gate",
        "drawer": 1,
        "name": "Test Gate",
        "predicate": "test_condition == true",
        "required": True,
    }


@pytest.fixture
def valid_drawer() -> dict:
    """Valid drawer definition."""
    return {
        "id": 1,
        "name": "Test Drawer",
        "gates": ["gate_a", "gate_b"],
        "evaluation": {
            "type": "EXPLICIT_BOOLEAN_RULE",
            "rule": "all_required",
            "logic": "gate_a AND gate_b",
            "runtime_configurable": False,
        },
    }


# =============================================================================
# FORBIDDEN FIELD REJECTION TESTS
# =============================================================================


class TestForbiddenFieldRejection:
    """Tests for forbidden field rejection."""

    def test_gate_rejects_quality_score(self, validator: DrawerSchemaValidator) -> None:
        """Gate with quality_score is rejected."""
        gate = {
            "id": "test",
            "drawer": 1,
            "name": "Test",
            "predicate": "x",
            "quality_score": 0.8,
        }
        result = validator.validate_gate(gate)
        assert not result.valid
        assert any(e.code == "FORBIDDEN_FIELD" for e in result.errors)

    def test_gate_rejects_confidence(self, validator: DrawerSchemaValidator) -> None:
        """Gate with confidence is rejected."""
        gate = {
            "id": "test",
            "drawer": 1,
            "name": "Test",
            "predicate": "x",
            "confidence": 0.95,
        }
        result = validator.validate_gate(gate)
        assert not result.valid
        assert any(e.code == "FORBIDDEN_FIELD" for e in result.errors)

    def test_gate_rejects_grade(self, validator: DrawerSchemaValidator) -> None:
        """Gate with grade is rejected."""
        gate = {
            "id": "test",
            "drawer": 1,
            "name": "Test",
            "predicate": "x",
            "grade": "A",
        }
        result = validator.validate_gate(gate)
        assert not result.valid
        assert any(e.code == "FORBIDDEN_FIELD" for e in result.errors)

    def test_gate_rejects_rank(self, validator: DrawerSchemaValidator) -> None:
        """Gate with rank is rejected."""
        gate = {
            "id": "test",
            "drawer": 1,
            "name": "Test",
            "predicate": "x",
            "rank": 1,
        }
        result = validator.validate_gate(gate)
        assert not result.valid
        assert any(e.code == "FORBIDDEN_FIELD" for e in result.errors)

    def test_gate_rejects_weight(self, validator: DrawerSchemaValidator) -> None:
        """Gate with weight is rejected."""
        gate = {
            "id": "test",
            "drawer": 1,
            "name": "Test",
            "predicate": "x",
            "weight": 0.5,
        }
        result = validator.validate_gate(gate)
        assert not result.valid
        assert any(e.code == "FORBIDDEN_FIELD" for e in result.errors)

    def test_gate_rejects_priority(self, validator: DrawerSchemaValidator) -> None:
        """Gate with priority is rejected."""
        gate = {
            "id": "test",
            "drawer": 1,
            "name": "Test",
            "predicate": "x",
            "priority": 1,
        }
        result = validator.validate_gate(gate)
        assert not result.valid
        assert any(e.code == "FORBIDDEN_FIELD" for e in result.errors)

    def test_gate_rejects_score(self, validator: DrawerSchemaValidator) -> None:
        """Gate with score is rejected."""
        gate = {
            "id": "test",
            "drawer": 1,
            "name": "Test",
            "predicate": "x",
            "score": 85,
        }
        result = validator.validate_gate(gate)
        assert not result.valid
        assert any(e.code == "FORBIDDEN_FIELD" for e in result.errors)


# =============================================================================
# DRAWER RULE EXPLICIT TESTS
# =============================================================================


class TestDrawerRuleExplicit:
    """Tests for drawer rule explicit declaration."""

    def test_drawer_rejects_runtime_configurable(self, validator: DrawerSchemaValidator) -> None:
        """Drawer with runtime_configurable=True is rejected."""
        drawer = {
            "id": 1,
            "name": "Test",
            "gates": ["a"],
            "evaluation": {
                "type": "EXPLICIT_BOOLEAN_RULE",
                "rule": "all_required",
                "runtime_configurable": True,
            },
        }
        result = validator.validate_drawer(drawer)
        assert not result.valid
        assert any(e.code == "RUNTIME_CONFIG_FORBIDDEN" for e in result.errors)

    def test_drawer_rejects_quality_threshold(self, validator: DrawerSchemaValidator) -> None:
        """Drawer with quality_threshold is rejected."""
        drawer = {
            "id": 1,
            "name": "Test",
            "gates": ["a"],
            "evaluation": {
                "type": "EXPLICIT_BOOLEAN_RULE",
                "rule": "all_required",
                "quality_threshold": 0.7,
            },
        }
        result = validator.validate_drawer(drawer)
        assert not result.valid
        assert any(e.code == "FORBIDDEN_FIELD" for e in result.errors)

    def test_drawer_requires_explicit_boolean_rule(self, validator: DrawerSchemaValidator) -> None:
        """Drawer must use EXPLICIT_BOOLEAN_RULE type."""
        drawer = {
            "id": 1,
            "name": "Test",
            "gates": ["a"],
            "evaluation": {
                "type": "QUALITY_SCORE",  # Invalid
                "rule": "all_required",
            },
        }
        result = validator.validate_drawer(drawer)
        assert not result.valid
        assert any(e.code == "INVALID_EVALUATION_TYPE" for e in result.errors)


# =============================================================================
# VALID SCHEMA TESTS
# =============================================================================


class TestValidSchemas:
    """Tests for valid schema acceptance."""

    def test_valid_gate_accepted(self, validator: DrawerSchemaValidator, valid_gate: dict) -> None:
        """Valid gate is accepted."""
        result = validator.validate_gate(valid_gate)
        assert result.valid

    def test_valid_drawer_accepted(
        self, validator: DrawerSchemaValidator, valid_drawer: dict
    ) -> None:
        """Valid drawer is accepted."""
        result = validator.validate_drawer(valid_drawer)
        assert result.valid

    def test_gate_with_threshold_accepted(self, validator: DrawerSchemaValidator) -> None:
        """Gate with threshold (for delta) is accepted."""
        gate = {
            "id": "test",
            "drawer": 1,
            "name": "Test",
            "predicate": "x < 50",
            "required": True,
            "threshold": 50,
        }
        result = validator.validate_gate(gate)
        assert result.valid

    def test_gate_with_data_requirements_accepted(self, validator: DrawerSchemaValidator) -> None:
        """Gate with data_requirements is accepted."""
        gate = {
            "id": "test",
            "drawer": 1,
            "name": "Test",
            "predicate": "x",
            "required": True,
            "data_requirements": ["htf_data", "current_price"],
        }
        result = validator.validate_gate(gate)
        assert result.valid


# =============================================================================
# DRAWER RULE EVALUATION TESTS
# =============================================================================


class TestDrawerRuleEvaluation:
    """Tests for drawer rule evaluation."""

    def test_all_required_passes_when_all_pass(self) -> None:
        """ALL_REQUIRED passes when all gates pass."""
        results = {
            "a": GateEvaluationResult("a", True),
            "b": GateEvaluationResult("b", True),
            "c": GateEvaluationResult("c", True),
        }
        passed = evaluate_drawer_rule(DrawerRuleType.ALL_REQUIRED, results, ["a", "b", "c"])
        assert passed

    def test_all_required_fails_when_one_fails(self) -> None:
        """ALL_REQUIRED fails when one gate fails."""
        results = {
            "a": GateEvaluationResult("a", True),
            "b": GateEvaluationResult("b", False),
            "c": GateEvaluationResult("c", True),
        }
        passed = evaluate_drawer_rule(DrawerRuleType.ALL_REQUIRED, results, ["a", "b", "c"])
        assert not passed

    def test_minimum_2_of_3_passes_with_2(self) -> None:
        """MINIMUM_2_OF_3 passes with 2 of 3."""
        results = {
            "a": GateEvaluationResult("a", True),
            "b": GateEvaluationResult("b", False),
            "c": GateEvaluationResult("c", True),
        }
        passed = evaluate_drawer_rule(DrawerRuleType.MINIMUM_2_OF_3, results, ["a", "b", "c"])
        assert passed

    def test_minimum_2_of_3_fails_with_1(self) -> None:
        """MINIMUM_2_OF_3 fails with only 1."""
        results = {
            "a": GateEvaluationResult("a", True),
            "b": GateEvaluationResult("b", False),
            "c": GateEvaluationResult("c", False),
        }
        passed = evaluate_drawer_rule(DrawerRuleType.MINIMUM_2_OF_3, results, ["a", "b", "c"])
        assert not passed

    def test_at_least_one_directional_passes(self) -> None:
        """AT_LEAST_ONE_DIRECTIONAL passes with bullish + POI."""
        results = {
            "htf_structure_bullish": GateEvaluationResult("htf_structure_bullish", True),
            "htf_structure_bearish": GateEvaluationResult("htf_structure_bearish", False),
            "htf_poi_identified": GateEvaluationResult("htf_poi_identified", True),
        }
        passed = evaluate_drawer_rule(
            DrawerRuleType.AT_LEAST_ONE_DIRECTIONAL,
            results,
            ["htf_structure_bullish", "htf_structure_bearish", "htf_poi_identified"],
        )
        assert passed

    def test_at_least_one_directional_fails_without_poi(self) -> None:
        """AT_LEAST_ONE_DIRECTIONAL fails without POI."""
        results = {
            "htf_structure_bullish": GateEvaluationResult("htf_structure_bullish", True),
            "htf_structure_bearish": GateEvaluationResult("htf_structure_bearish", False),
            "htf_poi_identified": GateEvaluationResult("htf_poi_identified", False),
        }
        passed = evaluate_drawer_rule(
            DrawerRuleType.AT_LEAST_ONE_DIRECTIONAL,
            results,
            ["htf_structure_bullish", "htf_structure_bearish", "htf_poi_identified"],
        )
        assert not passed


# =============================================================================
# GATE EVALUATION RESULT VALIDATION
# =============================================================================


class TestGateEvaluationResultValidation:
    """Tests for gate evaluation result validation."""

    def test_result_rejects_quality_score(self, validator: DrawerSchemaValidator) -> None:
        """Evaluation result with quality_score is rejected."""
        result_dict = {
            "gate_id": "test",
            "passed": True,
            "quality_score": 0.85,
        }
        validation = validator.validate_gate_evaluation_result(result_dict)
        assert not validation.valid
        assert any(e.code == "FORBIDDEN_FIELD_IN_OUTPUT" for e in validation.errors)

    def test_result_rejects_confidence(self, validator: DrawerSchemaValidator) -> None:
        """Evaluation result with confidence is rejected."""
        result_dict = {
            "gate_id": "test",
            "passed": True,
            "confidence": 0.95,
        }
        validation = validator.validate_gate_evaluation_result(result_dict)
        assert not validation.valid

    def test_valid_result_accepted(self, validator: DrawerSchemaValidator) -> None:
        """Valid evaluation result is accepted."""
        result_dict = {
            "gate_id": "test",
            "passed": True,
            "predicate_delta": None,
        }
        validation = validator.validate_gate_evaluation_result(result_dict)
        assert validation.valid


# =============================================================================
# SCHEMA LOADING TESTS
# =============================================================================


class TestSchemaLoading:
    """Tests for schema loading."""

    def test_get_drawer_definitions(self, validator: DrawerSchemaValidator) -> None:
        """Can load drawer definitions from schema."""
        definitions = validator.get_drawer_definitions()
        # Should have 5 drawers
        assert len(definitions) == 5
        assert 1 in definitions
        assert definitions[1].name == "HTF Bias"

    def test_get_gate_definitions(self, validator: DrawerSchemaValidator) -> None:
        """Can load gate definitions from schema."""
        definitions = validator.get_gate_definitions()
        # Should have gates
        assert len(definitions) > 0
        assert "htf_structure_bullish" in definitions


# =============================================================================
# PREDICATE DELTA TESTS
# =============================================================================


class TestPredicateDelta:
    """Tests for predicate delta on failure."""

    def test_gate_result_with_numeric_delta(self) -> None:
        """Gate result can include numeric delta."""
        result = GateEvaluationResult(
            gate_id="htf_poi_identified",
            passed=False,
            predicate_delta="delta: 1.2 pips from threshold",
        )
        assert result.predicate_delta == "delta: 1.2 pips from threshold"

    def test_gate_result_with_enum_delta(self) -> None:
        """Gate result can include enum delta."""
        result = GateEvaluationResult(
            gate_id="kill_zone_active",
            passed=False,
            predicate_delta="actual: tokyo",
        )
        assert result.predicate_delta == "actual: tokyo"

    def test_gate_result_with_null_delta(self) -> None:
        """Gate result can have null delta (boolean predicates)."""
        result = GateEvaluationResult(
            gate_id="fvg_present",
            passed=False,
            predicate_delta=None,
        )
        assert result.predicate_delta is None


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
