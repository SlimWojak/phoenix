"""
Gate Registry — DEPLOY.P0.2 Constitutional Truth Layer
======================================================

Maps cartridge gate IDs to predicate functions.
INV-GATE-NAMESPACE-SINGLETON: This is the ONLY module that defines or resolves gate IDs.

Both GateEvaluator AND CartridgeLoader import from here.
No other module defines gate predicates.

FORBIDDEN:
  - Scoring, grading, ranking
  - Composite scalars derived from gate booleans
  - Any logic beyond boolean predicate evaluation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from cso.drawer import (
    DrawerEvaluationResult,
    DrawerRuleType,
    GateEvaluationResult,
)

if TYPE_CHECKING:
    from cso.evaluator import MarketState


@dataclass(frozen=True)
class GateContext:
    """
    Runtime context for gates that need strategy-computed values.

    Populated by the orchestrator BEFORE CSO evaluation.
    Contains values that are computed from MarketState + strategy logic,
    not from enrichment alone.
    """

    rr_ratio: float | None = None
    session_can_trade: bool = True
    session_reject_reason: str | None = None


class GatePredicate(Protocol):
    """Predicate function: MarketState + optional context → (passed, delta)."""

    def __call__(
        self, state: MarketState, ctx: GateContext | None = None
    ) -> tuple[bool, str | None]:
        ...


@dataclass(frozen=True)
class GateRegistration:
    """Single gate registration in the registry."""

    gate_id: str
    predicate: GatePredicate
    drawer: int
    description: str = ""


@dataclass(frozen=True)
class DrawerSpec:
    """Drawer configuration for a strategy's gate set."""

    drawer_id: int
    name: str
    gate_ids: tuple[str, ...]
    rule: DrawerRuleType


@dataclass
class RegistryEvaluationResult:
    """Result of evaluating all gates via the registry."""

    gate_results: dict[str, GateEvaluationResult] = field(default_factory=dict)
    drawer_results: list[DrawerEvaluationResult] = field(default_factory=list)
    drawer_status: dict[int, bool] = field(default_factory=dict)
    gates_passed: list[str] = field(default_factory=list)
    gates_failed: list[str] = field(default_factory=list)


class GateRegistry:
    """
    Constitutional truth layer for gate resolution.

    INV-GATE-NAMESPACE-SINGLETON: Cartridge gate IDs are the ONLY gate namespace.
    The evaluator rejects any gate not registered here.
    """

    def __init__(self) -> None:
        self._gates: dict[str, GateRegistration] = {}
        self._drawers: list[DrawerSpec] = []

    def register(
        self,
        gate_id: str,
        predicate: GatePredicate,
        drawer: int,
        description: str = "",
    ) -> None:
        """Register a gate predicate."""
        self._gates[gate_id] = GateRegistration(
            gate_id=gate_id,
            predicate=predicate,
            drawer=drawer,
            description=description,
        )

    def set_drawer_specs(self, specs: list[DrawerSpec]) -> None:
        """Set drawer configuration for the strategy."""
        self._drawers = list(specs)

    def has_gate(self, gate_id: str) -> bool:
        return gate_id in self._gates

    @property
    def registered_gate_ids(self) -> list[str]:
        return list(self._gates.keys())

    @property
    def drawer_specs(self) -> list[DrawerSpec]:
        return list(self._drawers)

    def evaluate_gate(
        self,
        gate_id: str,
        state: MarketState,
        ctx: GateContext | None = None,
    ) -> GateEvaluationResult:
        """Evaluate a single gate. Fails if gate not registered."""
        reg = self._gates.get(gate_id)
        if reg is None:
            return GateEvaluationResult(gate_id, False, f"UNREGISTERED_GATE: {gate_id}")

        passed, delta = reg.predicate(state, ctx)
        return GateEvaluationResult(gate_id, passed, delta)

    def evaluate_all(
        self,
        gate_ids: list[str],
        state: MarketState,
        ctx: GateContext | None = None,
    ) -> RegistryEvaluationResult:
        """
        Evaluate a set of gates and compute drawer results.

        Args:
            gate_ids: Gate IDs from cartridge gate_requirements
            state: Current market state

        Returns:
            RegistryEvaluationResult with gate + drawer verdicts
        """
        result = RegistryEvaluationResult()

        for gate_id in gate_ids:
            gate_result = self.evaluate_gate(gate_id, state, ctx)
            result.gate_results[gate_id] = gate_result

            if gate_result.passed:
                result.gates_passed.append(gate_id)
            else:
                delta_str = (
                    f" [{gate_result.predicate_delta}]" if gate_result.predicate_delta else ""
                )
                result.gates_failed.append(f"{gate_id}{delta_str}")

        for spec in self._drawers:
            drawer_gate_results = {
                gid: result.gate_results[gid] for gid in spec.gate_ids if gid in result.gate_results
            }

            passed = _evaluate_drawer_rule(spec.rule, drawer_gate_results, list(spec.gate_ids))

            d_passed = [
                g
                for g in spec.gate_ids
                if drawer_gate_results.get(g, GateEvaluationResult(g, False)).passed
            ]
            d_failed = [
                g
                for g in spec.gate_ids
                if not drawer_gate_results.get(g, GateEvaluationResult(g, False)).passed
            ]

            result.drawer_status[spec.drawer_id] = passed
            result.drawer_results.append(
                DrawerEvaluationResult(
                    drawer_id=spec.drawer_id,
                    drawer_name=spec.name,
                    passed=passed,
                    gates_passed=list(d_passed),
                    gates_failed=list(d_failed),
                    gates_skipped=[],
                    rule_applied=spec.rule.value,
                )
            )

        return result


def _evaluate_drawer_rule(
    rule: DrawerRuleType,
    gate_results: dict[str, GateEvaluationResult],
    gate_ids: list[str],
) -> bool:
    """Evaluate drawer rule for registry-based evaluation."""
    if rule == DrawerRuleType.ALL_REQUIRED:
        return all(
            gate_results.get(gid, GateEvaluationResult(gid, False)).passed for gid in gate_ids
        )
    elif rule == DrawerRuleType.MINIMUM_2_OF_3:
        count = sum(
            1 for gid in gate_ids if gate_results.get(gid, GateEvaluationResult(gid, False)).passed
        )
        return count >= 2
    elif rule == DrawerRuleType.ALL_GATES_INDEPENDENT:
        return True
    elif rule == DrawerRuleType.AT_LEAST_ONE_DIRECTIONAL:
        return any(
            gate_results.get(gid, GateEvaluationResult(gid, False)).passed for gid in gate_ids
        )
    return False


# =============================================================================
# ARS PREDICATE FUNCTIONS
# =============================================================================


def _gate_asia_range_valid(
    state: MarketState, ctx: GateContext | None = None
) -> tuple[bool, str | None]:
    """Asia range defined and <= 30 pips."""
    if state.asia_range_pips is None:
        return False, "asia_range_pips is None"
    if state.asia_high is None or state.asia_low is None:
        return False, "asia_high/low is None"
    passed = state.asia_range_pips <= 30.0
    return passed, None if passed else f"range={state.asia_range_pips:.1f} > 30.0"


def _gate_liquidity_sweep_detected(
    state: MarketState, ctx: GateContext | None = None
) -> tuple[bool, str | None]:
    """Sweep of Asia boundary detected in window."""
    if not state.recent_sweep:
        return False, "no recent sweep"
    if state.sweep_age_bars is None:
        return False, "sweep_age_bars is None"
    return True, None


def _gate_sweep_extension_valid(
    state: MarketState, ctx: GateContext | None = None
) -> tuple[bool, str | None]:
    """Extension 1-20 pips inclusive."""
    ext = state.sweep_extension_pips
    if ext is None:
        return False, "sweep_extension_pips is None"
    passed = 1.0 <= ext <= 20.0
    return passed, None if passed else f"ext={ext:.1f} outside [1.0, 20.0]"


def _gate_ltf_pda_engaged(
    state: MarketState, ctx: GateContext | None = None
) -> tuple[bool, str | None]:
    """Re-acceptance: 5m close strictly inside range after sweep."""
    passed = state.re_acceptance is True
    return passed, None if passed else "re_acceptance not True"


def _gate_fvg_active(
    state: MarketState,
    ctx: GateContext | None = None,
) -> tuple[bool, str | None]:
    """FVG exists with untouched >= 1.0 pip."""
    fvg_present = state.fvg_bull_present or state.fvg_bear_present
    if not fvg_present:
        return False, "no FVG present"
    if state.fvg_untouched_pips is None:
        return False, "fvg_untouched_pips is None"
    passed = state.fvg_untouched_pips >= 1.0
    return passed, None if passed else f"gap={state.fvg_untouched_pips:.1f} < 1.0"


def _gate_candle_c_inside(
    state: MarketState, ctx: GateContext | None = None
) -> tuple[bool, str | None]:
    """Candle C close strictly inside Asia range."""
    passed = state.candle_c_inside_range is True
    return passed, None if passed else "candle C not inside range"


def _gate_rr_valid(
    state: MarketState,
    ctx: GateContext | None = None,
) -> tuple[bool, str | None]:
    """R:R >= 1.5 (from cartridge min_rr). Uses GateContext.rr_ratio if provided."""
    rr = ctx.rr_ratio if ctx is not None and ctx.rr_ratio is not None else state.rr_ratio
    if rr is None:
        return False, "rr_ratio not computed"
    passed = rr >= 1.5
    return passed, None if passed else f"rr={rr:.2f} < 1.5"


def _gate_session_limit(
    state: MarketState, ctx: GateContext | None = None
) -> tuple[bool, str | None]:
    """Max 1 trade/session, max 1 daily loss. Uses GateContext.session_can_trade."""
    if ctx is None:
        return False, "session_limit: no GateContext provided"
    if not ctx.session_can_trade:
        return False, ctx.session_reject_reason or "session limit reached"
    return True, None


# =============================================================================
# FACTORY: Build ARS Registry
# =============================================================================


ARS_DRAWER_SPECS = [
    DrawerSpec(
        drawer_id=1,
        name="HTF Bias",
        gate_ids=("GATE_ASIA_RANGE_VALID",),
        rule=DrawerRuleType.ALL_REQUIRED,
    ),
    DrawerSpec(
        drawer_id=2,
        name="Market Structure",
        gate_ids=("GATE_LIQUIDITY_SWEEP_DETECTED", "GATE_SWEEP_EXTENSION_VALID"),
        rule=DrawerRuleType.ALL_REQUIRED,
    ),
    DrawerSpec(
        drawer_id=3,
        name="Premium / Discount",
        gate_ids=("GATE_LTF_PDA_ENGAGED", "GATE_CANDLE_C_INSIDE"),
        rule=DrawerRuleType.ALL_REQUIRED,
    ),
    DrawerSpec(
        drawer_id=4,
        name="Entry Model",
        gate_ids=("GATE_FVG_ACTIVE",),
        rule=DrawerRuleType.ALL_REQUIRED,
    ),
    DrawerSpec(
        drawer_id=5,
        name="Confirmation",
        gate_ids=("GATE_RR_VALID", "GATE_SESSION_LIMIT"),
        rule=DrawerRuleType.ALL_REQUIRED,
    ),
]


def build_ars_registry() -> GateRegistry:
    """
    Build GateRegistry for Asia Range Scalp cartridge.

    Registers all 8 ARS gate predicates with drawer assignments.
    """
    registry = GateRegistry()

    registry.register(
        "GATE_ASIA_RANGE_VALID",
        _gate_asia_range_valid,
        drawer=1,
        description="Asia range defined and <= 30 pips",
    )
    registry.register(
        "GATE_LIQUIDITY_SWEEP_DETECTED",
        _gate_liquidity_sweep_detected,
        drawer=2,
        description="Sweep of Asia boundary detected",
    )
    registry.register(
        "GATE_SWEEP_EXTENSION_VALID",
        _gate_sweep_extension_valid,
        drawer=2,
        description="Sweep extension 1-20 pips inclusive",
    )
    registry.register(
        "GATE_LTF_PDA_ENGAGED",
        _gate_ltf_pda_engaged,
        drawer=3,
        description="Re-acceptance: close inside range after sweep",
    )
    registry.register(
        "GATE_FVG_ACTIVE",
        _gate_fvg_active,
        drawer=4,
        description="FVG present with >= 1.0 pip untouched",
    )
    registry.register(
        "GATE_CANDLE_C_INSIDE",
        _gate_candle_c_inside,
        drawer=3,
        description="Candle C close strictly inside Asia range",
    )
    registry.register(
        "GATE_RR_VALID", _gate_rr_valid, drawer=5, description="R:R >= cartridge min_rr (1.5)"
    )
    registry.register(
        "GATE_SESSION_LIMIT",
        _gate_session_limit,
        drawer=5,
        description="Session trade limit (1/session, 1 daily loss)",
    )

    registry.set_drawer_specs(ARS_DRAWER_SPECS)

    return registry


__all__ = [
    "GateContext",
    "GateRegistry",
    "GateRegistration",
    "GatePredicate",
    "DrawerSpec",
    "RegistryEvaluationResult",
    "build_ars_registry",
    "ARS_DRAWER_SPECS",
]
