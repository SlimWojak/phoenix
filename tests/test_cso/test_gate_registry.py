"""
Gate Registry Tests — DEPLOY.P0.2
==================================

Tests the GateRegistry constitutional truth layer.

EXIT GATES:
  1. GateRegistry loads ARS cartridge gates
  2. Evaluator resolves all 8 ARS gate IDs to predicates
  3. No UNKNOWN_GATE results
  4. Existing evaluator tests still pass (separate file)
"""

from datetime import UTC, datetime

import pytest

from cso.evaluator import FiveDrawerResult, GateEvaluator, MarketState
from cso.gate_registry import (
    GateContext,
    GateRegistry,
    build_ars_registry,
)

ARS_GATE_IDS = [
    "GATE_ASIA_RANGE_VALID",
    "GATE_LIQUIDITY_SWEEP_DETECTED",
    "GATE_SWEEP_EXTENSION_VALID",
    "GATE_LTF_PDA_ENGAGED",
    "GATE_FVG_ACTIVE",
    "GATE_CANDLE_C_INSIDE",
    "GATE_RR_VALID",
    "GATE_SESSION_LIMIT",
]


@pytest.fixture  # type: ignore[misc]
def registry() -> GateRegistry:
    return build_ars_registry()


@pytest.fixture  # type: ignore[misc]
def evaluator() -> GateEvaluator:
    return GateEvaluator()


@pytest.fixture  # type: ignore[misc]
def valid_ars_state() -> MarketState:
    """MarketState where all enrichment-derived ARS gates pass."""
    return MarketState(
        pair="EURUSD",
        timestamp=datetime.now(UTC),
        asia_high=1.0850,
        asia_low=1.0820,
        asia_range_pips=30.0,
        asia_range_valid=True,
        recent_sweep=True,
        sweep_age_bars=3,
        sweep_direction="bullish",
        sweep_extension_pips=5.0,
        sweep_target_type="asia_low",
        re_acceptance=True,
        fvg_bull_present=True,
        fvg_bear_present=False,
        fvg_untouched_pips=2.5,
        candle_c_inside_range=True,
        rr_ratio=2.0,
    )


@pytest.fixture  # type: ignore[misc]
def invalid_ars_state() -> MarketState:
    """MarketState where most ARS gates fail."""
    return MarketState(
        pair="EURUSD",
        timestamp=datetime.now(UTC),
        asia_high=None,
        asia_low=None,
        asia_range_pips=None,
    )


# =============================================================================
# EXIT GATE 1: GateRegistry loads ARS cartridge gates
# =============================================================================


class TestRegistryLoadsARSGates:
    def test_all_8_gates_registered(self, registry: GateRegistry) -> None:
        for gate_id in ARS_GATE_IDS:
            assert registry.has_gate(gate_id), f"{gate_id} not registered"

    def test_exactly_8_gates(self, registry: GateRegistry) -> None:
        assert len(registry.registered_gate_ids) == 8

    def test_registered_ids_match_cartridge(self, registry: GateRegistry) -> None:
        assert set(registry.registered_gate_ids) == set(ARS_GATE_IDS)

    def test_5_drawers_configured(self, registry: GateRegistry) -> None:
        assert len(registry.drawer_specs) == 5

    def test_drawer_ids_1_through_5(self, registry: GateRegistry) -> None:
        drawer_ids = {s.drawer_id for s in registry.drawer_specs}
        assert drawer_ids == {1, 2, 3, 4, 5}

    def test_all_gates_assigned_to_drawers(self, registry: GateRegistry) -> None:
        assigned_gates: set[str] = set()
        for spec in registry.drawer_specs:
            assigned_gates.update(spec.gate_ids)
        assert assigned_gates == set(ARS_GATE_IDS)


# =============================================================================
# EXIT GATE 2: Evaluator resolves all 8 ARS gate IDs to predicates
# =============================================================================


class TestEvaluatorResolvesGates:
    def test_evaluate_all_returns_results_for_all_gates(
        self,
        registry: GateRegistry,
        valid_ars_state: MarketState,
    ) -> None:
        result = registry.evaluate_all(ARS_GATE_IDS, valid_ars_state)
        assert len(result.gate_results) == 8

    def test_evaluate_with_registry_returns_five_drawer_result(
        self,
        evaluator: GateEvaluator,
        registry: GateRegistry,
        valid_ars_state: MarketState,
    ) -> None:
        result = evaluator.evaluate_with_registry(
            "EURUSD",
            valid_ars_state,
            "test_hash",
            registry,
            ARS_GATE_IDS,
        )
        assert isinstance(result, FiveDrawerResult)
        assert result.pair == "EURUSD"

    def test_evaluate_with_registry_has_drawer_results(
        self,
        evaluator: GateEvaluator,
        registry: GateRegistry,
        valid_ars_state: MarketState,
    ) -> None:
        result = evaluator.evaluate_with_registry(
            "EURUSD",
            valid_ars_state,
            "test_hash",
            registry,
            ARS_GATE_IDS,
        )
        assert len(result.drawer_results) == 5


# =============================================================================
# EXIT GATE 3: No UNKNOWN_GATE results
# =============================================================================


class TestNoUnknownGate:
    def test_no_unknown_gate_on_valid_state(
        self,
        registry: GateRegistry,
        valid_ars_state: MarketState,
    ) -> None:
        result = registry.evaluate_all(ARS_GATE_IDS, valid_ars_state)
        for gate_id, gate_result in result.gate_results.items():
            assert gate_result.predicate_delta != "UNKNOWN_GATE", f"{gate_id} returned UNKNOWN_GATE"

    def test_no_unknown_gate_on_invalid_state(
        self,
        registry: GateRegistry,
        invalid_ars_state: MarketState,
    ) -> None:
        result = registry.evaluate_all(ARS_GATE_IDS, invalid_ars_state)
        for gate_id, gate_result in result.gate_results.items():
            assert gate_result.predicate_delta != "UNKNOWN_GATE", f"{gate_id} returned UNKNOWN_GATE"

    def test_unregistered_gate_returns_unregistered(
        self,
        registry: GateRegistry,
        valid_ars_state: MarketState,
    ) -> None:
        result = registry.evaluate_gate("NONEXISTENT_GATE", valid_ars_state)
        assert not result.passed
        assert "UNREGISTERED_GATE" in (result.predicate_delta or "")

    def test_evaluator_with_registry_no_unknown(
        self,
        evaluator: GateEvaluator,
        registry: GateRegistry,
        valid_ars_state: MarketState,
    ) -> None:
        result = evaluator.evaluate_with_registry(
            "EURUSD",
            valid_ars_state,
            "test_hash",
            registry,
            ARS_GATE_IDS,
        )
        for gate in result.gates_failed:
            assert "UNKNOWN_GATE" not in gate


# =============================================================================
# PREDICATE LOGIC TESTS
# =============================================================================


class TestARSPredicates:
    def test_asia_range_valid_passes(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            asia_high=1.0850,
            asia_low=1.0820,
            asia_range_pips=30.0,
        )
        result = registry.evaluate_gate("GATE_ASIA_RANGE_VALID", state)
        assert result.passed

    def test_asia_range_too_wide_fails(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            asia_high=1.0850,
            asia_low=1.0800,
            asia_range_pips=50.0,
        )
        result = registry.evaluate_gate("GATE_ASIA_RANGE_VALID", state)
        assert not result.passed
        assert "50.0" in (result.predicate_delta or "")

    def test_asia_range_none_fails(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        result = registry.evaluate_gate("GATE_ASIA_RANGE_VALID", state)
        assert not result.passed

    def test_sweep_detected_passes(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            recent_sweep=True,
            sweep_age_bars=5,
        )
        result = registry.evaluate_gate("GATE_LIQUIDITY_SWEEP_DETECTED", state)
        assert result.passed

    def test_no_sweep_fails(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC), recent_sweep=False)
        result = registry.evaluate_gate("GATE_LIQUIDITY_SWEEP_DETECTED", state)
        assert not result.passed

    def test_extension_valid_passes(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            sweep_extension_pips=10.0,
        )
        result = registry.evaluate_gate("GATE_SWEEP_EXTENSION_VALID", state)
        assert result.passed

    def test_extension_too_small_fails(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            sweep_extension_pips=0.5,
        )
        result = registry.evaluate_gate("GATE_SWEEP_EXTENSION_VALID", state)
        assert not result.passed

    def test_extension_too_large_fails(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            sweep_extension_pips=25.0,
        )
        result = registry.evaluate_gate("GATE_SWEEP_EXTENSION_VALID", state)
        assert not result.passed

    def test_re_acceptance_passes(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            re_acceptance=True,
        )
        result = registry.evaluate_gate("GATE_LTF_PDA_ENGAGED", state)
        assert result.passed

    def test_re_acceptance_false_fails(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            re_acceptance=False,
        )
        result = registry.evaluate_gate("GATE_LTF_PDA_ENGAGED", state)
        assert not result.passed

    def test_fvg_active_passes(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            fvg_bull_present=True,
            fvg_untouched_pips=2.0,
        )
        result = registry.evaluate_gate("GATE_FVG_ACTIVE", state)
        assert result.passed

    def test_fvg_too_small_fails(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            fvg_bull_present=True,
            fvg_untouched_pips=0.5,
        )
        result = registry.evaluate_gate("GATE_FVG_ACTIVE", state)
        assert not result.passed

    def test_no_fvg_fails(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        result = registry.evaluate_gate("GATE_FVG_ACTIVE", state)
        assert not result.passed

    def test_candle_c_inside_passes(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            candle_c_inside_range=True,
        )
        result = registry.evaluate_gate("GATE_CANDLE_C_INSIDE", state)
        assert result.passed

    def test_candle_c_outside_fails(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            candle_c_inside_range=False,
        )
        result = registry.evaluate_gate("GATE_CANDLE_C_INSIDE", state)
        assert not result.passed

    def test_rr_valid_passes_via_context(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        ctx = GateContext(rr_ratio=2.0)
        result = registry.evaluate_gate("GATE_RR_VALID", state, ctx)
        assert result.passed

    def test_rr_valid_passes_via_market_state(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC), rr_ratio=2.0)
        result = registry.evaluate_gate("GATE_RR_VALID", state)
        assert result.passed

    def test_rr_context_overrides_market_state(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC), rr_ratio=0.5)
        ctx = GateContext(rr_ratio=2.0)
        result = registry.evaluate_gate("GATE_RR_VALID", state, ctx)
        assert result.passed

    def test_rr_insufficient_fails(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        ctx = GateContext(rr_ratio=1.0)
        result = registry.evaluate_gate("GATE_RR_VALID", state, ctx)
        assert not result.passed

    def test_rr_none_fails(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        result = registry.evaluate_gate("GATE_RR_VALID", state)
        assert not result.passed

    def test_session_limit_passes_with_context(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        ctx = GateContext(session_can_trade=True)
        result = registry.evaluate_gate("GATE_SESSION_LIMIT", state, ctx)
        assert result.passed

    def test_session_limit_fails_when_blocked(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        ctx = GateContext(session_can_trade=False, session_reject_reason="daily_loss_limit: 1/1")
        result = registry.evaluate_gate("GATE_SESSION_LIMIT", state, ctx)
        assert not result.passed
        assert "daily_loss_limit" in (result.predicate_delta or "")

    def test_session_limit_fails_without_context(self, registry: GateRegistry) -> None:
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        result = registry.evaluate_gate("GATE_SESSION_LIMIT", state)
        assert not result.passed


# =============================================================================
# DRAWER EVALUATION TESTS
# =============================================================================


class TestDrawerEvaluation:
    def test_drawers_1_4_pass_without_context(
        self,
        registry: GateRegistry,
        valid_ars_state: MarketState,
    ) -> None:
        """Drawers 1-4 pass with valid enrichment data. D5 fails without context."""
        result = registry.evaluate_all(ARS_GATE_IDS, valid_ars_state)
        assert result.drawer_status.get(1) is True
        assert result.drawer_status.get(2) is True
        assert result.drawer_status.get(3) is True
        assert result.drawer_status.get(4) is True
        assert result.drawer_status.get(5) is False  # No context for session_limit

    def test_all_5_drawers_pass_with_context(
        self,
        registry: GateRegistry,
        valid_ars_state: MarketState,
    ) -> None:
        """All 5 drawers pass when GateContext provides rr_ratio and session_can_trade."""
        ctx = GateContext(rr_ratio=2.0, session_can_trade=True)
        result = registry.evaluate_all(ARS_GATE_IDS, valid_ars_state, ctx)
        for drawer_id in range(1, 6):
            assert result.drawer_status.get(drawer_id) is True, f"Drawer {drawer_id} failed"

    def test_all_drawers_fail_with_empty_state(
        self,
        registry: GateRegistry,
        invalid_ars_state: MarketState,
    ) -> None:
        result = registry.evaluate_all(ARS_GATE_IDS, invalid_ars_state)
        for drawer_id in range(1, 6):
            assert result.drawer_status.get(drawer_id) is False

    def test_drawer_1_requires_range_valid(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            asia_high=1.0850,
            asia_low=1.0800,
            asia_range_pips=50.0,
        )
        result = registry.evaluate_all(ARS_GATE_IDS, state)
        assert result.drawer_status.get(1) is False

    def test_drawer_2_requires_both_sweep_gates(self, registry: GateRegistry) -> None:
        state = MarketState(
            pair="EURUSD",
            timestamp=datetime.now(UTC),
            recent_sweep=True,
            sweep_age_bars=3,
            sweep_extension_pips=0.5,
        )
        result = registry.evaluate_all(ARS_GATE_IDS, state)
        assert result.drawer_status.get(2) is False


# =============================================================================
# INVARIANT TESTS
# =============================================================================


class TestInvariants:
    def test_inv_gate_namespace_singleton(self, registry: GateRegistry) -> None:
        """INV-GATE-NAMESPACE-SINGLETON: Registry is sole authority."""
        assert registry.has_gate("GATE_ASIA_RANGE_VALID")
        assert not registry.has_gate("htf_structure_bullish")
        assert not registry.has_gate("fvg_present")

    def test_no_forbidden_fields_in_result(
        self,
        registry: GateRegistry,
        valid_ars_state: MarketState,
    ) -> None:
        result = registry.evaluate_all(ARS_GATE_IDS, valid_ars_state)
        assert not hasattr(result, "score")
        assert not hasattr(result, "confidence")
        assert not hasattr(result, "grade")

    def test_market_state_hash_deterministic(
        self,
        evaluator: GateEvaluator,
        registry: GateRegistry,
        valid_ars_state: MarketState,
    ) -> None:
        r1 = evaluator.evaluate_with_registry(
            "EURUSD",
            valid_ars_state,
            "hash1",
            registry,
            ARS_GATE_IDS,
        )
        r2 = evaluator.evaluate_with_registry(
            "EURUSD",
            valid_ars_state,
            "hash1",
            registry,
            ARS_GATE_IDS,
        )
        assert r1.market_state_hash == r2.market_state_hash
