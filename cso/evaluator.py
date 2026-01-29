"""
Gate Evaluator — S36 Track B
============================

Evaluates gates against market state.
Returns boolean per gate. No interpretation. No synthesis.

INVARIANTS:
  - INV-HARNESS-1: Gate status only, never grades
  - INV-HARNESS-2: No confidence scores
  - INV-BIAS-PREDICATE: Bias as predicate status

FORBIDDEN:
  - popcount functions
  - sum of gates_passed
  - any scalar derived from gate booleans
  - len(gates_passed) in any computation
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from cso.drawer import (
    DrawerEvaluationResult,
    DrawerSchemaValidator,
    GateDefinition,
    GateEvaluationResult,
    evaluate_drawer_rule,
)

# =============================================================================
# CONSTANTS
# =============================================================================

CSO_ROOT = Path(__file__).parent
CONDITIONS_PATH = CSO_ROOT / "knowledge" / "conditions.yaml"


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class MarketState:
    """Snapshot of market state for evaluation."""

    pair: str
    timestamp: datetime
    htf_bias: str | None = None  # "bullish" | "bearish" | "neutral"
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
        """Compute hash of market state."""
        data = str(self.__dict__).encode("utf-8")
        return hashlib.sha256(data).hexdigest()


@dataclass
class FiveDrawerResult:
    """
    Result of 5-drawer evaluation.

    FORBIDDEN: Any count, sum, or scalar derivation.
    """

    pair: str
    timestamp: datetime
    gates_passed: list[str] = field(default_factory=list)
    gates_failed: list[str] = field(default_factory=list)
    gates_skipped: list[str] = field(default_factory=list)
    drawer_status: dict[int, bool] = field(default_factory=dict)
    drawer_results: list[DrawerEvaluationResult] = field(default_factory=list)
    strategy_config_hash: str = ""
    market_state_hash: str = ""

    # FORBIDDEN: Do not add any of these fields
    # - gates_passed_count
    # - score
    # - quality
    # - confidence
    # - grade


# =============================================================================
# GATE EVALUATOR
# =============================================================================


class GateEvaluator:
    """
    Evaluates gates against market state.

    Returns boolean per gate. No aggregation. No scoring.

    FORBIDDEN:
      - popcount
      - sum(gates_passed)
      - len(gates_passed)
      - Any scalar derived from booleans

    Usage:
        evaluator = GateEvaluator()
        result = evaluator.evaluate(pair, market_state, strategy_hash)
    """

    def __init__(self) -> None:
        """Initialize evaluator."""
        self._validator = DrawerSchemaValidator()
        self._conditions: dict[str, Any] | None = None

    def _load_conditions(self) -> dict[str, Any]:
        """Load conditions from YAML."""
        if self._conditions is not None:
            return self._conditions

        if CONDITIONS_PATH.exists():
            with open(CONDITIONS_PATH) as f:
                self._conditions = yaml.safe_load(f)
        else:
            self._conditions = {}

        return self._conditions

    def evaluate(
        self,
        pair: str,
        market_state: MarketState,
        strategy_config_hash: str,
    ) -> FiveDrawerResult:
        """
        Evaluate all gates for a pair.

        Args:
            pair: Trading pair
            market_state: Current market state
            strategy_config_hash: Strategy config hash

        Returns:
            FiveDrawerResult with gates_passed/failed lists

        NOTE: This method returns LISTS, not COUNTS.
        Any counting must happen in the human's head.
        """
        gate_results: dict[str, GateEvaluationResult] = {}
        gates_passed: list[str] = []
        gates_failed: list[str] = []
        gates_skipped: list[str] = []

        # Get gate definitions
        gate_defs = self._validator.get_gate_definitions()

        # Evaluate each gate
        for gate_id, gate_def in gate_defs.items():
            result = self._evaluate_gate(gate_def, market_state)
            gate_results[gate_id] = result

            if result.passed:
                gates_passed.append(gate_id)
            elif result.predicate_delta == "SKIPPED":
                gates_skipped.append(gate_id)
            else:
                # Include delta info in failed gate representation
                if result.predicate_delta:
                    gates_failed.append(f"{gate_id} [{result.predicate_delta}]")
                else:
                    gates_failed.append(gate_id)

        # Evaluate drawers
        drawer_defs = self._validator.get_drawer_definitions()
        drawer_status: dict[int, bool] = {}
        drawer_results: list[DrawerEvaluationResult] = []

        for drawer_id, drawer_def in drawer_defs.items():
            passed = evaluate_drawer_rule(
                drawer_def.rule,
                gate_results,
                drawer_def.gates,
            )
            drawer_status[drawer_id] = passed

            # Build drawer result
            drawer_gates_passed = [
                g
                for g in drawer_def.gates
                if gate_results.get(g, GateEvaluationResult(g, False)).passed
            ]
            drawer_gates_failed = [
                g
                for g in drawer_def.gates
                if not gate_results.get(g, GateEvaluationResult(g, False)).passed
                and gate_results.get(g, GateEvaluationResult(g, False)).predicate_delta != "SKIPPED"
            ]
            drawer_gates_skipped = [
                g
                for g in drawer_def.gates
                if gate_results.get(g, GateEvaluationResult(g, False)).predicate_delta == "SKIPPED"
            ]

            drawer_results.append(
                DrawerEvaluationResult(
                    drawer_id=drawer_id,
                    drawer_name=drawer_def.name,
                    passed=passed,
                    gates_passed=drawer_gates_passed,
                    gates_failed=drawer_gates_failed,
                    gates_skipped=drawer_gates_skipped,
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
        self,
        gate_def: GateDefinition,
        market_state: MarketState,
    ) -> GateEvaluationResult:
        """
        Evaluate a single gate.

        Returns boolean + predicate_delta on failure.
        """
        gate_id = gate_def.id

        # HTF Foundation Gates (Drawer 1)
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

        # Session Context Gates (Drawer 2)
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

        # Entry Conditions Gates (Drawer 3)
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
            delta = (
                None
                if passed
                else f"delta: {market_state.sweep_age_bars - threshold} bars over threshold"
            )
            return GateEvaluationResult(gate_id, passed, delta)

        # Entry Trigger Gates (Drawer 4)
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

        # Trade Management Gates (Drawer 5)
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

        # Unknown gate
        return GateEvaluationResult(gate_id, False, "UNKNOWN_GATE")


# =============================================================================
# FORBIDDEN OPERATIONS (for linting)
# =============================================================================

# These patterns should NEVER appear in evaluator code:
# - popcount
# - bin(x).count('1')
# - sum(1 for ...)
# - len([g for g in gates_passed])
# - gates_passed_count
# - quality_score
# - confidence
# - grade

# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "GateEvaluator",
    "FiveDrawerResult",
    "MarketState",
]
