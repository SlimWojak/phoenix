"""
5-Drawer Schema Validation — S36 Track A
========================================

Validates drawer and gate schemas.
Rejects any forbidden fields (grades, scores, weights).

INVARIANTS:
  - INV-HARNESS-1: Gate status only, never grades
  - INV-DRAWER-RULE-EXPLICIT: Rules in conditions.yaml only
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# CONSTANTS
# =============================================================================

CSO_ROOT = Path(__file__).parent
SCHEMAS_PATH = CSO_ROOT / "schemas"
DRAWER_SCHEMA_PATH = SCHEMAS_PATH / "drawer_schema.yaml"
GATE_SCHEMA_PATH = SCHEMAS_PATH / "gate_schema.yaml"

# Fields that are NEVER allowed
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


# =============================================================================
# TYPES
# =============================================================================


class DrawerRuleType(Enum):
    """Type of drawer evaluation rule."""

    AT_LEAST_ONE_DIRECTIONAL = "at_least_one_directional"
    ALL_GATES_INDEPENDENT = "all_gates_independent"
    MINIMUM_2_OF_3 = "minimum_2_of_3"
    ALL_REQUIRED = "all_required"


@dataclass
class GateDefinition:
    """Definition of a single gate."""

    id: str
    drawer: int
    name: str
    predicate: str
    required: bool
    threshold: float | None = None
    data_requirements: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class DrawerDefinition:
    """Definition of a drawer."""

    id: int
    name: str
    description: str
    gates: list[str]
    rule: DrawerRuleType
    logic: str
    runtime_configurable: bool = False


@dataclass
class GateEvaluationResult:
    """Result of evaluating a single gate."""

    gate_id: str
    passed: bool
    predicate_delta: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    data_hash: str = ""


@dataclass
class DrawerEvaluationResult:
    """Result of evaluating a drawer."""

    drawer_id: int
    drawer_name: str
    passed: bool
    gates_passed: list[str] = field(default_factory=list)
    gates_failed: list[str] = field(default_factory=list)
    gates_skipped: list[str] = field(default_factory=list)
    rule_applied: str = ""


@dataclass
class ValidationError:
    """Schema validation error."""

    field: str
    message: str
    code: str


@dataclass
class ValidationResult:
    """Result of schema validation."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def error_messages(self) -> list[str]:
        return [f"{e.code}: {e.message}" for e in self.errors]


# =============================================================================
# SCHEMA VALIDATOR
# =============================================================================


class DrawerSchemaValidator:
    """
    Validates drawer and gate definitions.

    Rejects any forbidden fields (grades, scores, weights).
    Ensures drawer rules are explicit, not runtime configurable.

    INVARIANTS:
      - INV-HARNESS-1: No grades, scores, or weights
      - INV-DRAWER-RULE-EXPLICIT: Rules declared in schema
    """

    def __init__(self) -> None:
        """Initialize validator with schemas."""
        self._drawer_schema: dict[str, Any] | None = None
        self._gate_schema: dict[str, Any] | None = None

    def _load_drawer_schema(self) -> dict[str, Any]:
        """Load drawer schema."""
        if self._drawer_schema is not None:
            return self._drawer_schema

        if DRAWER_SCHEMA_PATH.exists():
            with open(DRAWER_SCHEMA_PATH) as f:
                self._drawer_schema = yaml.safe_load(f)
        else:
            self._drawer_schema = {"forbidden_fields": list(FORBIDDEN_FIELDS)}

        return self._drawer_schema

    def _load_gate_schema(self) -> dict[str, Any]:
        """Load gate schema."""
        if self._gate_schema is not None:
            return self._gate_schema

        if GATE_SCHEMA_PATH.exists():
            with open(GATE_SCHEMA_PATH) as f:
                self._gate_schema = yaml.safe_load(f)
        else:
            self._gate_schema = {}

        return self._gate_schema

    def validate_gate(self, gate_dict: dict[str, Any]) -> ValidationResult:
        """
        Validate a gate definition.

        Checks:
        1. Required fields present
        2. No forbidden fields
        3. Valid drawer reference

        Args:
            gate_dict: Gate definition dictionary

        Returns:
            ValidationResult
        """
        errors: list[ValidationError] = []

        # Check required fields
        required = ["id", "drawer", "name", "predicate"]
        for field_name in required:
            if field_name not in gate_dict:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=f"Required field '{field_name}' missing",
                        code="MISSING_REQUIRED_FIELD",
                    )
                )

        # Check forbidden fields
        for field_name in gate_dict:
            if field_name.lower() in FORBIDDEN_FIELDS:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=f"Forbidden field '{field_name}' — grades/scores not allowed",
                        code="FORBIDDEN_FIELD",
                    )
                )

        # Check drawer range
        drawer = gate_dict.get("drawer")
        if drawer is not None and (drawer < 1 or drawer > 5):
            errors.append(
                ValidationError(
                    field="drawer",
                    message=f"Drawer must be 1-5, got {drawer}",
                    code="INVALID_DRAWER",
                )
            )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_drawer(self, drawer_dict: dict[str, Any]) -> ValidationResult:
        """
        Validate a drawer definition.

        Checks:
        1. Required fields present
        2. No forbidden fields
        3. Rule is explicit (not runtime configurable)
        4. Valid evaluation type

        Args:
            drawer_dict: Drawer definition dictionary

        Returns:
            ValidationResult
        """
        errors: list[ValidationError] = []

        # Check required fields
        required = ["id", "name", "gates", "evaluation"]
        for field_name in required:
            if field_name not in drawer_dict:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=f"Required field '{field_name}' missing",
                        code="MISSING_REQUIRED_FIELD",
                    )
                )

        # Check forbidden fields
        for field_name in drawer_dict:
            if field_name.lower() in FORBIDDEN_FIELDS:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=f"Forbidden field '{field_name}' — grades/scores not allowed",
                        code="FORBIDDEN_FIELD",
                    )
                )

        # Check evaluation structure
        evaluation = drawer_dict.get("evaluation", {})
        if isinstance(evaluation, dict):
            # Must be EXPLICIT_BOOLEAN_RULE
            eval_type = evaluation.get("type")
            if eval_type != "EXPLICIT_BOOLEAN_RULE":
                errors.append(
                    ValidationError(
                        field="evaluation.type",
                        message=f"Evaluation type must be EXPLICIT_BOOLEAN_RULE, got {eval_type}",
                        code="INVALID_EVALUATION_TYPE",
                    )
                )

            # Must NOT be runtime configurable
            if evaluation.get("runtime_configurable", False):
                errors.append(
                    ValidationError(
                        field="evaluation.runtime_configurable",
                        message="Drawer rules cannot be runtime configurable (INV-DRAWER-RULE-EXPLICIT)",
                        code="RUNTIME_CONFIG_FORBIDDEN",
                    )
                )

            # Check for quality_threshold in evaluation
            if "quality_threshold" in evaluation:
                errors.append(
                    ValidationError(
                        field="evaluation.quality_threshold",
                        message="quality_threshold is forbidden in drawer evaluation",
                        code="FORBIDDEN_FIELD",
                    )
                )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_gate_evaluation_result(self, result_dict: dict[str, Any]) -> ValidationResult:
        """
        Validate a gate evaluation result.

        Ensures no forbidden fields leak into output.

        Args:
            result_dict: Gate evaluation result dictionary

        Returns:
            ValidationResult
        """
        errors: list[ValidationError] = []

        # Check forbidden fields in result
        for field_name in result_dict:
            if field_name.lower() in FORBIDDEN_FIELDS:
                errors.append(
                    ValidationError(
                        field=field_name,
                        message=f"Forbidden field '{field_name}' in evaluation result",
                        code="FORBIDDEN_FIELD_IN_OUTPUT",
                    )
                )

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def get_drawer_definitions(self) -> dict[int, DrawerDefinition]:
        """Get all drawer definitions from schema."""
        schema = self._load_drawer_schema()
        drawers_dict = schema.get("drawers", {})

        definitions: dict[int, DrawerDefinition] = {}

        for drawer_key, drawer_data in drawers_dict.items():
            drawer_id = drawer_data.get("id", 0)
            evaluation = drawer_data.get("evaluation", {})

            rule_str = evaluation.get("rule", "all_required")
            try:
                rule = DrawerRuleType(rule_str)
            except ValueError:
                rule = DrawerRuleType.ALL_REQUIRED

            definitions[drawer_id] = DrawerDefinition(
                id=drawer_id,
                name=drawer_data.get("name", ""),
                description=drawer_data.get("description", ""),
                gates=drawer_data.get("gates", []),
                rule=rule,
                logic=evaluation.get("logic", ""),
                runtime_configurable=evaluation.get("runtime_configurable", False),
            )

        return definitions

    def get_gate_definitions(self) -> dict[str, GateDefinition]:
        """Get all gate definitions from schema."""
        schema = self._load_gate_schema()
        gates_dict = schema.get("gates", {})

        definitions: dict[str, GateDefinition] = {}

        for gate_id, gate_data in gates_dict.items():
            definitions[gate_id] = GateDefinition(
                id=gate_id,
                drawer=gate_data.get("drawer", 0),
                name=gate_data.get("name", ""),
                predicate=gate_data.get("predicate", ""),
                required=gate_data.get("required", False),
                threshold=gate_data.get("threshold"),
                data_requirements=gate_data.get("data_requirements", []),
                description=gate_data.get("description", ""),
            )

        return definitions


# =============================================================================
# DRAWER RULE EVALUATORS
# =============================================================================


def evaluate_drawer_rule(
    rule: DrawerRuleType,
    gate_results: dict[str, GateEvaluationResult],
    gate_ids: list[str],
) -> bool:
    """
    Evaluate a drawer rule against gate results.

    Args:
        rule: The drawer rule type
        gate_results: Dict of gate_id -> GateEvaluationResult
        gate_ids: List of gate IDs in this drawer

    Returns:
        True if drawer passes
    """
    if rule == DrawerRuleType.AT_LEAST_ONE_DIRECTIONAL:
        # Special case: at least one directional gate + POI
        directional_gates = ["htf_structure_bullish", "htf_structure_bearish"]
        poi_gate = "htf_poi_identified"

        directional_passed = any(
            gate_results.get(g, GateEvaluationResult(g, False)).passed
            for g in directional_gates
            if g in gate_ids
        )
        poi_passed = gate_results.get(poi_gate, GateEvaluationResult(poi_gate, False)).passed

        return directional_passed and poi_passed

    elif rule == DrawerRuleType.ALL_GATES_INDEPENDENT:
        # All gates evaluated independently — drawer always "passes"
        # (gates are informational only)
        return True

    elif rule == DrawerRuleType.MINIMUM_2_OF_3:
        # At least 2 of 3 gates must pass
        passed_count = sum(
            1
            for gate_id in gate_ids
            if gate_results.get(gate_id, GateEvaluationResult(gate_id, False)).passed
        )
        return passed_count >= 2

    elif rule == DrawerRuleType.ALL_REQUIRED:
        # All gates must pass
        return all(
            gate_results.get(gate_id, GateEvaluationResult(gate_id, False)).passed
            for gate_id in gate_ids
        )

    return False


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "DrawerSchemaValidator",
    "DrawerDefinition",
    "GateDefinition",
    "GateEvaluationResult",
    "DrawerEvaluationResult",
    "DrawerRuleType",
    "ValidationResult",
    "ValidationError",
    "evaluate_drawer_rule",
    "FORBIDDEN_FIELDS",
]
