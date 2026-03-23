"""
Strategy Orchestrator — DEPLOY.P1.3
====================================

Full constitutional chain: River → enrichment → MarketState → CSO → intent → broker.

10-step flow per bar:
  1. PRE-FLIGHT  — gateway, river, enrichment, halt
  2. WATCH       — new bar detection
  3. ENRICH      — L1→L7 enrichment
  4. BUILD STATE — build_market_state (INV-PIT-JOIN-ONLY)
  5. BARRIER     — hydration check (INV-RACE-BAR-SYNC)
  6. EVALUATE    — GateRegistry 5-drawer evaluation
  7. PROPOSE     — TradeProposal from strategy computation
  8. ADAPT       — TradeProposal → ExecutionIntent
  9. GOVERN      — halt, shadow, lease checks
  10. EXECUTE    — broker submit or ShadowObservation

INVARIANTS:
  INV-PRE-FLIGHT-HEARTBEAT: halt if gateway/river/enrichment unhealthy
  INV-RACE-BAR-SYNC: enrichment watermark >= current bar
  INV-SHADOW-MODE-RESPECTED: shadow=True → observe only
  INV-GOV-HALT-BEFORE-ACTION: halt check before any intent creation
  INV-NO-PARALLEL-EVAL-PATHS: only GateRegistry path, no bypass
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import pandas as pd

from cso.evaluator import FiveDrawerResult, GateEvaluator, MarketState
from cso.gate_registry import GateContext, build_ars_registry
from cso.market_state_builder import (
    RiverStalenessError,
    build_market_state,
)
from execution.asia_scalp import (
    SessionTracker,
    SetupVerdict,
    TradeProposal,
    evaluate_asia_scalp_setup,
    make_session_id,
)
from execution.intent import ExecutionIntent, IntentFactory
from execution.intent_adapter import adapt_proposal_to_intent

logger = logging.getLogger(__name__)

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

SL_BUFFER = 0.00005
PIP = 0.0001


class BarOutcome(str, Enum):
    NO_SETUP = "NO_SETUP"
    SETUP_REJECTED = "SETUP_REJECTED"
    SHADOW_OBSERVATION = "SHADOW_OBSERVATION"
    INTENT_CREATED = "INTENT_CREATED"
    HALT_BLOCKED = "HALT_BLOCKED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ShadowObservation:
    """Record of a trade that would have executed if shadow_mode=False."""

    timestamp: datetime
    pair: str
    proposal: TradeProposal
    intent: ExecutionIntent
    market_state_hash: str
    five_drawer_result: FiveDrawerResult
    reason: str = "shadow_mode=True"


@dataclass(frozen=True)
class PreFlightResult:
    healthy: bool
    checks: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class BarProcessingResult:
    """Result of processing a single bar through the constitutional chain."""

    timestamp: datetime
    pair: str
    outcome: BarOutcome
    market_state: MarketState | None = None
    five_drawer: FiveDrawerResult | None = None
    proposal: TradeProposal | None = None
    intent: ExecutionIntent | None = None
    shadow_observation: ShadowObservation | None = None
    rejection_reason: str | None = None
    error: str | None = None


@dataclass
class OrchestratorConfig:
    pair: str = "EURUSD"
    shadow_mode: bool = True
    cartridge_hash: str = "ARS_v2.0.0"
    halt_check_fn: Any | None = None
    account_equity: float = 10000.0
    pip_value: float = 10.0


class StrategyOrchestrator:
    """
    Constitutional strategy execution chain.

    INV-NO-PARALLEL-EVAL-PATHS: All evaluation through GateRegistry only.
    """

    def __init__(self, config: OrchestratorConfig | None = None) -> None:
        self._config = config or OrchestratorConfig()
        self._registry = build_ars_registry()
        self._evaluator = GateEvaluator()
        self._intent_factory = IntentFactory(source_module="ARS")
        self._session_tracker = SessionTracker()
        self._observations: list[ShadowObservation] = []

    @property
    def shadow_observations(self) -> list[ShadowObservation]:
        return list(self._observations)

    def pre_flight(self) -> PreFlightResult:
        """
        Step 1: PRE-FLIGHT HEARTBEAT.

        INV-PRE-FLIGHT-HEARTBEAT: halt if any component unhealthy.
        """
        checks: dict[str, bool] = {}
        errors: list[str] = []

        try:
            import enrichment  # noqa: F401

            checks["enrichment_importable"] = True
        except ImportError as e:
            checks["enrichment_importable"] = False
            errors.append(f"enrichment import failed: {e}")

        if self._config.halt_check_fn is not None:
            try:
                halted = self._config.halt_check_fn()
                checks["halt_clear"] = not halted
                if halted:
                    errors.append("HALT signal active")
            except Exception as e:
                checks["halt_clear"] = False
                errors.append(f"halt check error: {e}")
        else:
            checks["halt_clear"] = True

        checks["registry_loaded"] = len(self._registry.registered_gate_ids) == 8

        healthy = all(checks.values())
        return PreFlightResult(healthy=healthy, checks=checks, errors=errors)

    def process_bar(
        self,
        df: pd.DataFrame,
        pair: str,
        now: datetime,
    ) -> BarProcessingResult:
        """
        Steps 3-10: Process enriched DataFrame through constitutional chain.

        Args:
            df: Enriched DataFrame (L1-L7 columns applied)
            pair: Trading pair
            now: Current wall-clock time (PIT boundary)

        Returns:
            BarProcessingResult with full provenance
        """
        # Step 4: BUILD STATE
        try:
            state, report = build_market_state(df, pair, now)
        except RiverStalenessError as e:
            return BarProcessingResult(
                timestamp=now,
                pair=pair,
                outcome=BarOutcome.ERROR,
                error=f"INV-RIVER-FRESHNESS: {e}",
            )

        if not report.valid:
            return BarProcessingResult(
                timestamp=now,
                pair=pair,
                outcome=BarOutcome.NO_SETUP,
                market_state=state,
                rejection_reason=f"invalid state: {state.invalid_reason}",
            )

        # Step 5: HYDRATION BARRIER (INV-RACE-BAR-SYNC)
        if state.evaluation_time is None:
            return BarProcessingResult(
                timestamp=now,
                pair=pair,
                outcome=BarOutcome.ERROR,
                market_state=state,
                error="hydration barrier: evaluation_time is None",
            )

        # Extract candle C close from PIT-filtered data
        candle_c_close = self._extract_candle_c_close(df, now)

        # Step 6+7: Strategy computation for price discovery + EVALUATE
        strategy_result = self._compute_strategy(state, pair, now, candle_c_close)
        if strategy_result is None:
            return BarProcessingResult(
                timestamp=now,
                pair=pair,
                outcome=BarOutcome.NO_SETUP,
                market_state=state,
                rejection_reason="strategy computation: insufficient data for price discovery",
            )

        oracle_result, gate_ctx = strategy_result

        five_drawer = self._evaluator.evaluate_with_registry(
            pair,
            state,
            self._config.cartridge_hash,
            self._registry,
            ARS_GATE_IDS,
            gate_ctx,
        )

        all_drawers_pass = all(five_drawer.drawer_status.values())

        if not all_drawers_pass:
            return BarProcessingResult(
                timestamp=now,
                pair=pair,
                outcome=BarOutcome.SETUP_REJECTED,
                market_state=state,
                five_drawer=five_drawer,
                rejection_reason=f"CSO rejected: {five_drawer.gates_failed}",
            )

        if oracle_result.verdict != SetupVerdict.VALID or oracle_result.proposal is None:
            return BarProcessingResult(
                timestamp=now,
                pair=pair,
                outcome=BarOutcome.SETUP_REJECTED,
                market_state=state,
                five_drawer=five_drawer,
                rejection_reason=(f"oracle rejected: {oracle_result.verdict.value}"),
            )

        proposal = oracle_result.proposal

        # Step 8: ADAPT → ExecutionIntent
        intent = adapt_proposal_to_intent(proposal, pair, state)

        # Step 9: GOVERN
        if self._config.halt_check_fn is not None:
            try:
                if self._config.halt_check_fn():
                    return BarProcessingResult(
                        timestamp=now,
                        pair=pair,
                        outcome=BarOutcome.HALT_BLOCKED,
                        market_state=state,
                        five_drawer=five_drawer,
                        proposal=proposal,
                        intent=intent,
                    )
            except Exception as e:
                return BarProcessingResult(
                    timestamp=now,
                    pair=pair,
                    outcome=BarOutcome.ERROR,
                    error=f"halt check failed: {e}",
                )

        if self._config.shadow_mode:
            obs = ShadowObservation(
                timestamp=now,
                pair=pair,
                proposal=proposal,
                intent=intent,
                market_state_hash=state.compute_hash(),
                five_drawer_result=five_drawer,
            )
            self._observations.append(obs)
            logger.info(
                "SHADOW_OBSERVATION: %s %s entry=%.5f sl=%.5f tp=%.5f rr=%.2f",
                pair,
                proposal.direction.value,
                proposal.entry_price,
                proposal.stop_loss,
                proposal.take_profit,
                proposal.rr_ratio,
            )
            return BarProcessingResult(
                timestamp=now,
                pair=pair,
                outcome=BarOutcome.SHADOW_OBSERVATION,
                market_state=state,
                five_drawer=five_drawer,
                proposal=proposal,
                intent=intent,
                shadow_observation=obs,
            )

        # Step 10: EXECUTE (only when shadow_mode=False)
        return BarProcessingResult(
            timestamp=now,
            pair=pair,
            outcome=BarOutcome.INTENT_CREATED,
            market_state=state,
            five_drawer=five_drawer,
            proposal=proposal,
            intent=intent,
        )

    def _compute_strategy(
        self,
        state: MarketState,
        pair: str,
        now: datetime,
        candle_c_close: float | None = None,
    ) -> tuple[Any, GateContext] | None:
        """
        Compute strategy fields: entry/SL/TP/RR + session state.

        Uses evaluate_asia_scalp_setup as the computation engine
        (price discovery), then builds GateContext from the result.
        """
        if state.asia_high is None or state.asia_low is None:
            return None

        sweep_extreme = self._reconstruct_sweep_extreme(state)
        if sweep_extreme is None:
            return None

        if candle_c_close is None:
            return None

        ny_time = now.strftime("%Y-%m-%d")
        session_id = make_session_id(ny_time)

        # Session check BEFORE oracle (oracle mutates tracker on VALID)
        can_trade, reason = self._session_tracker.can_trade(session_id)

        fvg_valid = state.fvg_bull_present or state.fvg_bear_present

        oracle_result = evaluate_asia_scalp_setup(
            asia_high=state.asia_high,
            asia_low=state.asia_low,
            asia_range_pips=state.asia_range_pips,
            sweep_direction=state.sweep_direction,
            sweep_extension_pips=state.sweep_extension_pips,
            sweep_extreme_price=sweep_extreme,
            re_acceptance=state.re_acceptance,
            fvg_valid=fvg_valid,
            fvg_untouched_pips=state.fvg_untouched_pips,
            candle_c_inside=state.candle_c_inside_range,
            candle_c_close=candle_c_close,
            session_id=session_id,
            account_equity=self._config.account_equity,
            tracker=self._session_tracker,
            pip_value=self._config.pip_value,
        )

        rr: float | None = None
        if oracle_result.proposal is not None:
            rr = oracle_result.proposal.rr_ratio

        ctx = GateContext(
            rr_ratio=rr,
            session_can_trade=can_trade,
            session_reject_reason=reason,
        )

        return oracle_result, ctx

    @staticmethod
    def _reconstruct_sweep_extreme(state: MarketState) -> float | None:
        """Reconstruct sweep_extreme_price from MarketState fields."""
        if state.sweep_extension_pips is None or state.sweep_direction is None:
            return None
        if state.asia_high is None or state.asia_low is None:
            return None

        if state.sweep_direction == "bullish":
            return state.asia_low - state.sweep_extension_pips * PIP
        elif state.sweep_direction == "bearish":
            return state.asia_high + state.sweep_extension_pips * PIP
        return None

    @staticmethod
    def _extract_candle_c_close(df: pd.DataFrame, now: datetime) -> float | None:
        """
        Extract candle C close from PIT-filtered DataFrame.

        This is the actual bar close, not reconstructed from MarketState.
        Required for accurate SL/TP/R:R computation.
        """
        if df.empty or "timestamp" not in df.columns or "close" not in df.columns:
            return None

        from cso.market_state_builder import _point_in_time_filter

        pit = _point_in_time_filter(df, now)
        if pit.empty:
            return None
        return float(pit["close"].iloc[-1])

    def replay_historical(
        self,
        df: pd.DataFrame,
        pair: str,
        bar_timestamps: list[datetime] | None = None,
    ) -> list[BarProcessingResult]:
        """
        Replay enriched bars through the constitutional chain.

        Args:
            df: Full enriched DataFrame
            pair: Trading pair
            bar_timestamps: Specific timestamps to evaluate at.
                           If None, uses all unique timestamps.

        Returns:
            List of BarProcessingResult for each evaluated bar
        """
        results: list[BarProcessingResult] = []

        if bar_timestamps is None:
            if "timestamp" not in df.columns:
                return results
            bar_timestamps = sorted(df["timestamp"].unique().tolist())

        for ts in bar_timestamps:
            if isinstance(ts, pd.Timestamp):
                now = ts.to_pydatetime()
            else:
                now = ts

            if now.tzinfo is None:
                now = now.replace(tzinfo=UTC)

            result = self.process_bar(df, pair, now)
            results.append(result)

        return results


__all__ = [
    "StrategyOrchestrator",
    "OrchestratorConfig",
    "BarProcessingResult",
    "BarOutcome",
    "ShadowObservation",
    "PreFlightResult",
]
