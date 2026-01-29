"""
Lens Query Validation — Constitutional Boundary Enforcement
===========================================================

S35 TRACK A DELIVERABLE
Created: 2026-01-29 (Day 1)

This module enforces the constitutional boundary for CFP queries.
If it's not in lens_schema.yaml, it can't be queried.

INVARIANTS ENFORCED:
  - INV-REGIME-EXPLICIT: Regimes from conditions.yaml only
  - INV-METRIC-DEFINITION-EXPLICIT: All metrics have computational definitions
  - INV-ATTR-CAUSAL-BAN: No causal predicates allowed

USAGE:
    query = LensQuery(
        source="river",
        group_by=["session"],
        aggregate={"metrics": ["sharpe", "win_rate"]},
        strategy_config_hash="abc123...",
    )
    
    validator = LensQueryValidator()
    result = validator.validate(query)
    
    if not result.valid:
        print(result.errors)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# CONSTANTS
# =============================================================================

PHOENIX_ROOT = Path(__file__).parent.parent
CONDITIONS_PATH = PHOENIX_ROOT / "cso" / "knowledge" / "conditions.yaml"
LENS_SCHEMA_PATH = PHOENIX_ROOT / "cfp" / "schemas" / "lens_schema.yaml"

# Maximum limits
MAX_GROUPS_DEFAULT = 100
MAX_GROUPS_HARD_LIMIT = 1000
MAX_PREDICATES = 10
MAX_METRICS = 5
MAX_GROUP_BY_DIMS = 4


# =============================================================================
# ENUMS
# =============================================================================


class QuerySource(Enum):
    """Data source for CFP query."""

    RIVER = "river"
    BEADS = "beads"
    POSITIONS = "positions"


class OutputFormat(Enum):
    """Output format for CFP result."""

    TABLE = "table"
    SINGLE_VALUE = "single_value"


class ValidationSeverity(Enum):
    """Severity level for validation errors."""

    REJECT = "REJECT"
    WARNING = "WARNING"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Predicate:
    """Filter predicate for lens query."""

    field: str
    op: str
    value: Any

    ALLOWED_OPS = frozenset(["==", "!=", ">", "<", ">=", "<=", "in", "not_in"])

    def __post_init__(self) -> None:
        if self.op not in self.ALLOWED_OPS:
            raise ValueError(f"Invalid operator: {self.op}")


@dataclass
class TimeRange:
    """Time range filter."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("end must be after start")


@dataclass
class FilterSpec:
    """Filter specification for lens query."""

    conditions: list[Predicate] = field(default_factory=list)
    time_range: TimeRange | None = None


@dataclass
class AggregateSpec:
    """Aggregation specification."""

    metrics: list[str] = field(default_factory=list)


@dataclass
class OutputSpec:
    """Output specification."""

    format: OutputFormat = OutputFormat.TABLE
    include_provenance: bool = True  # Immutable — always True


@dataclass
class LensQuery:
    """
    Lens Query — The question schema for CFP.
    
    This dataclass represents a validated query that can be executed
    against River data or the bead store.
    
    REQUIRED:
        source: Data source (river, beads, positions)
        aggregate: Metrics to compute
        strategy_config_hash: Anchors fact to specific strategy version
        
    OPTIONAL:
        group_by: Dimensions to group by (max 4)
        filter: Predicates and time range
        max_groups: Maximum groups to return (default 100)
    """

    source: QuerySource
    aggregate: AggregateSpec
    strategy_config_hash: str
    output: OutputSpec = field(default_factory=OutputSpec)
    group_by: list[str] = field(default_factory=list)
    filter: FilterSpec | None = None
    max_groups: int = MAX_GROUPS_DEFAULT

    def __post_init__(self) -> None:
        # Coerce source to enum if string
        if isinstance(self.source, str):
            self.source = QuerySource(self.source)

        # Coerce output format if nested dict
        if isinstance(self.output, dict):
            fmt = self.output.get("format", "table")
            self.output = OutputSpec(format=OutputFormat(fmt))

        # Coerce aggregate if dict
        if isinstance(self.aggregate, dict):
            self.aggregate = AggregateSpec(metrics=self.aggregate.get("metrics", []))

        # Ensure provenance is always included (immutable)
        self.output.include_provenance = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LensQuery:
        """Create LensQuery from dictionary."""
        # Parse filter if present
        filter_spec = None
        if "filter" in data:
            filter_data = data["filter"]
            conditions = []
            for cond in filter_data.get("conditions", []):
                conditions.append(
                    Predicate(
                        field=cond["field"],
                        op=cond["op"],
                        value=cond["value"],
                    )
                )

            time_range = None
            if "time_range" in filter_data:
                tr = filter_data["time_range"]
                time_range = TimeRange(
                    start=datetime.fromisoformat(tr["start"].replace("Z", "+00:00")),
                    end=datetime.fromisoformat(tr["end"].replace("Z", "+00:00")),
                )

            filter_spec = FilterSpec(conditions=conditions, time_range=time_range)

        return cls(
            source=data["source"],
            aggregate=data.get("aggregate", {"metrics": []}),
            strategy_config_hash=data["strategy_config_hash"],
            output=data.get("output", {}),
            group_by=data.get("group_by", []),
            filter=filter_spec,
            max_groups=data.get("max_groups", MAX_GROUPS_DEFAULT),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "source": self.source.value,
            "aggregate": {"metrics": self.aggregate.metrics},
            "strategy_config_hash": self.strategy_config_hash,
            "output": {
                "format": self.output.format.value,
                "include_provenance": True,
            },
            "group_by": self.group_by,
            "max_groups": self.max_groups,
        }

        if self.filter:
            result["filter"] = {
                "conditions": [
                    {"field": p.field, "op": p.op, "value": p.value}
                    for p in self.filter.conditions
                ],
            }
            if self.filter.time_range:
                result["filter"]["time_range"] = {
                    "start": self.filter.time_range.start.isoformat(),
                    "end": self.filter.time_range.end.isoformat(),
                }

        return result


@dataclass
class ValidationError:
    """Single validation error."""

    code: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.REJECT
    field: str | None = None
    value: Any = None


@dataclass
class ValidationResult:
    """Result of lens query validation."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def add_error(self, error: ValidationError) -> None:
        """Add a validation error."""
        if error.severity == ValidationSeverity.REJECT:
            self.errors.append(error)
            self.valid = False
        else:
            self.warnings.append(error)


# =============================================================================
# VALIDATOR
# =============================================================================


class LensQueryValidator:
    """
    Validates LensQuery against constitutional schema.
    
    Loads allowed values from:
      - lens_schema.yaml (metric definitions, allowed fields)
      - conditions.yaml (valid regimes, composite gates)
    
    INVARIANTS ENFORCED:
      - INV-REGIME-EXPLICIT
      - INV-METRIC-DEFINITION-EXPLICIT
      - INV-ATTR-CAUSAL-BAN (partial — full enforcement in linter)
    """

    # Allowed group_by dimensions
    ALLOWED_GROUP_BY = frozenset([
        "session",
        "kill_zone",
        "pair",
        "regime",
        "direction",
        "day_of_week",
        "hour",
    ])

    # Forbidden group_by (cardinality explosion)
    FORBIDDEN_GROUP_BY = frozenset(["timestamp", "tick", "trade_id"])

    # Allowed metrics
    ALLOWED_METRICS = frozenset([
        "sharpe",
        "win_rate",
        "pnl",
        "profit_factor",
        "max_drawdown",
        "trade_count",
    ])

    # Allowed predicate fields
    ALLOWED_PREDICATE_FIELDS = frozenset([
        # Time-based
        "session",
        "kill_zone",
        "day_of_week",
        "entry_hour",
        "exit_hour",
        # Pair/Direction
        "pair",
        "direction",
        # Gate-based
        "gates_passed_count",
        "gates_failed_count",
        # Regime
        "regime",
        "trade_bias",
        "htf_direction",
        # Composite gates
        "composite_gates.alignment_gate",
        "composite_gates.freshness_gate",
        "composite_gates.high_quality_long",
        "composite_gates.high_quality_short",
        # Outcome
        "result",
        # Enrichment
        "zone",
        "in_fvg",
        "in_ob",
        "htf_unanimous",
    ])

    # Forbidden predicate patterns (regex)
    FORBIDDEN_PREDICATE_PATTERNS = [
        (r"auto_.*", "No auto-detected fields allowed"),
        (r"quality_score", "No quality scores — implies ranking"),
        (r"grade", "No grades — INV-HARNESS-1"),
        (r"confidence", "No confidence thresholds without explicit formula"),
        (r"best_.*", "No 'best' in predicates"),
        (r"worst_.*", "No 'worst' in predicates"),
        (r"optimal_.*", "No 'optimal' in predicates"),
    ]

    # Causal language patterns (partial — full in linter)
    CAUSAL_PATTERNS = [
        (r"contributed", "INV-ATTR-CAUSAL-BAN"),
        (r"caused", "INV-ATTR-CAUSAL-BAN"),
        (r"because", "INV-ATTR-CAUSAL-BAN"),
    ]

    def __init__(
        self,
        conditions_path: Path | None = None,
    ) -> None:
        """
        Initialize validator.
        
        Args:
            conditions_path: Path to conditions.yaml (for regime validation)
        """
        self._conditions_path = conditions_path or CONDITIONS_PATH
        self._valid_regimes: set[str] | None = None
        self._composite_gates: set[str] | None = None

    def _load_conditions(self) -> None:
        """Load valid regimes from conditions.yaml."""
        if self._valid_regimes is not None:
            return

        self._valid_regimes = set()
        self._composite_gates = set()

        if not self._conditions_path.exists():
            return

        with open(self._conditions_path) as f:
            conditions = yaml.safe_load(f)

        # Extract valid trade_bias values
        if "bias_framework" in conditions:
            bias_synthesis = conditions["bias_framework"].get("bias_synthesis", {})
            logic = bias_synthesis.get("logic", [])
            for item in logic:
                if "output" in item:
                    self._valid_regimes.add(item["output"])

        # Extract composite gates
        if "composite_gates" in conditions:
            for gate_name in conditions["composite_gates"]:
                self._composite_gates.add(f"composite_gates.{gate_name}")

    def _get_valid_regimes(self) -> set[str]:
        """Get valid regime values from conditions.yaml."""
        self._load_conditions()
        return self._valid_regimes or set()

    def _get_composite_gates(self) -> set[str]:
        """Get valid composite gate names."""
        self._load_conditions()
        return self._composite_gates or set()

    def validate(self, query: LensQuery) -> ValidationResult:
        """
        Validate a LensQuery.
        
        Returns:
            ValidationResult with errors/warnings
        """
        result = ValidationResult(valid=True)

        # Check strategy_config_hash (REQUIRED)
        self._validate_strategy_hash(query, result)

        # Check source
        self._validate_source(query, result)

        # Check group_by
        self._validate_group_by(query, result)

        # Check max_groups
        self._validate_max_groups(query, result)

        # Check metrics
        self._validate_metrics(query, result)

        # Check predicates
        self._validate_predicates(query, result)

        # Check time range
        self._validate_time_range(query, result)

        return result

    def _validate_strategy_hash(
        self, query: LensQuery, result: ValidationResult
    ) -> None:
        """Validate strategy_config_hash is present and valid."""
        if not query.strategy_config_hash:
            result.add_error(
                ValidationError(
                    code="MISSING_STRATEGY_HASH",
                    message="strategy_config_hash is required",
                    field="strategy_config_hash",
                )
            )
            return

        # Basic hex format validation
        if not re.match(r"^[a-fA-F0-9]+$", query.strategy_config_hash):
            result.add_error(
                ValidationError(
                    code="INVALID_STRATEGY_HASH",
                    message="strategy_config_hash must be valid hex string",
                    field="strategy_config_hash",
                    value=query.strategy_config_hash,
                )
            )

    def _validate_source(self, query: LensQuery, result: ValidationResult) -> None:
        """Validate source is valid enum value."""
        # Already validated by enum in dataclass
        pass

    def _validate_group_by(self, query: LensQuery, result: ValidationResult) -> None:
        """Validate group_by dimensions."""
        if len(query.group_by) > MAX_GROUP_BY_DIMS:
            result.add_error(
                ValidationError(
                    code="TOO_MANY_DIMENSIONS",
                    message=f"group_by has {len(query.group_by)} dimensions, max is {MAX_GROUP_BY_DIMS}",
                    field="group_by",
                )
            )

        for dim in query.group_by:
            # Check for forbidden dimensions (cardinality explosion)
            if dim in self.FORBIDDEN_GROUP_BY:
                result.add_error(
                    ValidationError(
                        code="CARDINALITY_EXPLOSION",
                        message=f"group_by '{dim}' would cause cardinality explosion",
                        field="group_by",
                        value=dim,
                    )
                )

            # Check for allowed dimensions
            elif dim not in self.ALLOWED_GROUP_BY:
                result.add_error(
                    ValidationError(
                        code="UNKNOWN_GROUP_BY",
                        message=f"Unknown group_by dimension: '{dim}'",
                        field="group_by",
                        value=dim,
                    )
                )

    def _validate_max_groups(self, query: LensQuery, result: ValidationResult) -> None:
        """Validate max_groups limit."""
        if query.max_groups > MAX_GROUPS_HARD_LIMIT:
            result.add_error(
                ValidationError(
                    code="MAX_GROUPS_EXCEEDED",
                    message=f"max_groups {query.max_groups} exceeds hard limit of {MAX_GROUPS_HARD_LIMIT}",
                    field="max_groups",
                    value=query.max_groups,
                )
            )
        elif query.max_groups > MAX_GROUPS_DEFAULT:
            # Warning — T2 approval required
            result.add_error(
                ValidationError(
                    code="MAX_GROUPS_EXCEEDED",
                    message=f"max_groups {query.max_groups} exceeds {MAX_GROUPS_DEFAULT} (T2 required for override)",
                    severity=ValidationSeverity.WARNING,
                    field="max_groups",
                    value=query.max_groups,
                )
            )

    def _validate_metrics(self, query: LensQuery, result: ValidationResult) -> None:
        """Validate metrics are defined."""
        if not query.aggregate.metrics:
            result.add_error(
                ValidationError(
                    code="NO_METRICS",
                    message="At least one metric required in aggregate.metrics",
                    field="aggregate.metrics",
                )
            )
            return

        if len(query.aggregate.metrics) > MAX_METRICS:
            result.add_error(
                ValidationError(
                    code="TOO_MANY_METRICS",
                    message=f"Too many metrics ({len(query.aggregate.metrics)}), max is {MAX_METRICS}",
                    field="aggregate.metrics",
                )
            )

        for metric in query.aggregate.metrics:
            if metric not in self.ALLOWED_METRICS:
                result.add_error(
                    ValidationError(
                        code="UNKNOWN_METRIC",
                        message=f"Metric '{metric}' not in metric_definitions",
                        field="aggregate.metrics",
                        value=metric,
                    )
                )

    def _validate_predicates(self, query: LensQuery, result: ValidationResult) -> None:
        """Validate filter predicates."""
        if not query.filter or not query.filter.conditions:
            return

        if len(query.filter.conditions) > MAX_PREDICATES:
            result.add_error(
                ValidationError(
                    code="TOO_MANY_PREDICATES",
                    message=f"Too many predicates ({len(query.filter.conditions)}), max is {MAX_PREDICATES}",
                    field="filter.conditions",
                )
            )

        for pred in query.filter.conditions:
            # Check field is allowed
            if pred.field not in self.ALLOWED_PREDICATE_FIELDS:
                result.add_error(
                    ValidationError(
                        code="UNKNOWN_PREDICATE_FIELD",
                        message=f"Field '{pred.field}' not in allowed_predicate_fields",
                        field="filter.conditions",
                        value=pred.field,
                    )
                )

            # Check for forbidden patterns in field name
            for pattern, reason in self.FORBIDDEN_PREDICATE_PATTERNS:
                if re.search(pattern, pred.field, re.IGNORECASE):
                    result.add_error(
                        ValidationError(
                            code="FORBIDDEN_PREDICATE",
                            message=f"Predicate field '{pred.field}' is forbidden: {reason}",
                            field="filter.conditions",
                            value=pred.field,
                        )
                    )

            # Check for causal language
            for pattern, reason in self.CAUSAL_PATTERNS:
                if re.search(pattern, str(pred.value), re.IGNORECASE):
                    result.add_error(
                        ValidationError(
                            code="CAUSAL_LANGUAGE_DETECTED",
                            message=f"Causal language detected in predicate value: '{pred.value}'",
                            field="filter.conditions",
                            value=pred.value,
                        )
                    )

            # Validate regime values against conditions.yaml
            if pred.field == "regime":
                valid_regimes = self._get_valid_regimes()
                if valid_regimes and pred.value not in valid_regimes:
                    result.add_error(
                        ValidationError(
                            code="REGIME_NOT_IN_CONDITIONS",
                            message=f"Regime '{pred.value}' not found in conditions.yaml",
                            field="filter.conditions",
                            value=pred.value,
                        )
                    )

    def _validate_time_range(self, query: LensQuery, result: ValidationResult) -> None:
        """Validate time range."""
        if not query.filter or not query.filter.time_range:
            return

        tr = query.filter.time_range
        if tr.end <= tr.start:
            result.add_error(
                ValidationError(
                    code="INVALID_TIME_RANGE",
                    message="time_range.end must be after time_range.start",
                    field="filter.time_range",
                )
            )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "LensQuery",
    "LensQueryValidator",
    "ValidationResult",
    "ValidationError",
    "Predicate",
    "FilterSpec",
    "TimeRange",
    "QuerySource",
    "OutputFormat",
]
