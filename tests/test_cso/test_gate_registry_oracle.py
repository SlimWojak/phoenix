"""
Gate Registry Oracle Verification — DEPLOY.P1.1
=================================================

STRICT ASSERTION: GateRegistry verdict MUST match evaluate_asia_scalp_setup()
verdict for every test scenario. Any divergence → HALT BUILD.

The oracle (evaluate_asia_scalp_setup) is the regression reference.
The registry is the constitutional path. They must agree.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from cso.evaluator import MarketState
from cso.gate_registry import GateContext, build_ars_registry
from execution.asia_scalp import (
    SessionTracker,
    SetupVerdict,
    evaluate_asia_scalp_setup,
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

SL_BUFFER = 0.00005
PIP = 0.0001


def _oracle_kwargs(**overrides: object) -> dict[str, Any]:
    """Canonical valid ARS setup for oracle evaluation."""
    base: dict[str, Any] = {
        "asia_high": 1.0860,
        "asia_low": 1.0840,
        "asia_range_pips": 20.0,
        "sweep_direction": "bullish",
        "sweep_extension_pips": 8.0,
        "sweep_extreme_price": 1.0832,
        "re_acceptance": True,
        "fvg_valid": True,
        "fvg_untouched_pips": 2.0,
        "candle_c_inside": True,
        "candle_c_close": 1.0842,
        "session_id": "ASIA_2026-02-21",
        "account_equity": 10000.0,
        "tracker": SessionTracker(),
        "pip_value": 10.0,
    }
    base.update(overrides)
    return base


def _state_from_kwargs(kw: dict[str, Any]) -> MarketState:
    """Build MarketState mirroring the oracle kwargs."""
    direction = kw.get("sweep_direction")
    fvg_valid = kw.get("fvg_valid", False)
    fvg_bull = fvg_valid and direction == "bullish"
    fvg_bear = fvg_valid and direction == "bearish"

    return MarketState(
        pair="EURUSD",
        timestamp=datetime.now(UTC),
        asia_high=kw.get("asia_high"),
        asia_low=kw.get("asia_low"),
        asia_range_pips=kw.get("asia_range_pips"),
        asia_range_valid=(kw.get("asia_range_pips") is not None and kw["asia_range_pips"] <= 30.0),
        recent_sweep=kw.get("sweep_direction") is not None,
        sweep_age_bars=3 if kw.get("sweep_direction") else None,
        sweep_direction=kw.get("sweep_direction"),
        sweep_extension_pips=kw.get("sweep_extension_pips"),
        sweep_target_type=(
            "asia_low"
            if direction == "bullish"
            else "asia_high"
            if direction == "bearish"
            else None
        ),
        re_acceptance=kw.get("re_acceptance"),
        fvg_bull_present=fvg_bull,
        fvg_bear_present=fvg_bear,
        fvg_untouched_pips=kw.get("fvg_untouched_pips"),
        candle_c_inside_range=kw.get("candle_c_inside"),
    )


def _context_from_oracle(kw: dict[str, Any]) -> GateContext:
    """Build GateContext from oracle kwargs (simulating runtime computation)."""
    tracker: SessionTracker = kw["tracker"]
    session_id: str = kw["session_id"]
    can_trade, reason = tracker.can_trade(session_id)

    rr: float | None = None
    asia_high = kw.get("asia_high")
    asia_low = kw.get("asia_low")
    extreme = kw.get("sweep_extreme_price")
    close = kw.get("candle_c_close")
    direction = kw.get("sweep_direction")

    if all(v is not None for v in [asia_high, asia_low, extreme, close, direction]):
        assert asia_high is not None and asia_low is not None
        assert extreme is not None and close is not None
        _ah = float(asia_high)
        _al = float(asia_low)
        _ex = float(extreme)
        _cl = float(close)
        if direction == "bullish":
            sl = _ex - SL_BUFFER
            tp = _ah
        else:
            sl = _ex + SL_BUFFER
            tp = _al
        risk = abs(_cl - sl)
        reward = abs(tp - _cl)
        if risk > 0:
            rr = reward / risk

    return GateContext(
        rr_ratio=rr,
        session_can_trade=can_trade,
        session_reject_reason=reason,
    )


def _run_oracle(kw: dict[str, Any]) -> SetupVerdict:
    """Run the oracle (evaluate_asia_scalp_setup) and return verdict."""
    return evaluate_asia_scalp_setup(**kw).verdict


def _run_registry(state: MarketState, ctx: GateContext) -> bool:
    """Run the GateRegistry path and return True if all gates pass."""
    registry = build_ars_registry()
    result = registry.evaluate_all(ARS_GATE_IDS, state, ctx)
    return all(result.gate_results[gid].passed for gid in ARS_GATE_IDS)


def _assert_verdict_match(
    kw: dict[str, Any],
    label: str,
) -> None:
    """
    STRICT ASSERTION: oracle and registry must agree on verdict.

    If oracle says VALID → registry must have all gates pass.
    If oracle says REJECTED → registry must have at least one gate fail.

    Context is computed from a FRESH tracker clone to avoid mutation
    interference with the oracle's tracker (can_trade mutates state).
    """
    state = _state_from_kwargs(kw)

    ctx_kw: dict[str, Any] = dict(kw)
    original_tracker: SessionTracker = kw["tracker"]
    ctx_tracker = SessionTracker(
        trades_this_session=original_tracker.trades_this_session,
        daily_losses=original_tracker.daily_losses,
        current_session_id=original_tracker.current_session_id,
    )
    ctx_kw["tracker"] = ctx_tracker
    ctx = _context_from_oracle(ctx_kw)

    oracle_verdict = _run_oracle(kw)
    registry_all_pass = _run_registry(state, ctx)

    oracle_valid = oracle_verdict == SetupVerdict.VALID
    assert oracle_valid == registry_all_pass, (
        f"ORACLE DIVERGENCE [{label}]: "
        f"oracle={oracle_verdict.value}, "
        f"registry_all_pass={registry_all_pass}"
    )


# =============================================================================
# P1.1 ORACLE VERIFICATION: VALID TRADES
# =============================================================================


class TestOracleValidTrades:
    """Oracle and registry agree: these trades are VALID."""

    def test_canonical_bullish(self) -> None:
        _assert_verdict_match(_oracle_kwargs(), "canonical_bullish")

    def test_canonical_bearish(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(
                sweep_direction="bearish",
                sweep_extreme_price=1.0868,
                candle_c_close=1.0858,
            ),
            "canonical_bearish",
        )

    def test_min_extension(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(sweep_extension_pips=1.0),
            "min_extension",
        )

    def test_max_extension(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(sweep_extension_pips=20.0, sweep_extreme_price=1.0820),
            "max_extension",
        )

    def test_tight_range(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(
                asia_range_pips=10.0,
                asia_high=1.0855,
                asia_low=1.0845,
                candle_c_close=1.0848,
            ),
            "tight_range",
        )

    def test_max_range_boundary(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(asia_range_pips=30.0),
            "max_range_boundary",
        )


# =============================================================================
# P1.1 ORACLE VERIFICATION: REJECTED TRADES
# =============================================================================


class TestOracleRejectedTrades:
    """Oracle and registry agree: these trades are REJECTED."""

    def test_range_too_wide(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(asia_range_pips=35.0),
            "range_too_wide",
        )

    def test_no_sweep(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(
                sweep_direction=None,
                sweep_extension_pips=None,
            ),
            "no_sweep",
        )

    def test_extension_too_small(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(sweep_extension_pips=0.5),
            "extension_too_small",
        )

    def test_extension_too_large(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(sweep_extension_pips=25.0),
            "extension_too_large",
        )

    def test_no_re_acceptance(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(re_acceptance=False),
            "no_re_acceptance",
        )

    def test_no_fvg(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(fvg_valid=False),
            "no_fvg",
        )

    def test_fvg_too_small(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(fvg_untouched_pips=0.8),
            "fvg_too_small",
        )

    def test_candle_not_inside(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(candle_c_inside=False),
            "candle_not_inside",
        )

    def test_rr_insufficient(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(
                candle_c_close=1.0855,
                sweep_extreme_price=1.0825,
            ),
            "rr_insufficient",
        )

    def test_session_limit(self) -> None:
        tracker = SessionTracker()
        tracker.current_session_id = "ASIA_2026-02-21"
        tracker.trades_this_session = 1
        _assert_verdict_match(
            _oracle_kwargs(tracker=tracker),
            "session_limit",
        )

    def test_daily_loss_limit(self) -> None:
        tracker = SessionTracker()
        tracker.daily_losses = 1
        _assert_verdict_match(
            _oracle_kwargs(tracker=tracker),
            "daily_loss_limit",
        )

    def test_missing_data_asia_high(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(asia_high=None),
            "missing_asia_high",
        )

    def test_missing_data_candle_close(self) -> None:
        _assert_verdict_match(
            _oracle_kwargs(candle_c_close=None, sweep_extreme_price=None),
            "missing_candle_close",
        )


# =============================================================================
# P1.2 INTENT ADAPTER
# =============================================================================


class TestIntentAdapter:
    """TradeProposal → ExecutionIntent adapter tests."""

    def test_valid_proposal_converts(self) -> None:
        from execution.intent import Direction, IntentStatus, IntentType
        from execution.intent_adapter import (
            adapt_proposal_to_intent,
            reset_factory,
        )

        reset_factory()
        kw = _oracle_kwargs()
        result = evaluate_asia_scalp_setup(**kw)
        assert result.verdict == SetupVerdict.VALID
        assert result.proposal is not None

        state = _state_from_kwargs(kw)
        intent = adapt_proposal_to_intent(result.proposal, "EURUSD", state)

        assert intent.intent_type == IntentType.ENTRY
        assert intent.status == IntentStatus.PENDING
        assert intent.symbol == "EURUSD"
        assert intent.direction == Direction.LONG
        assert intent.size == result.proposal.position_size_lots
        assert intent.entry_price == result.proposal.entry_price
        assert intent.stop_loss == result.proposal.stop_loss
        assert intent.take_profit == result.proposal.take_profit
        assert intent.source_state_hash == state.compute_hash()
        assert len(intent.intent_hash) == 16

    def test_intent_hash_deterministic(self) -> None:
        from execution.intent_adapter import (
            adapt_proposal_to_intent,
            reset_factory,
        )

        kw = _oracle_kwargs()
        result = evaluate_asia_scalp_setup(**kw)
        assert result.proposal is not None
        state = _state_from_kwargs(kw)

        reset_factory()
        intent1 = adapt_proposal_to_intent(result.proposal, "EURUSD", state)
        reset_factory()
        intent2 = adapt_proposal_to_intent(result.proposal, "EURUSD", state)

        assert intent1.intent_hash == intent2.intent_hash

    def test_bearish_maps_to_short(self) -> None:
        from execution.intent import Direction
        from execution.intent_adapter import (
            adapt_proposal_to_intent,
            reset_factory,
        )

        reset_factory()
        kw = _oracle_kwargs(
            sweep_direction="bearish",
            sweep_extreme_price=1.0868,
            candle_c_close=1.0858,
        )
        result = evaluate_asia_scalp_setup(**kw)
        assert result.proposal is not None

        state = _state_from_kwargs(kw)
        intent = adapt_proposal_to_intent(result.proposal, "EURUSD", state)
        assert intent.direction == Direction.SHORT
