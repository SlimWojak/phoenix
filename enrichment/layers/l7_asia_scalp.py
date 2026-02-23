"""
Layer 7: Asia Range Scalp Primitives — S51 DRIVESHAFT T2
=========================================================

Strategy-specific enrichment for Asia Range Scalp:
  - RE_ACCEPTANCE detection (5m close strictly inside Asia range after sweep)
  - Per-direction sweep extension tracking with 20-pip invalidation
  - FVG Asia validation (untouched >= 1.0 pip + Candle C inside range)

DEPENDENCIES: L1 (sessions), L2 (asia range), L3 (sweeps), L6 (FVG)

INVARIANTS:
  - INV-CONTRACT-1: deterministic
  - INV-NO-FORMING-CANDLE: only closed bars

FORBIDDEN:
  - forward_fill
  - scoring or inference
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PIP_SIZE_EURUSD = 0.0001
ASIA_SWEEP_EXTENSION_MIN = 1.0
ASIA_SWEEP_EXTENSION_MAX = 20.0
ASIA_RANGE_MAX_PIPS = 30.0
FVG_MIN_UNTOUCHED_PIPS = 1.0


def enrich(df: pd.DataFrame, symbol: str = "EURUSD") -> pd.DataFrame:
    """
    Add Asia Range Scalp primitive columns.

    INV-CONTRACT-1: Deterministic.

    Args:
        df: DataFrame with L1-L6 columns applied.
        symbol: Trading pair.

    Returns:
        DataFrame with Asia Scalp columns added.
    """
    df = df.copy()
    _validate_input(df)

    pip_size = 0.01 if "JPY" in symbol.upper() else PIP_SIZE_EURUSD

    df = _detect_asia_sweep_extensions(df, pip_size)
    df = _detect_re_acceptance(df)
    df = _validate_fvg_asia(df, pip_size)
    df = _build_asia_scalp_state(df)

    return df


# =============================================================================
# PER-DIRECTION SWEEP EXTENSION TRACKING
# =============================================================================


def _detect_asia_sweep_extensions(df: pd.DataFrame, pip_size: float) -> pd.DataFrame:
    """
    Track max sweep extension per direction within each session's sweep window.

    Extension = wick extreme beyond Asia boundary (max traded price).
    >20 pips in a direction → invalidate THAT direction only.
    Valid range: 1-20 pips inclusive.
    """
    n = len(df)

    asia_high = df["asia_high"].values
    asia_low = df["asia_low"].values
    high = df["high"].values
    low = df["low"].values
    hour_ny = df["hour_ny"].values if "hour_ny" in df.columns else np.zeros(n)
    trading_day = df["trading_day"].values if "trading_day" in df.columns else np.zeros(n)

    asia_ext_high = np.full(n, 0.0)
    asia_ext_low = np.full(n, 0.0)
    asia_ext_high_max = np.full(n, 0.0)
    asia_ext_low_max = np.full(n, 0.0)
    asia_high_direction_valid = np.ones(n, dtype=bool)
    asia_low_direction_valid = np.ones(n, dtype=bool)

    current_day = None
    running_high_max = 0.0
    running_low_max = 0.0

    for i in range(n):
        in_sweep_window = 0 <= hour_ny[i] < 4

        if trading_day[i] != current_day:
            current_day = trading_day[i]
            running_high_max = 0.0
            running_low_max = 0.0

        if in_sweep_window and not np.isnan(asia_high[i]):
            ext_h = max(0.0, (high[i] - asia_high[i]) / pip_size)
            ext_l = max(0.0, (asia_low[i] - low[i]) / pip_size)

            asia_ext_high[i] = ext_h
            asia_ext_low[i] = ext_l

            running_high_max = max(running_high_max, ext_h)
            running_low_max = max(running_low_max, ext_l)

        asia_ext_high_max[i] = running_high_max
        asia_ext_low_max[i] = running_low_max
        asia_high_direction_valid[i] = running_high_max <= ASIA_SWEEP_EXTENSION_MAX
        asia_low_direction_valid[i] = running_low_max <= ASIA_SWEEP_EXTENSION_MAX

    df["asia_ext_high_pips"] = asia_ext_high
    df["asia_ext_low_pips"] = asia_ext_low
    df["asia_ext_high_max_pips"] = asia_ext_high_max
    df["asia_ext_low_max_pips"] = asia_ext_low_max
    df["asia_high_direction_valid"] = asia_high_direction_valid
    df["asia_low_direction_valid"] = asia_low_direction_valid

    df["asia_sweep_high_valid"] = (
        (asia_ext_high_max > 0)
        & (asia_ext_high_max >= ASIA_SWEEP_EXTENSION_MIN)
        & asia_high_direction_valid
    )
    df["asia_sweep_low_valid"] = (
        (asia_ext_low_max > 0)
        & (asia_ext_low_max >= ASIA_SWEEP_EXTENSION_MIN)
        & asia_low_direction_valid
    )

    return df


# =============================================================================
# RE-ACCEPTANCE DETECTION
# =============================================================================


def _detect_re_acceptance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect re-acceptance: at least ONE 5m candle close strictly inside Asia range
    after a sweep event.

    Strictly inside: asia_low < close < asia_high (not on boundary).
    """
    n = len(df)

    asia_high = df["asia_high"].values
    asia_low = df["asia_low"].values
    close = df["close"].values
    hour_ny = df["hour_ny"].values if "hour_ny" in df.columns else np.zeros(n)
    trading_day = df["trading_day"].values if "trading_day" in df.columns else np.zeros(n)

    sweep_detected = (
        df["sweep_detected"].values if "sweep_detected" in df.columns else np.zeros(n, dtype=bool)
    )

    re_acceptance = np.zeros(n, dtype=bool)
    close_strictly_inside = np.zeros(n, dtype=bool)

    current_day = None
    sweep_seen_this_session = False

    for i in range(n):
        in_sweep_window = 0 <= hour_ny[i] < 4

        if trading_day[i] != current_day:
            current_day = trading_day[i]
            sweep_seen_this_session = False

        if not np.isnan(asia_high[i]) and not np.isnan(asia_low[i]):
            strictly_inside = bool(asia_low[i] < close[i] < asia_high[i])
            close_strictly_inside[i] = strictly_inside
        else:
            strictly_inside = False

        if in_sweep_window and sweep_detected[i]:
            sweep_seen_this_session = True

        if in_sweep_window and sweep_seen_this_session and strictly_inside:
            re_acceptance[i] = True

    df["close_strictly_inside_asia"] = close_strictly_inside
    df["re_acceptance"] = re_acceptance

    return df


# =============================================================================
# FVG ASIA VALIDATION
# =============================================================================


def _validate_fvg_asia(df: pd.DataFrame, pip_size: float) -> pd.DataFrame:
    """
    Validate FVGs for Asia Scalp strategy:
    1. Standard FVG exists (from L6)
    2. Untouched area >= 1.0 pip
    3. Candle C close strictly inside Asia range
    """
    n = len(df)

    fvg_bull = df["fvg_bull"].values if "fvg_bull" in df.columns else np.zeros(n, dtype=bool)
    fvg_bear = df["fvg_bear"].values if "fvg_bear" in df.columns else np.zeros(n, dtype=bool)
    fvg_bull_high = (
        df["fvg_bull_high"].values if "fvg_bull_high" in df.columns else np.full(n, np.nan)
    )
    fvg_bull_low = df["fvg_bull_low"].values if "fvg_bull_low" in df.columns else np.full(n, np.nan)
    fvg_bear_high = (
        df["fvg_bear_high"].values if "fvg_bear_high" in df.columns else np.full(n, np.nan)
    )
    fvg_bear_low = df["fvg_bear_low"].values if "fvg_bear_low" in df.columns else np.full(n, np.nan)
    close_inside = (
        df["close_strictly_inside_asia"].values
        if "close_strictly_inside_asia" in df.columns
        else np.zeros(n, dtype=bool)
    )

    fvg_asia_bull_valid = np.zeros(n, dtype=bool)
    fvg_asia_bear_valid = np.zeros(n, dtype=bool)
    fvg_untouched_pips = np.full(n, np.nan)

    for i in range(n):
        if fvg_bull[i]:
            gap = (fvg_bull_high[i] - fvg_bull_low[i]) / pip_size
            fvg_untouched_pips[i] = gap
            if gap >= FVG_MIN_UNTOUCHED_PIPS and close_inside[i]:
                fvg_asia_bull_valid[i] = True

        if fvg_bear[i]:
            gap = (fvg_bear_high[i] - fvg_bear_low[i]) / pip_size
            fvg_untouched_pips[i] = gap
            if gap >= FVG_MIN_UNTOUCHED_PIPS and close_inside[i]:
                fvg_asia_bear_valid[i] = True

    df["fvg_asia_bull_valid"] = fvg_asia_bull_valid
    df["fvg_asia_bear_valid"] = fvg_asia_bear_valid
    df["fvg_untouched_pips"] = fvg_untouched_pips

    return df


# =============================================================================
# COMPOSITE STATE MACHINE
# =============================================================================


def _build_asia_scalp_state(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build composite Asia Scalp state per bar.

    State machine: WAIT_RANGE → WAIT_SWEEP → WAIT_REACCEPT → WAIT_FVG → SETUP_VALID
    """
    n = len(df)
    hour_ny = df["hour_ny"].values if "hour_ny" in df.columns else np.zeros(n)
    trading_day = df["trading_day"].values if "trading_day" in df.columns else np.zeros(n)
    asia_range_pips = (
        df["asia_range_pips"].values if "asia_range_pips" in df.columns else np.full(n, np.nan)
    )

    sweep_detected = (
        df["sweep_detected"].values if "sweep_detected" in df.columns else np.zeros(n, dtype=bool)
    )
    re_acceptance = (
        df["re_acceptance"].values if "re_acceptance" in df.columns else np.zeros(n, dtype=bool)
    )
    fvg_bull_valid = (
        df["fvg_asia_bull_valid"].values
        if "fvg_asia_bull_valid" in df.columns
        else np.zeros(n, dtype=bool)
    )
    fvg_bear_valid = (
        df["fvg_asia_bear_valid"].values
        if "fvg_asia_bear_valid" in df.columns
        else np.zeros(n, dtype=bool)
    )

    asia_high_valid = (
        df["asia_high_direction_valid"].values
        if "asia_high_direction_valid" in df.columns
        else np.ones(n, dtype=bool)
    )
    asia_low_valid = (
        df["asia_low_direction_valid"].values
        if "asia_low_direction_valid" in df.columns
        else np.ones(n, dtype=bool)
    )
    sweep_direction = (
        df["sweep_direction"].values
        if "sweep_direction" in df.columns
        else np.full(n, None, dtype=object)
    )

    state = np.full(n, "INACTIVE", dtype=object)
    setup_valid = np.zeros(n, dtype=bool)
    setup_direction = np.full(n, None, dtype=object)

    current_day = None
    session_state = "INACTIVE"
    range_valid = False
    sweep_seen = False
    reaccept_seen = False
    last_sweep_dir = None
    trade_taken = False

    for i in range(n):
        in_range_window = hour_ny[i] >= 19
        in_sweep_window = 0 <= hour_ny[i] < 4

        if trading_day[i] != current_day:
            current_day = trading_day[i]
            session_state = "WAIT_RANGE"
            range_valid = False
            sweep_seen = False
            reaccept_seen = False
            last_sweep_dir = None
            trade_taken = False

        if trade_taken:
            state[i] = "TRADE_TAKEN"
            continue

        if session_state == "WAIT_RANGE":
            if not np.isnan(asia_range_pips[i]) and asia_range_pips[i] <= ASIA_RANGE_MAX_PIPS:
                range_valid = True
            if in_sweep_window and range_valid:
                session_state = "WAIT_SWEEP"
            elif in_sweep_window and not range_valid:
                session_state = "SESSION_INVALID"

        if session_state == "WAIT_SWEEP" and in_sweep_window:
            if sweep_detected[i]:
                d = sweep_direction[i]
                direction_ok = True
                if d == "bearish" and not asia_high_valid[i]:
                    direction_ok = False
                elif d == "bullish" and not asia_low_valid[i]:
                    direction_ok = False

                if direction_ok:
                    sweep_seen = True
                    last_sweep_dir = d
                    session_state = "WAIT_REACCEPT"

        if session_state == "WAIT_REACCEPT" and in_sweep_window:
            if re_acceptance[i]:
                reaccept_seen = True
                session_state = "WAIT_FVG"

        if session_state == "WAIT_FVG" and in_sweep_window:
            fvg_match = False
            if last_sweep_dir == "bullish" and fvg_bull_valid[i]:
                fvg_match = True
            elif last_sweep_dir == "bearish" and fvg_bear_valid[i]:
                fvg_match = True

            if fvg_match:
                session_state = "SETUP_VALID"
                setup_valid[i] = True
                setup_direction[i] = "long" if last_sweep_dir == "bullish" else "short"

        if not in_sweep_window and session_state in ("WAIT_SWEEP", "WAIT_REACCEPT", "WAIT_FVG"):
            session_state = "WINDOW_EXPIRED"

        state[i] = session_state

    df["asia_scalp_state"] = state
    df["asia_scalp_setup_valid"] = setup_valid
    df["asia_scalp_setup_direction"] = setup_direction

    return df


# =============================================================================
# VALIDATION
# =============================================================================


def _validate_input(df: pd.DataFrame) -> None:
    """Validate required columns from L1-L6 exist."""
    required = ["high", "low", "close", "asia_high", "asia_low"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for L7: {missing}")


# =============================================================================
# COLUMN MANIFEST
# =============================================================================

LAYER_7_COLUMNS = [
    "asia_ext_high_pips",
    "asia_ext_low_pips",
    "asia_ext_high_max_pips",
    "asia_ext_low_max_pips",
    "asia_high_direction_valid",
    "asia_low_direction_valid",
    "asia_sweep_high_valid",
    "asia_sweep_low_valid",
    "close_strictly_inside_asia",
    "re_acceptance",
    "fvg_asia_bull_valid",
    "fvg_asia_bear_valid",
    "fvg_untouched_pips",
    "asia_scalp_state",
    "asia_scalp_setup_valid",
    "asia_scalp_setup_direction",
]


def get_columns() -> list[str]:
    """Return columns this layer creates."""
    return LAYER_7_COLUMNS.copy()
