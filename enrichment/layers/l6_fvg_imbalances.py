"""
Layer 6: FVG & Imbalances — Phoenix Subsumption.

ORIGIN: NEX nex_lab/data/enrichment/displacement.py + mtf_fvg.py
SPRINT: S27.0
STATUS: SUBSUMED

Detects Fair Value Gaps (FVGs) and displacement candles.

FVG Definition (ICT):
- Bullish FVG: Candle A high < Candle C low (gap up)
- Bearish FVG: Candle A low > Candle C high (gap down)

Displacement = Institutional movement
- Large body relative to ATR
- Creates the void that FVG occupies

COLUMNS: 20 (12 displacement + 8 FVG)
DEPENDENCIES: Raw OHLC

FORBIDDEN:
- forward_fill
- auto_fix
- synthetic fills

INVARIANTS:
- INV-CONTRACT-1: deterministic
"""

import pandas as pd
import numpy as np
from typing import List


# =============================================================================
# DISPLACEMENT DETECTION
# =============================================================================

def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high = df['high']
    low = df['low']
    close = df['close'].shift(1)
    
    tr1 = high - low
    tr2 = abs(high - close)
    tr3 = abs(low - close)
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(span=period, adjust=False).mean()
    
    return atr


def _bars_since_event(event_series: pd.Series) -> pd.Series:
    """
    Calculate bars since last True event.
    
    NO forward_fill — explicit iteration.
    """
    n = len(event_series)
    bars_since = np.full(n, 9999, dtype=int)
    
    last_event_idx = None
    for i in range(n):
        if event_series.iloc[i]:
            last_event_idx = i
        if last_event_idx is not None:
            bars_since[i] = i - last_event_idx
    
    return pd.Series(bars_since, index=event_series.index)


# =============================================================================
# FVG DETECTION
# =============================================================================

def _detect_fvg(df: pd.DataFrame) -> dict:
    """
    Detect FVGs using ICT definition.
    
    Bullish FVG: Candle[i-2].high < Candle[i].low
    Bearish FVG: Candle[i-2].low > Candle[i].high
    
    Returns discrete FVG events (NO forward_fill).
    """
    n = len(df)
    
    fvg_bull = np.zeros(n, dtype=bool)
    fvg_bear = np.zeros(n, dtype=bool)
    fvg_bull_high = np.full(n, np.nan)
    fvg_bull_low = np.full(n, np.nan)
    fvg_bear_high = np.full(n, np.nan)
    fvg_bear_low = np.full(n, np.nan)
    
    highs = df['high'].values
    lows = df['low'].values
    
    for i in range(2, n):
        candle_a_high = highs[i-2]
        candle_a_low = lows[i-2]
        candle_c_high = highs[i]
        candle_c_low = lows[i]
        
        # Bullish FVG
        if candle_a_high < candle_c_low:
            fvg_bull[i] = True
            fvg_bull_high[i] = candle_c_low  # Top of gap
            fvg_bull_low[i] = candle_a_high   # Bottom of gap
        
        # Bearish FVG
        if candle_a_low > candle_c_high:
            fvg_bear[i] = True
            fvg_bear_high[i] = candle_a_low   # Top of gap
            fvg_bear_low[i] = candle_c_high   # Bottom of gap
    
    return {
        'fvg_bull': fvg_bull,
        'fvg_bear': fvg_bear,
        'fvg_bull_high': fvg_bull_high,
        'fvg_bull_low': fvg_bull_low,
        'fvg_bear_high': fvg_bear_high,
        'fvg_bear_low': fvg_bear_low,
    }


# =============================================================================
# MAIN ENRICHMENT
# =============================================================================

def enrich(df: pd.DataFrame, atr_period: int = 14) -> pd.DataFrame:
    """
    Add displacement and FVG columns.
    
    INV-CONTRACT-1: Deterministic.
    NO forward_fill.
    
    Args:
        df: DataFrame with OHLC
        atr_period: Period for ATR (default 14)
    
    Returns:
        DataFrame with 20 new columns
    """
    df = df.copy()
    
    _validate_input(df)
    
    # =========================================================================
    # ATR CALCULATION
    # =========================================================================
    
    atr_col = f'atr_{atr_period}'
    if atr_col not in df.columns:
        df[atr_col] = _calculate_atr(df, atr_period)
    
    # =========================================================================
    # BODY & RANGE METRICS (4 columns)
    # =========================================================================
    
    df['candle_body'] = abs(df['close'] - df['open'])
    df['candle_range'] = df['high'] - df['low']
    
    df['body_ratio'] = np.where(
        df['candle_range'] > 0,
        df['candle_body'] / df['candle_range'],
        0
    )
    
    df['atr_body_multiple'] = np.where(
        df[atr_col] > 0,
        df['candle_body'] / df[atr_col],
        0
    )
    
    # =========================================================================
    # DISPLACEMENT DETECTION (3 columns)
    # =========================================================================
    
    # Displacement = body > 1.5x ATR AND body_ratio > 0.6
    is_displacement = (df['atr_body_multiple'] > 1.5) & (df['body_ratio'] > 0.6)
    is_bullish = df['close'] > df['open']
    is_bearish = df['close'] < df['open']
    
    df['displacement_up'] = is_displacement & is_bullish
    df['displacement_down'] = is_displacement & is_bearish
    df['is_displacement'] = is_displacement
    
    # =========================================================================
    # DISPLACEMENT METRICS (5 columns)
    # =========================================================================
    
    df['displacement_pips'] = np.where(
        is_displacement,
        df['candle_body'] * 10000,
        0
    )
    
    df['displacement_atr_multiple'] = np.where(
        is_displacement,
        df['atr_body_multiple'],
        0
    )
    
    df['bars_since_displacement_up'] = _bars_since_event(df['displacement_up'])
    df['bars_since_displacement_down'] = _bars_since_event(df['displacement_down'])
    df['bars_since_any_displacement'] = np.minimum(
        df['bars_since_displacement_up'],
        df['bars_since_displacement_down']
    )
    
    # =========================================================================
    # FVG DETECTION (8 columns)
    # =========================================================================
    
    fvg = _detect_fvg(df)
    
    df['fvg_bull'] = fvg['fvg_bull']
    df['fvg_bear'] = fvg['fvg_bear']
    df['fvg_bull_high'] = fvg['fvg_bull_high']
    df['fvg_bull_low'] = fvg['fvg_bull_low']
    df['fvg_bear_high'] = fvg['fvg_bear_high']
    df['fvg_bear_low'] = fvg['fvg_bear_low']
    
    # FVG midpoint (CE - Consequent Encroachment)
    df['fvg_bull_ce'] = (df['fvg_bull_high'] + df['fvg_bull_low']) / 2
    df['fvg_bear_ce'] = (df['fvg_bear_high'] + df['fvg_bear_low']) / 2
    
    return df


# =============================================================================
# VALIDATION
# =============================================================================

def _validate_input(df: pd.DataFrame) -> None:
    """Validate required columns exist."""
    required = ['open', 'high', 'low', 'close']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


# =============================================================================
# COLUMN MANIFEST
# =============================================================================

LAYER_6_COLUMNS = [
    # Body & Range (4)
    'candle_body', 'candle_range', 'body_ratio', 'atr_body_multiple',
    # Displacement detection (3)
    'displacement_up', 'displacement_down', 'is_displacement',
    # Displacement metrics (5)
    'displacement_pips', 'displacement_atr_multiple',
    'bars_since_displacement_up', 'bars_since_displacement_down',
    'bars_since_any_displacement',
    # FVG (8)
    'fvg_bull', 'fvg_bear',
    'fvg_bull_high', 'fvg_bull_low', 'fvg_bull_ce',
    'fvg_bear_high', 'fvg_bear_low', 'fvg_bear_ce',
]


def get_columns() -> List[str]:
    """Return columns this layer creates."""
    return LAYER_6_COLUMNS.copy()
