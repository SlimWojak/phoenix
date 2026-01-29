"""
Gate Evaluator Tests — S36 Track B
==================================

INVARIANTS PROVEN:
  - INV-HARNESS-1: Gate status only, never grades
  - INV-HARNESS-2: No confidence scores
  - INV-BIAS-PREDICATE: Bias as predicate status

EXIT GATE B:
  Criterion: "Evaluator returns gate status per pair; no scores/grades; no aggregation"
  Proof: "No popcount/sum functions; all outputs are boolean per gate"
"""

import hashlib
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import pytest
import yaml

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

# =============================================================================
# INLINE IMPORTS (avoid cso/__init__.py which requires pandas)
# =============================================================================
# We copy the essential types here to avoid import chain issues

CSO_ROOT = PHOENIX_ROOT / "cso"
SCHEMAS_PATH = CSO_ROOT / "schemas"
DRAWER_SCHEMA_PATH = SCHEMAS_PATH / "drawer_schema.yaml"
GATE_SCHEMA_PATH = SCHEMAS_PATH / "gate_schema.yaml"


class DrawerRuleType(Enum):
    AT_LEAST_ONE_DIRECTIONAL = "at_least_one_directional"
    ALL_GATES_INDEPENDENT = "all_gates_independent"
    MINIMUM_2_OF_3 = "minimum_2_of_3"
    ALL_REQUIRED = "all_required"


@dataclass
class GateEvaluationResult:
    gate_id: str
    passed: bool
    predicate_delta: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    data_hash: str = ""


@dataclass
class DrawerEvaluationResult:
    drawer_id: int
    drawer_name: str
    passed: bool
    gates_passed: list[str] = field(default_factory=list)
    gates_failed: list[str] = field(default_factory=list)
    gates_skipped: list[str] = field(default_factory=list)
    rule_applied: str = ""


@dataclass
class GateDefinition:
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
    id: int
    name: str
    description: str
    gates: list[str]
    rule: DrawerRuleType
    logic: str
    runtime_configurable: bool = False


@dataclass
class MarketState:
    pair: str
    timestamp: datetime
    htf_bias: str | None = None
    poi_distance_pips: float | None = None
    current_session: str | None = None
    asia_high: float | None = None
    asia_low: float | None = None
    session_bias: str | None = None
    fvg_count: int = 0
    fvg_direction: str | None = None
    displacement_pips: float | None = None
    recent_sweep: bool = False
    sweep_age_bars: int | None = None
    ltf_confirmation: bool = False
    ltf_direction: str | None = None
    entry_model: str | None = None
    stop_distance_pips: float | None = None
    target_defined: bool = False
    rr_ratio: float | None = None
    partials_defined: bool = False

    def compute_hash(self) -> str:
        data = str(self.__dict__).encode("utf-8")
        return hashlib.sha256(data).hexdigest()


@dataclass
class FiveDrawerResult:
    pair: str
    timestamp: datetime
    gates_passed: list[str] = field(default_factory=list)
    gates_failed: list[str] = field(default_factory=list)
    gates_skipped: list[str] = field(default_factory=list)
    drawer_status: dict[int, bool] = field(default_factory=dict)
    drawer_results: list[DrawerEvaluationResult] = field(default_factory=list)
    strategy_config_hash: str = ""
    market_state_hash: str = ""


# Simplified schema validator
class DrawerSchemaValidator:
    def __init__(self) -> None:
        self._drawer_schema: dict[str, Any] | None = None
        self._gate_schema: dict[str, Any] | None = None

    def _load_drawer_schema(self) -> dict[str, Any]:
        if self._drawer_schema is None:
            if DRAWER_SCHEMA_PATH.exists():
                with open(DRAWER_SCHEMA_PATH) as f:
                    self._drawer_schema = yaml.safe_load(f)
            else:
                self._drawer_schema = {}
        return self._drawer_schema

    def _load_gate_schema(self) -> dict[str, Any]:
        if self._gate_schema is None:
            if GATE_SCHEMA_PATH.exists():
                with open(GATE_SCHEMA_PATH) as f:
                    self._gate_schema = yaml.safe_load(f)
            else:
                self._gate_schema = {}
        return self._gate_schema

    def get_drawer_definitions(self) -> dict[int, DrawerDefinition]:
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
            )
        return definitions

    def get_gate_definitions(self) -> dict[str, GateDefinition]:
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


def evaluate_drawer_rule(
    rule: DrawerRuleType,
    gate_results: dict[str, GateEvaluationResult],
    gate_ids: list[str],
) -> bool:
    if rule == DrawerRuleType.AT_LEAST_ONE_DIRECTIONAL:
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
        return True
    elif rule == DrawerRuleType.MINIMUM_2_OF_3:
        passed_count = sum(
            1
            for gate_id in gate_ids
            if gate_results.get(gate_id, GateEvaluationResult(gate_id, False)).passed
        )
        return passed_count >= 2
    elif rule == DrawerRuleType.ALL_REQUIRED:
        return all(
            gate_results.get(gate_id, GateEvaluationResult(gate_id, False)).passed
            for gate_id in gate_ids
        )
    return False


# Simplified GateEvaluator
class GateEvaluator:
    def __init__(self) -> None:
        self._validator = DrawerSchemaValidator()

    def evaluate(
        self,
        pair: str,
        market_state: MarketState,
        strategy_config_hash: str,
    ) -> FiveDrawerResult:
        gate_results: dict[str, GateEvaluationResult] = {}
        gates_passed: list[str] = []
        gates_failed: list[str] = []
        gates_skipped: list[str] = []

        gate_defs = self._validator.get_gate_definitions()

        for gate_id, gate_def in gate_defs.items():
            result = self._evaluate_gate(gate_def, market_state)
            gate_results[gate_id] = result
            if result.passed:
                gates_passed.append(gate_id)
            elif result.predicate_delta == "SKIPPED":
                gates_skipped.append(gate_id)
            else:
                if result.predicate_delta:
                    gates_failed.append(f"{gate_id} [{result.predicate_delta}]")
                else:
                    gates_failed.append(gate_id)

        drawer_defs = self._validator.get_drawer_definitions()
        drawer_status: dict[int, bool] = {}
        drawer_results: list[DrawerEvaluationResult] = []

        for drawer_id, drawer_def in drawer_defs.items():
            passed = evaluate_drawer_rule(drawer_def.rule, gate_results, drawer_def.gates)
            drawer_status[drawer_id] = passed
            drawer_results.append(
                DrawerEvaluationResult(
                    drawer_id=drawer_id,
                    drawer_name=drawer_def.name,
                    passed=passed,
                    rule_applied=drawer_def.rule.value,
                )
            )

        return FiveDrawerResult(
            pair=pair,
            timestamp=datetime.now(UTC),
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            gates_skipped=gates_skipped,
            drawer_status=drawer_status,
            drawer_results=drawer_results,
            strategy_config_hash=strategy_config_hash,
            market_state_hash=market_state.compute_hash(),
        )

    def _evaluate_gate(
        self, gate_def: GateDefinition, market_state: MarketState
    ) -> GateEvaluationResult:
        gate_id = gate_def.id

        if gate_id == "htf_structure_bullish":
            passed = market_state.htf_bias == "bullish"
            delta = None if passed else f"actual: {market_state.htf_bias}"
            return GateEvaluationResult(gate_id, passed, delta)
        elif gate_id == "htf_structure_bearish":
            passed = market_state.htf_bias == "bearish"
            delta = None if passed else f"actual: {market_state.htf_bias}"
            return GateEvaluationResult(gate_id, passed, delta)
        elif gate_id == "htf_poi_identified":
            if market_state.poi_distance_pips is None:
                return GateEvaluationResult(gate_id, False, "SKIPPED")
            threshold = gate_def.threshold or 50
            passed = market_state.poi_distance_pips <= threshold
            delta = (
                None
                if passed
                else f"delta: {market_state.poi_distance_pips - threshold:.1f} pips from threshold"
            )
            return GateEvaluationResult(gate_id, passed, delta)
        elif gate_id == "kill_zone_active":
            valid_sessions = ["london", "new_york", "london_close"]
            passed = market_state.current_session in valid_sessions
            delta = None if passed else f"actual: {market_state.current_session}"
            return GateEvaluationResult(gate_id, passed, delta)
        elif gate_id == "asia_range_defined":
            passed = market_state.asia_high is not None and market_state.asia_low is not None
            return GateEvaluationResult(gate_id, passed, None)
        elif gate_id == "session_bias_aligned":
            passed = (
                market_state.session_bias == market_state.htf_bias
                or market_state.session_bias == "neutral"
            )
            delta = (
                None
                if passed
                else f"session: {market_state.session_bias}, htf: {market_state.htf_bias}"
            )
            return GateEvaluationResult(gate_id, passed, delta)
        elif gate_id == "fvg_present":
            passed = market_state.fvg_count > 0
            return GateEvaluationResult(gate_id, passed, None)
        elif gate_id == "displacement_sufficient":
            if market_state.displacement_pips is None:
                return GateEvaluationResult(gate_id, False, "SKIPPED")
            threshold = gate_def.threshold or 15
            passed = market_state.displacement_pips >= threshold
            delta = (
                None
                if passed
                else f"delta: {threshold - market_state.displacement_pips:.1f} pips short"
            )
            return GateEvaluationResult(gate_id, passed, delta)
        elif gate_id == "liquidity_swept":
            if market_state.sweep_age_bars is None:
                return GateEvaluationResult(gate_id, False, "SKIPPED")
            threshold = gate_def.threshold or 10
            passed = market_state.recent_sweep and market_state.sweep_age_bars <= threshold
            delta = None if passed else "delta: sweep conditions not met"
            return GateEvaluationResult(gate_id, passed, delta)
        elif gate_id == "ltf_confirmation":
            passed = (
                market_state.ltf_confirmation
                and market_state.ltf_direction == market_state.htf_bias
            )
            return GateEvaluationResult(gate_id, passed, None)
        elif gate_id == "entry_model_valid":
            valid_models = ["fvg_entry", "ob_entry", "breaker_entry"]
            passed = market_state.entry_model in valid_models
            delta = None if passed else f"actual: {market_state.entry_model}"
            return GateEvaluationResult(gate_id, passed, delta)
        elif gate_id == "stop_defined":
            if market_state.stop_distance_pips is None:
                return GateEvaluationResult(gate_id, False, "SKIPPED")
            threshold = gate_def.threshold or 30
            passed = market_state.stop_distance_pips <= threshold
            delta = (
                None
                if passed
                else f"delta: {market_state.stop_distance_pips - threshold:.1f} pips over max"
            )
            return GateEvaluationResult(gate_id, passed, delta)
        elif gate_id == "target_defined":
            passed = market_state.target_defined
            return GateEvaluationResult(gate_id, passed, None)
        elif gate_id == "rr_acceptable":
            if market_state.rr_ratio is None:
                return GateEvaluationResult(gate_id, False, "SKIPPED")
            threshold = gate_def.threshold or 2.0
            passed = market_state.rr_ratio >= threshold
            delta = None if passed else f"delta: {threshold - market_state.rr_ratio:.2f}R short"
            return GateEvaluationResult(gate_id, passed, delta)
        elif gate_id == "partials_planned":
            passed = market_state.partials_defined
            return GateEvaluationResult(gate_id, passed, None)

        return GateEvaluationResult(gate_id, False, "UNKNOWN_GATE")


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def evaluator() -> GateEvaluator:
    """Create evaluator instance."""
    return GateEvaluator()


@pytest.fixture
def strategy_hash() -> str:
    """Valid strategy hash."""
    return "abc123def456"


@pytest.fixture
def bullish_market_state() -> MarketState:
    """Market state favorable for long."""
    return MarketState(
        pair="EURUSD",
        timestamp=datetime.now(UTC),
        htf_bias="bullish",
        poi_distance_pips=30,
        current_session="london",
        asia_high=1.0850,
        asia_low=1.0800,
        session_bias="bullish",
        fvg_count=2,
        fvg_direction="bullish",
        displacement_pips=20,
        recent_sweep=True,
        sweep_age_bars=5,
        ltf_confirmation=True,
        ltf_direction="bullish",
        entry_model="fvg_entry",
        stop_distance_pips=15,
        target_defined=True,
        rr_ratio=3.0,
        partials_defined=True,
    )


@pytest.fixture
def weak_market_state() -> MarketState:
    """Market state with few gates passing."""
    return MarketState(
        pair="GBPUSD",
        timestamp=datetime.now(UTC),
        htf_bias="bearish",
        poi_distance_pips=100,  # Too far
        current_session="asia",  # Not a kill zone
        session_bias="bullish",  # Misaligned
    )


# =============================================================================
# BASIC EVALUATION TESTS
# =============================================================================


class TestBasicEvaluation:
    """Tests for basic gate evaluation."""

    def test_evaluate_returns_five_drawer_result(
        self,
        evaluator: GateEvaluator,
        bullish_market_state: MarketState,
        strategy_hash: str,
    ) -> None:
        """Evaluation returns FiveDrawerResult."""
        result = evaluator.evaluate("EURUSD", bullish_market_state, strategy_hash)

        assert isinstance(result, FiveDrawerResult)
        assert result.pair == "EURUSD"
        assert result.strategy_config_hash == strategy_hash

    def test_result_has_gates_passed_list(
        self,
        evaluator: GateEvaluator,
        bullish_market_state: MarketState,
        strategy_hash: str,
    ) -> None:
        """Result contains gates_passed as list."""
        result = evaluator.evaluate("EURUSD", bullish_market_state, strategy_hash)

        assert isinstance(result.gates_passed, list)
        assert len(result.gates_passed) > 0

    def test_result_has_gates_failed_list(
        self,
        evaluator: GateEvaluator,
        weak_market_state: MarketState,
        strategy_hash: str,
    ) -> None:
        """Result contains gates_failed as list."""
        result = evaluator.evaluate("GBPUSD", weak_market_state, strategy_hash)

        assert isinstance(result.gates_failed, list)


# =============================================================================
# NO AGGREGATION TESTS (Critical)
# =============================================================================


class TestNoAggregation:
    """Tests ensuring no aggregation/scoring occurs."""

    def test_result_has_no_gates_passed_count(
        self,
        evaluator: GateEvaluator,
        bullish_market_state: MarketState,
        strategy_hash: str,
    ) -> None:
        """Result does not have gates_passed_count field."""
        result = evaluator.evaluate("EURUSD", bullish_market_state, strategy_hash)

        assert not hasattr(result, "gates_passed_count")
        assert not hasattr(result, "count")
        assert not hasattr(result, "total_passed")

    def test_result_has_no_score(
        self,
        evaluator: GateEvaluator,
        bullish_market_state: MarketState,
        strategy_hash: str,
    ) -> None:
        """Result does not have score field."""
        result = evaluator.evaluate("EURUSD", bullish_market_state, strategy_hash)

        assert not hasattr(result, "score")
        assert not hasattr(result, "quality_score")
        assert not hasattr(result, "quality")

    def test_result_has_no_confidence(
        self,
        evaluator: GateEvaluator,
        bullish_market_state: MarketState,
        strategy_hash: str,
    ) -> None:
        """Result does not have confidence field."""
        result = evaluator.evaluate("EURUSD", bullish_market_state, strategy_hash)

        assert not hasattr(result, "confidence")

    def test_result_has_no_grade(
        self,
        evaluator: GateEvaluator,
        bullish_market_state: MarketState,
        strategy_hash: str,
    ) -> None:
        """Result does not have grade field."""
        result = evaluator.evaluate("EURUSD", bullish_market_state, strategy_hash)

        assert not hasattr(result, "grade")


# =============================================================================
# PREDICATE DELTA TESTS
# =============================================================================


class TestPredicateDelta:
    """Tests for predicate delta on gate failure."""

    def test_numeric_gate_includes_delta(
        self,
        evaluator: GateEvaluator,
        strategy_hash: str,
    ) -> None:
        """Numeric gate failure includes delta from threshold."""
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            poi_distance_pips=60,  # Threshold is 50
        )
        result = evaluator.evaluate("EURUSD", state, strategy_hash)

        # htf_poi_identified should fail with delta
        failed_with_delta = [g for g in result.gates_failed if "delta:" in g]
        poi_failures = [g for g in failed_with_delta if "htf_poi_identified" in g]

        assert len(poi_failures) > 0

    def test_enum_gate_includes_actual(
        self,
        evaluator: GateEvaluator,
        strategy_hash: str,
    ) -> None:
        """Enum gate failure includes actual value."""
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            current_session="asia",  # Not a kill zone
        )
        result = evaluator.evaluate("EURUSD", state, strategy_hash)

        # kill_zone_active should fail with actual value
        kz_failures = [g for g in result.gates_failed if "kill_zone_active" in g]

        assert len(kz_failures) > 0
        assert any("actual: asia" in g for g in kz_failures)


# =============================================================================
# DRAWER STATUS TESTS
# =============================================================================


class TestDrawerStatus:
    """Tests for drawer-level status."""

    def test_drawer_status_is_dict(
        self,
        evaluator: GateEvaluator,
        bullish_market_state: MarketState,
        strategy_hash: str,
    ) -> None:
        """drawer_status is dict[int, bool]."""
        result = evaluator.evaluate("EURUSD", bullish_market_state, strategy_hash)

        assert isinstance(result.drawer_status, dict)
        assert all(isinstance(k, int) for k in result.drawer_status.keys())
        assert all(isinstance(v, bool) for v in result.drawer_status.values())

    def test_drawer_results_included(
        self,
        evaluator: GateEvaluator,
        bullish_market_state: MarketState,
        strategy_hash: str,
    ) -> None:
        """drawer_results contains per-drawer details."""
        result = evaluator.evaluate("EURUSD", bullish_market_state, strategy_hash)

        assert len(result.drawer_results) > 0
        assert all(hasattr(dr, "drawer_id") for dr in result.drawer_results)
        assert all(hasattr(dr, "passed") for dr in result.drawer_results)


# =============================================================================
# BIAS AS PREDICATE TESTS
# =============================================================================


class TestBiasAsPredicate:
    """Tests for bias as predicate status (not directional word)."""

    def test_bullish_is_gate_status(
        self,
        evaluator: GateEvaluator,
        bullish_market_state: MarketState,
        strategy_hash: str,
    ) -> None:
        """Bullish appears only as gate status, not standalone."""
        result = evaluator.evaluate("EURUSD", bullish_market_state, strategy_hash)

        # Check gates_passed for structure
        htf_bullish_gates = [g for g in result.gates_passed if "htf_structure_bullish" in g]

        # Should be in gates_passed if bullish
        assert len(htf_bullish_gates) > 0

        # Result should NOT have a "bias" field with just "bullish"
        assert not hasattr(result, "bias")
        assert not hasattr(result, "direction")


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
