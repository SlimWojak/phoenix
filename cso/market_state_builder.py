"""
Market State Builder — S51 DRIVESHAFT T1
=========================================

Frozen Dataclass Factory: enrichment DataFrames → immutable MarketState.

INVARIANTS:
  INV-BUILDER-PURE-ADAPTER: Zero scoring. Zero inference. Zero heuristics.
  INV-NO-FORMING-CANDLE: Only data from closed bars. evaluation_time = t_close.
  INV-PIT-JOIN-ONLY: Only data indexed < now visible.
  INV-CONTRACT-1: Deterministic — same inputs → same MarketState.

FORBIDDEN:
  - Scoring or grading
  - Inference or heuristics
  - Forward-looking data access
  - Any logic beyond column mapping + NaN policy
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]  # pandas has no py.typed

from cso.evaluator import MarketState

logger = logging.getLogger(__name__)

PIP_SIZE = 0.0001


@dataclass
class MarketStateBuildReport:
    """Observability report emitted per evaluation tick."""

    evaluation_time: datetime
    pair: str
    tf_close_times: dict[str, datetime | None]
    missing_required: list[str]
    per_field_sources: dict[str, str]
    unmapped_columns: int
    valid: bool

    # S52 T3 — River provenance (REQUIRED on every CSE downstream)
    river_latest_bar_timestamp: datetime | None = None
    river_knowledge_time: datetime | None = None
    river_bar_hash_sample: str | None = None


STALENESS_THRESHOLD_MINUTES: int = 5


class RiverStalenessError(Exception):
    """INV-RIVER-FRESHNESS: River data is stale beyond threshold."""


def build_market_state(
    df: pd.DataFrame,
    pair: str,
    now: datetime,
    sweep_window_bars: int = 48,
    fvg_window_bars: int = 12,
    staleness_threshold_minutes: int = STALENESS_THRESHOLD_MINUTES,
) -> tuple[MarketState, MarketStateBuildReport]:
    """
    Build immutable MarketState from enrichment DataFrame.

    INV-BUILDER-PURE-ADAPTER: Pure mapping. No inference.
    INV-NO-FORMING-CANDLE: Uses latest bar with t_close <= now.
    INV-PIT-JOIN-ONLY: Filters df to rows where timestamp < now.
    INV-RIVER-FRESHNESS: Refuses data older than staleness_threshold_minutes.

    Args:
        df: Enrichment DataFrame (L1-L6 columns applied).
            Must have 'timestamp' column (UTC, tz-aware or naive).
        pair: Trading pair (e.g. "EURUSD").
        now: Current wall-clock time (UTC). Only bars with
             timestamp < now are visible.
        sweep_window_bars: Lookback window for sweep detection.
        fvg_window_bars: Lookback window for FVG detection.
        staleness_threshold_minutes: Max age of newest bar before HALT.

    Returns:
        (MarketState, MarketStateBuildReport) tuple.

    Raises:
        RiverStalenessError: If newest bar is older than threshold (INV-RIVER-FRESHNESS).
    """
    report_sources: dict[str, str] = {}
    missing_required: list[str] = []

    pit_df = _point_in_time_filter(df, now)

    # INV-RIVER-FRESHNESS: refuse stale data
    if not pit_df.empty and "timestamp" in pit_df.columns:
        last_bar = pit_df["timestamp"].max()
        if hasattr(last_bar, "tz") and last_bar.tz is not None:
            now_ts = (
                pd.Timestamp(now, tz="UTC")
                if not hasattr(now, "tzinfo") or now.tzinfo is None
                else pd.Timestamp(now)
            )
        else:
            now_ts = (
                pd.Timestamp(now.replace(tzinfo=None))
                if hasattr(now, "tzinfo")
                else pd.Timestamp(now)
            )
        staleness = now_ts - last_bar
        if staleness > pd.Timedelta(minutes=staleness_threshold_minutes):
            logger.error(
                "INV-RIVER-FRESHNESS: %s last_bar=%s staleness_minutes=%.1f",
                pair,
                str(last_bar),
                staleness.total_seconds() / 60,
            )
            raise RiverStalenessError(
                f"INV-RIVER-FRESHNESS: {pair} last bar {last_bar}, "
                f"staleness {staleness} exceeds {staleness_threshold_minutes}min threshold"
            )

    # S52 T3: Extract River provenance before any early returns
    river_latest_ts: datetime | None = None
    river_kt: datetime | None = None
    river_hash_sample: str | None = None
    if not pit_df.empty:
        last_ts = pit_df["timestamp"].max()
        river_latest_ts = last_ts.to_pydatetime() if isinstance(last_ts, pd.Timestamp) else last_ts
        if "knowledge_time" in pit_df.columns:
            kt = pit_df["knowledge_time"].max()
            if pd.notna(kt):
                river_kt = kt.to_pydatetime() if isinstance(kt, pd.Timestamp) else kt
        if "bar_hash" in pit_df.columns:
            last_hash = pit_df.iloc[-1].get("bar_hash")
            if last_hash is not None and not (isinstance(last_hash, float) and pd.isna(last_hash)):
                river_hash_sample = str(last_hash)

    if pit_df.empty:
        return _cold_start(pair, now, missing_required, report_sources)

    eval_time = _get_evaluation_time(pit_df)
    latest = pit_df.iloc[-1]

    htf_bias = _safe_str(latest, "order_flow", report_sources, "L4")
    current_session = _safe_str(latest, "session_name", report_sources, "L1")
    session_bias = _safe_str(latest, "order_flow", report_sources, "L4")

    asia_high = _safe_float(latest, "asia_high", report_sources, "L2")
    asia_low = _safe_float(latest, "asia_low", report_sources, "L2")
    asia_range_pips = _safe_float(latest, "asia_range_pips", report_sources, "L2")

    if asia_high is None:
        missing_required.append("asia_high")
    if asia_low is None:
        missing_required.append("asia_low")

    asia_range_valid = asia_range_pips is not None and asia_range_pips <= 30.0

    sweep_window = pit_df.tail(sweep_window_bars)
    sweep_data = _extract_sweep_data(sweep_window, latest, report_sources)

    fvg_window = pit_df.tail(fvg_window_bars)
    fvg_data = _extract_fvg_data(fvg_window, latest, report_sources)

    displacement_pips = _safe_float(latest, "displacement_pips", report_sources, "L6")
    if displacement_pips is not None and displacement_pips == 0:
        displacement_pips = None

    ltf_recent = pit_df.tail(6)
    ltf_confirmation = (
        bool(ltf_recent["structure_confirmed"].any())
        if "structure_confirmed" in ltf_recent.columns
        else False
    )
    report_sources["ltf_confirmation"] = "L4:structure_confirmed"

    ltf_direction = _safe_str(latest, "structure_trend", report_sources, "L4")

    re_acc = _extract_re_acceptance(sweep_window, asia_high, asia_low, report_sources)

    candle_c_inside = None
    if asia_high is not None and asia_low is not None and "close" in latest.index:
        c = latest["close"]
        candle_c_inside = bool(asia_low < c < asia_high)
        report_sources["candle_c_inside_range"] = "L0:close vs L2:asia_high/low"

    invalid_reason = None
    if missing_required:
        invalid_reason = f"missing_required: {', '.join(missing_required)}"

    state = MarketState(
        pair=pair,
        timestamp=now,
        evaluation_time=eval_time,
        htf_bias=htf_bias,
        current_session=current_session,
        session_bias=session_bias,
        asia_high=asia_high,
        asia_low=asia_low,
        asia_range_pips=asia_range_pips,
        asia_range_valid=asia_range_valid,
        fvg_count=fvg_data["fvg_count"],
        fvg_direction=fvg_data["fvg_direction"],
        fvg_bull_present=fvg_data["fvg_bull_present"],
        fvg_bear_present=fvg_data["fvg_bear_present"],
        fvg_untouched_pips=fvg_data["fvg_untouched_pips"],
        displacement_pips=displacement_pips,
        recent_sweep=sweep_data["recent_sweep"],
        sweep_age_bars=sweep_data["sweep_age_bars"],
        sweep_direction=sweep_data["sweep_direction"],
        sweep_extension_pips=sweep_data["sweep_extension_pips"],
        sweep_target_type=sweep_data["sweep_target_type"],
        asia_high_max_extension_pips=sweep_data["asia_high_max_ext"],
        asia_low_max_extension_pips=sweep_data["asia_low_max_ext"],
        re_acceptance=re_acc,
        candle_c_inside_range=candle_c_inside,
        ltf_confirmation=ltf_confirmation,
        ltf_direction=ltf_direction,
        invalid_reason=invalid_reason,
    )

    report = MarketStateBuildReport(
        evaluation_time=eval_time,
        pair=pair,
        tf_close_times={"5m": eval_time},
        missing_required=missing_required,
        per_field_sources=report_sources,
        unmapped_columns=0,
        valid=invalid_reason is None,
        river_latest_bar_timestamp=river_latest_ts,
        river_knowledge_time=river_kt,
        river_bar_hash_sample=river_hash_sample,
    )

    return state, report


# =============================================================================
# POINT-IN-TIME FILTERING
# =============================================================================


def _point_in_time_filter(df: pd.DataFrame, now: datetime) -> pd.DataFrame:
    """
    Filter DataFrame to rows with timestamp < now.

    INV-PIT-JOIN-ONLY: Future data present in df but invisible to output.
    INV-NO-FORMING-CANDLE: Only completed bars visible.
    """
    if df.empty or "timestamp" not in df.columns:
        return df

    ts = df["timestamp"]
    if ts.dt.tz is None:
        now_comparable = now.replace(tzinfo=None) if now.tzinfo else now
    else:
        now_comparable = now if now.tzinfo else now.replace(tzinfo=UTC)

    return df[ts < now_comparable].copy()


def _get_evaluation_time(pit_df: pd.DataFrame) -> datetime:
    """Get evaluation time = timestamp of latest closed bar."""
    ts = pit_df["timestamp"].iloc[-1]
    if isinstance(ts, pd.Timestamp):
        dt: datetime = ts.to_pydatetime()
        return dt
    if isinstance(ts, datetime):
        return ts
    return datetime.now(UTC)


# =============================================================================
# FIELD EXTRACTORS — Pure mapping, no logic
# =============================================================================


def _safe_float(
    row: pd.Series,
    col: str,
    sources: dict[str, str],
    layer: str,
) -> float | None:
    """Extract float value, return None for NaN/missing."""
    if col not in row.index:
        return None
    val = row[col]
    sources[col] = f"{layer}:{col}"
    if pd.isna(val):
        return None
    return float(val)


def _safe_str(
    row: pd.Series,
    col: str,
    sources: dict[str, str],
    layer: str,
) -> str | None:
    """Extract string value, return None for NaN/None/missing."""
    if col not in row.index:
        return None
    val = row[col]
    sources[col] = f"{layer}:{col}"
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return str(val)


def _extract_sweep_data(
    window: pd.DataFrame,
    latest: pd.Series,
    sources: dict[str, str],
) -> dict[str, Any]:
    """Extract sweep-related fields from recent window."""
    result: dict[str, Any] = {
        "recent_sweep": False,
        "sweep_age_bars": None,
        "sweep_direction": None,
        "sweep_extension_pips": None,
        "sweep_target_type": None,
        "asia_high_max_ext": None,
        "asia_low_max_ext": None,
    }

    if "sweep_detected" not in window.columns:
        return result

    sweep_mask = window["sweep_detected"] == True
    if not sweep_mask.any():
        sources["sweep_detected"] = "L3:sweep_detected (none in window)"
        return result

    result["recent_sweep"] = True
    sources["sweep_detected"] = "L3:sweep_detected"

    last_sweep_idx = sweep_mask[::-1].idxmax()
    bars_since = len(window) - 1 - window.index.get_loc(last_sweep_idx)
    result["sweep_age_bars"] = int(bars_since)

    last_sweep = window.loc[last_sweep_idx]

    if "sweep_direction" in window.columns:
        val = last_sweep.get("sweep_direction")
        if val is not None and not (isinstance(val, float) and np.isnan(val)):
            result["sweep_direction"] = str(val)
            sources["sweep_direction"] = "L3:sweep_direction"

    if "sweep_extension_pips" in window.columns:
        val = last_sweep.get("sweep_extension_pips")
        if val is not None and not (isinstance(val, float) and np.isnan(val)):
            result["sweep_extension_pips"] = float(val)
            sources["sweep_extension_pips"] = "L3:sweep_extension_pips"

    if "sweep_target_type" in window.columns:
        val = last_sweep.get("sweep_target_type")
        if val is not None and not (isinstance(val, float) and np.isnan(val)):
            result["sweep_target_type"] = str(val)
            sources["sweep_target_type"] = "L3:sweep_target_type"

    if "sweep_extension_pips" in window.columns and "sweep_target_type" in window.columns:
        high_sweeps = window[
            (window["sweep_detected"] == True) & (window["sweep_target_type"] == "asia_high")
        ]
        if not high_sweeps.empty:
            result["asia_high_max_ext"] = float(high_sweeps["sweep_extension_pips"].max())
            sources["asia_high_max_extension_pips"] = "L3:sweep_extension_pips(asia_high)"

        low_sweeps = window[
            (window["sweep_detected"] == True) & (window["sweep_target_type"] == "asia_low")
        ]
        if not low_sweeps.empty:
            result["asia_low_max_ext"] = float(low_sweeps["sweep_extension_pips"].max())
            sources["asia_low_max_extension_pips"] = "L3:sweep_extension_pips(asia_low)"

    return result


def _extract_fvg_data(
    window: pd.DataFrame,
    latest: pd.Series,
    sources: dict[str, str],
) -> dict[str, Any]:
    """Extract FVG-related fields from recent window."""
    result: dict[str, Any] = {
        "fvg_count": 0,
        "fvg_direction": None,
        "fvg_bull_present": False,
        "fvg_bear_present": False,
        "fvg_untouched_pips": None,
    }

    if "fvg_bull" not in window.columns:
        return result

    bull_mask = window["fvg_bull"] == True
    bear_mask = (
        window["fvg_bear"] == True
        if "fvg_bear" in window.columns
        else pd.Series(False, index=window.index)
    )

    bull_count = int(bull_mask.sum())
    bear_count = int(bear_mask.sum())
    result["fvg_count"] = bull_count + bear_count
    result["fvg_bull_present"] = bull_count > 0
    result["fvg_bear_present"] = bear_count > 0
    sources["fvg_count"] = "L6:fvg_bull+fvg_bear"

    if bull_count > 0 and bear_count == 0:
        result["fvg_direction"] = "bullish"
    elif bear_count > 0 and bull_count == 0:
        result["fvg_direction"] = "bearish"
    elif bull_count > 0 and bear_count > 0:
        last_bull = bull_mask[::-1].idxmax() if bull_count > 0 else -1
        last_bear = bear_mask[::-1].idxmax() if bear_count > 0 else -1
        result["fvg_direction"] = "bullish" if last_bull > last_bear else "bearish"

    latest_fvg_row = None
    if bull_mask.any() or bear_mask.any():
        combined = bull_mask | bear_mask
        latest_fvg_idx = combined[::-1].idxmax()
        latest_fvg_row = window.loc[latest_fvg_idx]

    if latest_fvg_row is not None:
        gap_size = None
        if latest_fvg_row.get("fvg_bull", False):
            h = latest_fvg_row.get("fvg_bull_high")
            l = latest_fvg_row.get("fvg_bull_low")
            if h is not None and l is not None and not np.isnan(h) and not np.isnan(l):
                gap_size = (h - l) / PIP_SIZE
        elif latest_fvg_row.get("fvg_bear", False):
            h = latest_fvg_row.get("fvg_bear_high")
            l = latest_fvg_row.get("fvg_bear_low")
            if h is not None and l is not None and not np.isnan(h) and not np.isnan(l):
                gap_size = (h - l) / PIP_SIZE
        result["fvg_untouched_pips"] = gap_size
        sources["fvg_untouched_pips"] = "L6:fvg_*_high/low"

    return result


def _extract_re_acceptance(
    window: pd.DataFrame,
    asia_high: float | None,
    asia_low: float | None,
    sources: dict[str, str],
) -> bool | None:
    """
    Detect re-acceptance: 5m close strictly inside Asia range after sweep.

    Returns None if data insufficient, True/False otherwise.
    """
    if asia_high is None or asia_low is None:
        return None

    if "sweep_detected" not in window.columns or "close" not in window.columns:
        return None

    sweep_mask = window["sweep_detected"] == True
    if not sweep_mask.any():
        return None

    last_sweep_idx = sweep_mask[::-1].idxmax()
    last_sweep_pos = window.index.get_loc(last_sweep_idx)

    post_sweep = window.iloc[last_sweep_pos:]
    for _, row in post_sweep.iterrows():
        c = row["close"]
        if asia_low < c < asia_high:
            sources["re_acceptance"] = "L3:sweep + L0:close inside L2:asia range"
            return True

    sources["re_acceptance"] = "L3:sweep found, no close inside range"
    return False


# =============================================================================
# COLD START
# =============================================================================


def _cold_start(
    pair: str,
    now: datetime,
    missing_required: list[str],
    report_sources: dict[str, str],
) -> tuple[MarketState, MarketStateBuildReport]:
    """Handle cold start: empty DataFrame → invalid MarketState, all gates SKIP."""
    missing_required.append("all_data")

    state = MarketState(
        pair=pair,
        timestamp=now,
        invalid_reason="cold_start: no data available",
    )

    report = MarketStateBuildReport(
        evaluation_time=now,
        pair=pair,
        tf_close_times={"5m": None},
        missing_required=missing_required,
        per_field_sources=report_sources,
        unmapped_columns=0,
        valid=False,
    )

    return state, report


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "build_market_state",
    "MarketStateBuildReport",
]
