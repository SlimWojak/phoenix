"""
Shared fixtures for S51 DRIVESHAFT tests.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd


def _make_bar(
    ts: datetime,
    o: float = 1.0850,
    h: float = 1.0855,
    l: float = 1.0845,
    c: float = 1.0852,
    vol: int = 1000,
) -> dict:
    return {
        "timestamp": ts,
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "volume": vol,
    }


def make_5m_bars(
    start: datetime,
    count: int,
    base_price: float = 1.0850,
    noise: float = 0.0005,
) -> pd.DataFrame:
    """Generate synthetic 5m bars for testing."""
    rng = np.random.RandomState(42)
    bars = []
    price = base_price

    for i in range(count):
        ts = start + timedelta(minutes=5 * i)
        delta = rng.uniform(-noise, noise)
        o = price
        c = price + delta
        h = max(o, c) + abs(rng.uniform(0, noise / 2))
        l = min(o, c) - abs(rng.uniform(0, noise / 2))
        bars.append(_make_bar(ts, o, h, l, c))
        price = c

    df = pd.DataFrame(bars)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def make_asia_scalp_scenario(
    asia_range_pips: float = 20.0,
    sweep_direction: str = "bullish",
    sweep_extension_pips: float = 10.0,
    has_re_acceptance: bool = True,
    has_fvg: bool = True,
    fvg_gap_pips: float = 2.0,
    candle_c_inside: bool = True,
) -> pd.DataFrame:
    """
    Build a synthetic enriched DataFrame for a specific Asia Scalp scenario.

    Timestamps use UTC that map to correct NY hours:
    - EST = UTC-5, so 19:00 NY = 00:00 UTC next day
    - Sweep window 00:00-04:00 NY = 05:00-09:00 UTC

    Returns a DataFrame with all L1-L7 columns pre-populated.
    """
    pip = 0.0001
    base = 1.0850
    asia_high = base + (asia_range_pips / 2) * pip
    asia_low = base - (asia_range_pips / 2) * pip

    # Asia session: 19:00-23:59 NY = 00:00-04:59 UTC (next day in EST)
    asia_start_utc = datetime(2026, 2, 21, 0, 0, tzinfo=UTC)  # = 19:00 NY Feb 20
    bars = []

    for i in range(60):
        ts = asia_start_utc + timedelta(minutes=5 * i)
        c = base + np.random.RandomState(i).uniform(-0.0002, 0.0002)
        bars.append(_make_bar(ts, base, asia_high - pip, asia_low + pip, c))

    # Sweep window: 00:00-04:00 NY = 05:00-09:00 UTC
    sweep_start_utc = datetime(2026, 2, 21, 5, 0, tzinfo=UTC)  # = 00:00 NY Feb 21
    for i in range(48):
        ts = sweep_start_utc + timedelta(minutes=5 * i)
        c = base
        h = base + 0.0002
        l = base - 0.0002
        bars.append(_make_bar(ts, base, h, l, c))

    df = pd.DataFrame(bars)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    n = len(df)
    ny_hours = df["timestamp"].dt.tz_convert("America/New_York")
    df["hour_ny"] = ny_hours.dt.hour
    df["trading_day"] = ny_hours.apply(
        lambda x: x.date() if x.hour >= 17 else (x - timedelta(days=1)).date()
    )
    df["session_name"] = "off_session"
    df.loc[df["hour_ny"] >= 19, "session_name"] = "asia"
    df.loc[(df["hour_ny"] >= 2) & (df["hour_ny"] <= 4), "session_name"] = "london"

    df["is_asia_session"] = df["hour_ny"] >= 19
    df["is_london_session"] = (df["hour_ny"] >= 2) & (df["hour_ny"] <= 4)
    df["is_ny_session"] = (df["hour_ny"] >= 7) & (df["hour_ny"] <= 9)
    df["kz_active"] = False

    df["asia_high"] = asia_high
    df["asia_low"] = asia_low
    df["asia_range"] = asia_high - asia_low
    df["asia_range_pips"] = asia_range_pips

    df["order_flow"] = "neutral"
    df["structure_trend"] = "neutral"
    df["structure_confirmed"] = False

    df["sweep_detected"] = False
    df["sweep_direction"] = None
    df["sweep_extension_pips"] = np.nan
    df["sweep_target_type"] = None
    df["sweep_is_valid"] = False

    # Place sweep at bar 70 (inside sweep window 00:00-04:00 NY)
    sweep_bar = 70
    if sweep_direction and sweep_extension_pips:
        df.loc[sweep_bar, "sweep_detected"] = True
        df.loc[sweep_bar, "sweep_direction"] = sweep_direction
        df.loc[sweep_bar, "sweep_extension_pips"] = sweep_extension_pips
        df.loc[sweep_bar, "sweep_is_valid"] = 1.0 <= sweep_extension_pips <= 20.0

        if sweep_direction == "bullish":
            df.loc[sweep_bar, "sweep_target_type"] = "asia_low"
            ext_price = asia_low - sweep_extension_pips * pip
            df.loc[sweep_bar, "low"] = ext_price
        else:
            df.loc[sweep_bar, "sweep_target_type"] = "asia_high"
            ext_price = asia_high + sweep_extension_pips * pip
            df.loc[sweep_bar, "high"] = ext_price

    df["fvg_bull"] = False
    df["fvg_bear"] = False
    df["fvg_bull_high"] = np.nan
    df["fvg_bull_low"] = np.nan
    df["fvg_bear_high"] = np.nan
    df["fvg_bear_low"] = np.nan

    df["displacement_pips"] = 0.0
    df["is_displacement"] = False

    # Place FVG at bar 75 (inside sweep window)
    fvg_bar = 75
    if has_fvg:
        if sweep_direction == "bullish":
            df.loc[fvg_bar, "fvg_bull"] = True
            df.loc[fvg_bar, "fvg_bull_high"] = base + fvg_gap_pips * pip / 2
            df.loc[fvg_bar, "fvg_bull_low"] = base - fvg_gap_pips * pip / 2
        else:
            df.loc[fvg_bar, "fvg_bear"] = True
            df.loc[fvg_bar, "fvg_bear_high"] = base + fvg_gap_pips * pip / 2
            df.loc[fvg_bar, "fvg_bear_low"] = base - fvg_gap_pips * pip / 2

    if candle_c_inside:
        df.loc[fvg_bar, "close"] = base
    else:
        df.loc[fvg_bar, "close"] = asia_high + pip

    df["close_strictly_inside_asia"] = (df["close"] > asia_low) & (df["close"] < asia_high)
    df["re_acceptance"] = False
    if has_re_acceptance and sweep_bar < n:
        for idx in range(sweep_bar + 1, min(sweep_bar + 10, n)):
            if df.loc[idx, "close_strictly_inside_asia"]:
                df.loc[idx, "re_acceptance"] = True
                break

    return df
