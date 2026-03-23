"""
Signal Adapter — DEPLOY.P2.1 + P2.3
=====================================

Converts Dexter DIAGNOSTIC_SIGNAL into Phoenix governance proposal.
The adapter does PRICE DISCOVERY — transforming an analytical claim
into a priced TradeProposal with full geometry (entry, SL, TP, size),
then routes through the constitutional 5-drawer governance path.

"Telescopes do not fire rockets."
The signal says WHEN to look. The adapter computes WHAT to do.
The 5-drawer gates decide WHETHER to act.

INV-BUILDER-PURE-ADAPTER: Maps fields + computes prices. No scoring/inference.
INV-CONTRACT-1: Same signal + same enrichment → same intent_hash.
INV-NO-FORMING-CANDLE: signal.bar_time must reference closed bar.
INV-RACE-BAR-SYNC: enrichment watermark >= signal.bar_time.
INV-SHADOW-MODE-RESPECTED: shadow=True → ShadowObservation only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import pandas as pd

from cso.evaluator import FiveDrawerResult, GateEvaluator, MarketState
from cso.gate_registry import (
    GateContext,
    GateRegistry,
    build_ars_registry,
)
from cso.market_state_builder import (
    RiverStalenessError,
    build_market_state,
)
from execution.asia_scalp import TradeDirection, TradeProposal
from execution.intent import ExecutionIntent
from execution.intent_adapter import adapt_proposal_to_intent

logger = logging.getLogger(__name__)

PIP = 0.0001
SL_BUFFER = 0.00005
RISK_PCT = 0.01
MIN_RR = 1.5
PIT_OFFSET_MINUTES = 5
DRIFT_WARNING_SECONDS = 240

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

REQUIRED_SIGNAL_KEYS = frozenset({"bar_time", "direction"})


class SignalOutcome(str, Enum):
    PROPOSAL_CREATED = "PROPOSAL_CREATED"
    SHADOW_OBSERVATION = "SHADOW_OBSERVATION"
    CSO_REJECTED = "CSO_REJECTED"
    PRICE_DISCOVERY_FAILED = "PRICE_DISCOVERY_FAILED"
    INVALID_SIGNAL = "INVALID_SIGNAL"
    HALT_BLOCKED = "HALT_BLOCKED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class SignalContext:
    """
    Fields carried from the Dexter signal, available to gate predicates.

    For P2.2 HTF gates (stub now, calibrated by Olya later),
    these fields flow into evaluation context.
    """

    direction: str = ""
    model_type: str = ""
    chain_type: str = ""
    htf_phase: str = ""
    direction_permission: str = ""
    peak_window: bool = False


@dataclass(frozen=True)
class SignalFriction:
    """
    P2.3 — Governance-side rejection record.

    Generated when a valid analytical signal fails the 5-drawer CSO.
    Dream Cycle tracks analytical rejections (why chains were skipped).
    Signal Friction tracks governance rejections (why valid signals failed CSO).
    Together: complete learning surface across both economies.
    """

    timestamp: datetime
    pair: str
    signal_direction: str
    signal_model_type: str
    gate_failures: list[str]
    drawer_failures: list[int]
    bar_time: datetime
    reason: str


@dataclass
class SignalResult:
    """Complete result of processing a DIAGNOSTIC_SIGNAL through governance."""

    outcome: SignalOutcome
    signal_context: SignalContext | None = None
    market_state: MarketState | None = None
    proposal: TradeProposal | None = None
    five_drawer: FiveDrawerResult | None = None
    intent: ExecutionIntent | None = None
    friction: SignalFriction | None = None
    drift_seconds: float | None = None
    error: str | None = None


def process_signal(
    signal: dict[str, Any],
    df: pd.DataFrame,
    pair: str,
    account_equity: float = 10000.0,
    pip_value: float = 10.0,
    shadow_mode: bool = True,
    halt_check_fn: Any | None = None,
    registry: GateRegistry | None = None,
) -> SignalResult:
    """
    Process a Dexter DIAGNOSTIC_SIGNAL through constitutional governance.

    Steps:
      1. Parse + validate signal
      2. Time alignment (bar_time + 5min)
      3. Build MarketState from enrichment
      4. Price discovery (entry, SL, TP, size)
      5. Build TradeProposal with full geometry
      6. 5-drawer CSO evaluation
      7. If pass → ExecutionIntent
      8. Governance (halt, shadow)
      9. If rejected → SignalFriction

    Args:
        signal: DIAGNOSTIC_SIGNAL reasoning_trace dict from Dexter
        df: Enriched DataFrame (L1-L7 columns)
        pair: Trading pair
        account_equity: Account equity for position sizing
        pip_value: Pip value for sizing (default 10.0 for EURUSD)
        shadow_mode: If True, observe only (INV-SHADOW-MODE-RESPECTED)
        halt_check_fn: Optional halt check callable
        registry: Optional GateRegistry (builds ARS default if None)

    Returns:
        SignalResult with full provenance
    """
    # Step 1: Parse + validate
    sig_ctx, parse_error = _parse_signal(signal)
    if parse_error is not None:
        return SignalResult(
            outcome=SignalOutcome.INVALID_SIGNAL,
            error=parse_error,
        )

    bar_time = _parse_bar_time(signal.get("bar_time", ""))
    if bar_time is None:
        return SignalResult(
            outcome=SignalOutcome.INVALID_SIGNAL,
            signal_context=sig_ctx,
            error="bar_time missing or unparseable",
        )

    assert sig_ctx is not None  # guaranteed by parse check above

    # Step 2: PIT alignment (Appendix B §3)
    now = bar_time + timedelta(minutes=PIT_OFFSET_MINUTES)

    # Step 3: Build MarketState
    try:
        state, report = build_market_state(df, pair, now)
    except RiverStalenessError as e:
        return SignalResult(
            outcome=SignalOutcome.ERROR,
            signal_context=sig_ctx,
            error=f"INV-RIVER-FRESHNESS: {e}",
        )

    if not report.valid:
        return SignalResult(
            outcome=SignalOutcome.PRICE_DISCOVERY_FAILED,
            signal_context=sig_ctx,
            market_state=state,
            error=f"invalid state: {state.invalid_reason}",
        )

    # Drift check (OWL insight)
    drift_seconds: float | None = None
    if state.evaluation_time is not None:
        drift = now - state.evaluation_time
        drift_seconds = drift.total_seconds()
        if drift_seconds > DRIFT_WARNING_SECONDS:
            logger.warning(
                "PIT_DRIFT: %.1fs between now=%s and evaluation_time=%s (> %ds threshold)",
                drift_seconds,
                now.isoformat(),
                state.evaluation_time.isoformat(),
                DRIFT_WARNING_SECONDS,
            )

    # Step 4: Price discovery
    proposal = _price_discovery(
        state,
        df,
        now,
        pair,
        sig_ctx.direction,
        account_equity,
        pip_value,
    )
    if proposal is None:
        return SignalResult(
            outcome=SignalOutcome.PRICE_DISCOVERY_FAILED,
            signal_context=sig_ctx,
            market_state=state,
            drift_seconds=drift_seconds,
            error="insufficient data for price discovery",
        )

    # Step 5: Build GateContext
    gate_ctx = GateContext(
        rr_ratio=proposal.rr_ratio,
        session_can_trade=True,
    )

    # Step 6: 5-drawer CSO evaluation
    if registry is None:
        registry = build_ars_registry()
    evaluator = GateEvaluator()
    five_drawer = evaluator.evaluate_with_registry(
        pair,
        state,
        "ARS_v2.0.0",
        registry,
        ARS_GATE_IDS,
        gate_ctx,
    )

    all_pass = all(five_drawer.drawer_status.values())

    if not all_pass:
        friction = _build_friction(
            signal,
            sig_ctx,
            five_drawer,
            bar_time,
            pair,
        )
        return SignalResult(
            outcome=SignalOutcome.CSO_REJECTED,
            signal_context=sig_ctx,
            market_state=state,
            proposal=proposal,
            five_drawer=five_drawer,
            friction=friction,
            drift_seconds=drift_seconds,
        )

    # Step 7: Adapt → ExecutionIntent
    intent = adapt_proposal_to_intent(proposal, pair, state)

    # Step 8: Governance
    if halt_check_fn is not None:
        try:
            if halt_check_fn():
                return SignalResult(
                    outcome=SignalOutcome.HALT_BLOCKED,
                    signal_context=sig_ctx,
                    market_state=state,
                    proposal=proposal,
                    five_drawer=five_drawer,
                    intent=intent,
                    drift_seconds=drift_seconds,
                )
        except Exception as e:
            return SignalResult(
                outcome=SignalOutcome.ERROR,
                signal_context=sig_ctx,
                error=f"halt check failed: {e}",
            )

    if shadow_mode:
        return SignalResult(
            outcome=SignalOutcome.SHADOW_OBSERVATION,
            signal_context=sig_ctx,
            market_state=state,
            proposal=proposal,
            five_drawer=five_drawer,
            intent=intent,
            drift_seconds=drift_seconds,
        )

    return SignalResult(
        outcome=SignalOutcome.PROPOSAL_CREATED,
        signal_context=sig_ctx,
        market_state=state,
        proposal=proposal,
        five_drawer=five_drawer,
        intent=intent,
        drift_seconds=drift_seconds,
    )


# =============================================================================
# INTERNALS
# =============================================================================


def _parse_signal(
    signal: dict[str, Any],
) -> tuple[SignalContext | None, str | None]:
    """Parse and validate signal dict. Returns (context, error)."""
    missing = REQUIRED_SIGNAL_KEYS - set(signal.keys())
    if missing:
        return None, f"missing required keys: {sorted(missing)}"

    ctx = SignalContext(
        direction=str(signal.get("direction", "")),
        model_type=str(signal.get("model_type", "")),
        chain_type=str(signal.get("chain_type", "")),
        htf_phase=str(signal.get("worldstate_snapshot", {}).get("htf_phase", "")),
        direction_permission=str(
            signal.get("worldstate_snapshot", {}).get("direction_permission", "")
        ),
        peak_window=bool(signal.get("peak_window", False)),
    )
    return ctx, None


def _parse_bar_time(raw: Any) -> datetime | None:
    """Parse bar_time from ISO string or datetime."""
    if isinstance(raw, datetime):
        if raw.tzinfo is None:
            return raw.replace(tzinfo=UTC)
        return raw
    if isinstance(raw, str) and raw:
        try:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            return None
    return None


def _price_discovery(
    state: MarketState,
    df: pd.DataFrame,
    now: datetime,
    pair: str,
    signal_direction: str,
    account_equity: float,
    pip_value: float,
) -> TradeProposal | None:
    """
    Compute entry, SL, TP, size from MarketState + enrichment DataFrame.

    This is the core of the adapter — translating analytical observation
    into priced execution geometry.
    """
    if state.asia_high is None or state.asia_low is None:
        return None
    if state.sweep_extension_pips is None or state.sweep_direction is None:
        return None
    if state.asia_range_pips is None:
        return None

    # Entry price: candle C close from PIT-filtered DataFrame
    entry = _extract_close(df, now)
    if entry is None:
        return None

    # Direction from signal (mapped to TradeDirection)
    if signal_direction.lower() in ("bullish", "long"):
        direction = TradeDirection.LONG
        sweep_extreme = state.asia_low - state.sweep_extension_pips * PIP
        sl = sweep_extreme - SL_BUFFER
        tp = state.asia_high
    elif signal_direction.lower() in ("bearish", "short"):
        direction = TradeDirection.SHORT
        sweep_extreme = state.asia_high + state.sweep_extension_pips * PIP
        sl = sweep_extreme + SL_BUFFER
        tp = state.asia_low
    else:
        return None

    risk_pips = abs(entry - sl) / PIP
    reward_pips = abs(tp - entry) / PIP

    if risk_pips <= 0:
        return None

    rr_ratio = reward_pips / risk_pips

    risk_amount = account_equity * RISK_PCT
    risk_price = abs(entry - sl)
    size = risk_amount / (risk_price * pip_value * 10000) if risk_price > 0 else 0.0

    return TradeProposal(
        direction=direction,
        entry_price=entry,
        stop_loss=sl,
        take_profit=tp,
        risk_pips=risk_pips,
        reward_pips=reward_pips,
        rr_ratio=rr_ratio,
        position_size_lots=round(size, 2),
        risk_amount=risk_amount,
        session_id=f"SIGNAL_{now.strftime('%Y-%m-%d')}",
        sweep_extension_pips=state.sweep_extension_pips,
        asia_high=state.asia_high,
        asia_low=state.asia_low,
        asia_range_pips=state.asia_range_pips,
        timestamp=now,
    )


def _extract_close(df: pd.DataFrame, now: datetime) -> float | None:
    """Extract candle C close from PIT-filtered DataFrame."""
    if df.empty or "timestamp" not in df.columns or "close" not in df.columns:
        return None
    from cso.market_state_builder import _point_in_time_filter

    pit = _point_in_time_filter(df, now)
    if pit.empty:
        return None
    return float(pit["close"].iloc[-1])


def _build_friction(
    signal: dict[str, Any],
    ctx: SignalContext,
    five_drawer: FiveDrawerResult,
    bar_time: datetime,
    pair: str,
) -> SignalFriction:
    """Build a SignalFriction record from a governance rejection."""
    gate_failures = list(five_drawer.gates_failed)
    drawer_failures = [did for did, passed in five_drawer.drawer_status.items() if not passed]
    reason_parts = [f"D{d}" for d in drawer_failures]

    return SignalFriction(
        timestamp=datetime.now(UTC),
        pair=pair,
        signal_direction=ctx.direction,
        signal_model_type=ctx.model_type,
        gate_failures=gate_failures,
        drawer_failures=drawer_failures,
        bar_time=bar_time,
        reason=f"CSO rejected: drawers {reason_parts} failed",
    )


__all__ = [
    "process_signal",
    "SignalResult",
    "SignalOutcome",
    "SignalContext",
    "SignalFriction",
]
