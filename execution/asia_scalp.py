"""
Asia Range Scalp Execution — S51 DRIVESHAFT T4
================================================

Complete trade lifecycle for Asia Range Scalp strategy:
  Setup detection → Entry → SL/TP → Position sizing → Session enforcement.

Methodology source: ~/dexter/docs/olya_canon_docs/asia_range_scalp_strategy_FINAL(1).md

DECISIONS (all locked):
  D6: Market order at Candle C close
  D7: SL buffer 0.5 pip (0.00005) beyond sweep extreme
  D8: Sweep extension = wick extreme beyond Asia boundary
  D9: 1 trade per Asia session (19:00 NY start)
  D10: Min R:R 1.5
  D11: FVG min 1.0 pip untouched area

INVARIANTS:
  INV-SOVEREIGN-1: Human sovereignty over capital absolute
  INV-HALT-OVERRIDES-LEASE: Halt wins always
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

SL_BUFFER_PIPS = 0.5
SL_BUFFER_PRICE = 0.00005  # EURUSD
MIN_RR = 1.5
MAX_TRADES_PER_SESSION = 1
MAX_DAILY_LOSSES = 1  # 1R = -1% equity
RISK_PCT = 0.01


class TradeDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class SetupVerdict(str, Enum):
    VALID = "VALID"
    REJECTED_RANGE_TOO_WIDE = "REJECTED_RANGE_TOO_WIDE"
    REJECTED_NO_SWEEP = "REJECTED_NO_SWEEP"
    REJECTED_EXTENSION_INVALID = "REJECTED_EXTENSION_INVALID"
    REJECTED_NO_REACCEPTANCE = "REJECTED_NO_REACCEPTANCE"
    REJECTED_NO_FVG = "REJECTED_NO_FVG"
    REJECTED_FVG_TOO_SMALL = "REJECTED_FVG_TOO_SMALL"
    REJECTED_CANDLE_NOT_INSIDE = "REJECTED_CANDLE_NOT_INSIDE"
    REJECTED_RR_INSUFFICIENT = "REJECTED_RR_INSUFFICIENT"
    REJECTED_SESSION_LIMIT = "REJECTED_SESSION_LIMIT"
    REJECTED_DAILY_LOSS_LIMIT = "REJECTED_DAILY_LOSS_LIMIT"
    REJECTED_MISSING_DATA = "REJECTED_MISSING_DATA"


@dataclass(frozen=True)
class TradeProposal:
    """Immutable trade proposal for T2 human gate."""

    direction: TradeDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_pips: float
    reward_pips: float
    rr_ratio: float
    position_size_lots: float
    risk_amount: float
    session_id: str
    sweep_extension_pips: float
    asia_high: float
    asia_low: float
    asia_range_pips: float
    timestamp: datetime


@dataclass(frozen=True)
class SetupResult:
    """Result of Asia Scalp setup evaluation."""

    verdict: SetupVerdict
    proposal: TradeProposal | None = None
    rejection_detail: str | None = None


@dataclass
class SessionTracker:
    """Track per-session and daily trade state."""

    trades_this_session: int = 0
    daily_losses: int = 0
    current_session_id: str | None = None

    def can_trade(self, session_id: str) -> tuple[bool, str | None]:
        if self.daily_losses >= MAX_DAILY_LOSSES:
            return False, f"daily_loss_limit: {self.daily_losses}/{MAX_DAILY_LOSSES}"

        if session_id == self.current_session_id:
            if self.trades_this_session >= MAX_TRADES_PER_SESSION:
                return False, f"session_limit: {self.trades_this_session}/{MAX_TRADES_PER_SESSION}"
        else:
            self.current_session_id = session_id
            self.trades_this_session = 0

        return True, None

    def record_trade(self) -> None:
        self.trades_this_session += 1

    def record_loss(self) -> None:
        self.daily_losses += 1

    def new_day(self) -> None:
        self.daily_losses = 0
        self.trades_this_session = 0
        self.current_session_id = None


def evaluate_asia_scalp_setup(
    asia_high: float | None,
    asia_low: float | None,
    asia_range_pips: float | None,
    sweep_direction: str | None,
    sweep_extension_pips: float | None,
    sweep_extreme_price: float | None,
    re_acceptance: bool | None,
    fvg_valid: bool,
    fvg_untouched_pips: float | None,
    candle_c_inside: bool | None,
    candle_c_close: float | None,
    session_id: str,
    account_equity: float,
    tracker: SessionTracker,
    pip_value: float = 10.0,
) -> SetupResult:
    """
    Evaluate a potential Asia Range Scalp setup.

    Pure function (except tracker mutation on success).
    Returns SetupResult with verdict + optional TradeProposal.
    """
    if asia_high is None or asia_low is None or asia_range_pips is None:
        return SetupResult(
            SetupVerdict.REJECTED_MISSING_DATA, rejection_detail="asia range data missing"
        )

    if candle_c_close is None or sweep_extreme_price is None:
        return SetupResult(
            SetupVerdict.REJECTED_MISSING_DATA, rejection_detail="price data missing"
        )

    can_trade, reason = tracker.can_trade(session_id)
    if not can_trade:
        if "daily" in (reason or ""):
            return SetupResult(SetupVerdict.REJECTED_DAILY_LOSS_LIMIT, rejection_detail=reason)
        return SetupResult(SetupVerdict.REJECTED_SESSION_LIMIT, rejection_detail=reason)

    if asia_range_pips > 30.0:
        return SetupResult(
            SetupVerdict.REJECTED_RANGE_TOO_WIDE, rejection_detail=f"range={asia_range_pips:.1f}"
        )

    if sweep_direction is None or sweep_extension_pips is None:
        return SetupResult(SetupVerdict.REJECTED_NO_SWEEP)

    if sweep_extension_pips < 1.0 or sweep_extension_pips > 20.0:
        return SetupResult(
            SetupVerdict.REJECTED_EXTENSION_INVALID,
            rejection_detail=f"ext={sweep_extension_pips:.1f}",
        )

    if re_acceptance is not True:
        return SetupResult(SetupVerdict.REJECTED_NO_REACCEPTANCE)

    if not fvg_valid:
        return SetupResult(SetupVerdict.REJECTED_NO_FVG)

    if fvg_untouched_pips is not None and fvg_untouched_pips < 1.0:
        return SetupResult(
            SetupVerdict.REJECTED_FVG_TOO_SMALL, rejection_detail=f"gap={fvg_untouched_pips:.1f}"
        )

    if candle_c_inside is not True:
        return SetupResult(SetupVerdict.REJECTED_CANDLE_NOT_INSIDE)

    if sweep_direction == "bullish":
        direction = TradeDirection.LONG
        entry_price = candle_c_close
        sl = sweep_extreme_price - SL_BUFFER_PRICE
        tp = asia_high
    elif sweep_direction == "bearish":
        direction = TradeDirection.SHORT
        entry_price = candle_c_close
        sl = sweep_extreme_price + SL_BUFFER_PRICE
        tp = asia_low
    else:
        return SetupResult(
            SetupVerdict.REJECTED_MISSING_DATA,
            rejection_detail=f"unknown direction: {sweep_direction}",
        )

    risk_pips = abs(entry_price - sl) / 0.0001
    reward_pips = abs(tp - entry_price) / 0.0001

    if risk_pips <= 0:
        return SetupResult(SetupVerdict.REJECTED_MISSING_DATA, rejection_detail="risk_pips <= 0")

    rr_ratio = reward_pips / risk_pips

    if rr_ratio < MIN_RR:
        return SetupResult(
            SetupVerdict.REJECTED_RR_INSUFFICIENT,
            rejection_detail=f"rr={rr_ratio:.2f} < {MIN_RR}",
        )

    risk_amount = account_equity * RISK_PCT
    risk_price = abs(entry_price - sl)
    position_size = risk_amount / (risk_price * pip_value * 10000) if risk_price > 0 else 0.0

    proposal = TradeProposal(
        direction=direction,
        entry_price=entry_price,
        stop_loss=sl,
        take_profit=tp,
        risk_pips=risk_pips,
        reward_pips=reward_pips,
        rr_ratio=rr_ratio,
        position_size_lots=round(position_size, 2),
        risk_amount=risk_amount,
        session_id=session_id,
        sweep_extension_pips=sweep_extension_pips,
        asia_high=asia_high,
        asia_low=asia_low,
        asia_range_pips=asia_range_pips,
        timestamp=datetime.now(),
    )

    tracker.record_trade()

    return SetupResult(SetupVerdict.VALID, proposal=proposal)


def make_session_id(trading_day: str) -> str:
    """Build session ID per D4: ASIA_ + date(19:00 NY start)."""
    return f"ASIA_{trading_day}"


__all__ = [
    "evaluate_asia_scalp_setup",
    "make_session_id",
    "TradeProposal",
    "SetupResult",
    "SetupVerdict",
    "SessionTracker",
    "TradeDirection",
]
