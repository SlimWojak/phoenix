"""
P2.2 HTF Scaffold + P2.4 Graduation Tests
==========================================

P2.2: HTF directional gates registered, stubs reject with calibration message.
P2.4: Graduation ceremony, shadow callable, check_graduation_ready().
"""

from __future__ import annotations

from datetime import UTC, datetime

from cso.evaluator import MarketState
from cso.gate_registry import (
    HTF_GATE_IDS,
    GateContext,
    build_htf_registry,
)
from daemons.strategy_orchestrator import (
    OrchestratorConfig,
    StrategyOrchestrator,
)
from governance.graduation import (
    GraduationRequirements,
    check_graduation_ready,
)

# =============================================================================
# P2.2: HTF DIRECTIONAL SCAFFOLD
# =============================================================================


class TestHTFScaffold:
    def test_all_6_htf_gates_registered(self) -> None:
        registry = build_htf_registry()
        for gate_id in HTF_GATE_IDS:
            assert registry.has_gate(gate_id), f"{gate_id} not registered"

    def test_no_unknown_gate(self) -> None:
        registry = build_htf_registry()
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        for gate_id in HTF_GATE_IDS:
            result = registry.evaluate_gate(gate_id, state)
            assert "UNREGISTERED" not in (result.predicate_delta or "")

    def test_stubs_reject_with_calibration_message(self) -> None:
        registry = build_htf_registry()
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        stub_gates = [g for g in HTF_GATE_IDS if g != "GATE_RR_VALID"]
        for gate_id in stub_gates:
            result = registry.evaluate_gate(gate_id, state)
            assert not result.passed
            assert "Olya calibration" in (result.predicate_delta or "")

    def test_htf_eval_produces_friction_path(self) -> None:
        """Signal through HTF path → all stubs fail → rejection expected."""
        registry = build_htf_registry()
        state = MarketState(pair="EURUSD", timestamp=datetime.now(UTC))
        ctx = GateContext(rr_ratio=3.0, session_can_trade=True)
        result = registry.evaluate_all(HTF_GATE_IDS, state, ctx)
        all_pass = all(result.drawer_status.values())
        assert not all_pass

    def test_5_drawers_configured(self) -> None:
        registry = build_htf_registry()
        assert len(registry.drawer_specs) == 5
        drawer_ids = {s.drawer_id for s in registry.drawer_specs}
        assert drawer_ids == {1, 2, 3, 4, 5}


# =============================================================================
# P2.4: GRADUATION CEREMONY
# =============================================================================


class TestGraduation:
    def test_not_enough_days(self) -> None:
        ready, blockers = check_graduation_ready(
            observation_count=10,
            days_active=3,
        )
        assert not ready
        assert any("days_active" in b for b in blockers)

    def test_not_enough_signals(self) -> None:
        ready, blockers = check_graduation_ready(
            observation_count=1,
            days_active=10,
        )
        assert not ready
        assert any("observations" in b for b in blockers)

    def test_no_cso_signoff(self) -> None:
        ready, blockers = check_graduation_ready(
            observation_count=10,
            days_active=10,
            has_cso_signoff=False,
        )
        assert not ready
        assert any("Olya" in b for b in blockers)

    def test_no_g_approval(self) -> None:
        ready, blockers = check_graduation_ready(
            observation_count=10,
            days_active=10,
            has_cso_signoff=True,
            has_g_approval=False,
        )
        assert not ready
        assert any("G approval" in b for b in blockers)

    def test_all_requirements_met(self) -> None:
        ready, blockers = check_graduation_ready(
            observation_count=10,
            days_active=10,
            has_cso_signoff=True,
            has_g_approval=True,
            has_dream_cycle_summary=True,
        )
        assert ready
        assert blockers == []

    def test_custom_requirements(self) -> None:
        reqs = GraduationRequirements(
            min_shadow_days=3,
            min_shadow_signals=2,
            requires_cso_signoff=False,
            requires_g_approval=False,
            requires_dream_cycle_summary=False,
        )
        ready, blockers = check_graduation_ready(
            observation_count=2,
            days_active=3,
            requirements=reqs,
        )
        assert ready


# =============================================================================
# P2.4: SHADOW CALLABLE IN ORCHESTRATOR
# =============================================================================


class TestShadowCallable:
    def test_shadow_fn_overrides_config(self) -> None:
        config = OrchestratorConfig(
            shadow_mode=True,
            is_shadow_fn=lambda: False,
        )
        orch = StrategyOrchestrator(config)
        assert not orch._is_shadow()

    def test_no_shadow_fn_uses_config(self) -> None:
        config = OrchestratorConfig(shadow_mode=True)
        orch = StrategyOrchestrator(config)
        assert orch._is_shadow()

    def test_shadow_fn_false_allows_execution(self) -> None:
        config = OrchestratorConfig(
            shadow_mode=True,
            is_shadow_fn=lambda: False,
        )
        orch = StrategyOrchestrator(config)
        assert not orch._is_shadow()

    def test_default_is_shadow(self) -> None:
        """Safe default: shadow mode is True."""
        orch = StrategyOrchestrator()
        assert orch._is_shadow()
