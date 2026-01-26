"""
Layer 4: Structure Breaks — Phoenix Subsumption.

ORIGIN: NEX nex_lab/data/enrichment/structure.py
SPRINT: S27.0
STATUS: SUBSUMED

Detects swing structure (HH/HL/LH/LL) to determine order flow direction.

Order Flow = "What is price respecting?"
- HH + HL = Bullish order flow
- LH + LL = Bearish order flow

COLUMNS: 13 (pair structure only, DXY coupling removed)
DEPENDENCIES: Raw OHLC

FORBIDDEN:
- forward_fill (groupby broadcast only)
- DXY coupling (NEX had this, Phoenix removes it)
- auto_fix

INVARIANTS:
- INV-CONTRACT-1: deterministic
"""

import pandas as pd
import numpy as np
from typing import List, Tuple


# =============================================================================
# SWING DETECTION
# =============================================================================

def _detect_swings(
    highs: np.ndarray,
    lows: np.ndarray,
    lookback: int = 3
) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """
    Detect swing highs and lows using local extrema.
    
    INV-CONTRACT-1: Deterministic.
    
    Swing High: high[i] is highest in window [i-lookback, i+lookback]
    Swing Low: low[i] is lowest in window [i-lookback, i+lookback]
    """
    n = len(highs)
    swing_highs = []
    swing_lows = []
    
    for i in range(lookback, n - lookback):
        # Swing high if highest in window
        window_high = highs[i-lookback:i+lookback+1]
        if highs[i] == max(window_high):
            swing_highs.append((i, highs[i]))
        
        # Swing low if lowest in window
        window_low = lows[i-lookback:i+lookback+1]
        if lows[i] == min(window_low):
            swing_lows.append((i, lows[i]))
    
    return swing_highs, swing_lows


# =============================================================================
# MAIN ENRICHMENT
# =============================================================================

def enrich(df: pd.DataFrame, symbol: str = 'EURUSD') -> pd.DataFrame:
    """
    Add structure columns.
    
    INV-CONTRACT-1: Deterministic.
    NO forward_fill — state tracked per-bar.
    NO DXY coupling — removed from Phoenix.
    
    Args:
        df: DataFrame with OHLC
        symbol: Trading symbol
    
    Returns:
        DataFrame with 13 new columns
    """
    df = df.copy()
    
    _validate_input(df)
    
    highs = df['high'].values
    lows = df['low'].values
    n = len(df)
    
    # Initialize arrays
    swing_high_arr = np.full(n, np.nan)
    swing_low_arr = np.full(n, np.nan)
    swing_high_idx_arr = np.full(n, np.nan)
    swing_low_idx_arr = np.full(n, np.nan)
    
    is_higher_high = np.zeros(n, dtype=bool)
    is_lower_high = np.zeros(n, dtype=bool)
    is_higher_low = np.zeros(n, dtype=bool)
    is_lower_low = np.zeros(n, dtype=bool)
    
    order_flow_arr = np.array(['neutral'] * n, dtype=object)
    
    structure_break_up = np.zeros(n, dtype=bool)
    structure_break_down = np.zeros(n, dtype=bool)
    structure_trend_arr = np.array(['neutral'] * n, dtype=object)
    
    # Detect swings
    swing_highs, swing_lows = _detect_swings(highs, lows, lookback=3)
    
    # Track state (NO ffill — explicit state machine)
    prev_swing_high = None
    prev_swing_low = None
    current_swing_high = np.nan
    current_swing_low = np.nan
    current_swing_high_idx = np.nan
    current_swing_low_idx = np.nan
    last_high_comparison = None  # 'HH' or 'LH'
    last_low_comparison = None   # 'HL' or 'LL'
    
    sh_ptr = 0
    sl_ptr = 0
    
    # Process each bar
    for i in range(n):
        # Check if new swing high at this bar
        while sh_ptr < len(swing_highs) and swing_highs[sh_ptr][0] <= i:
            swing_idx, swing_price = swing_highs[sh_ptr]
            
            if prev_swing_high is not None:
                if swing_price > prev_swing_high:
                    is_higher_high[swing_idx] = True
                    last_high_comparison = 'HH'
                    # Structure break up when HH confirmed
                    structure_break_up[swing_idx] = True
                else:
                    is_lower_high[swing_idx] = True
                    last_high_comparison = 'LH'
            
            prev_swing_high = swing_price
            current_swing_high = swing_price
            current_swing_high_idx = float(swing_idx)
            sh_ptr += 1
        
        # Check if new swing low at this bar
        while sl_ptr < len(swing_lows) and swing_lows[sl_ptr][0] <= i:
            swing_idx, swing_price = swing_lows[sl_ptr]
            
            if prev_swing_low is not None:
                if swing_price > prev_swing_low:
                    is_higher_low[swing_idx] = True
                    last_low_comparison = 'HL'
                else:
                    is_lower_low[swing_idx] = True
                    last_low_comparison = 'LL'
                    # Structure break down when LL confirmed
                    structure_break_down[swing_idx] = True
            
            prev_swing_low = swing_price
            current_swing_low = swing_price
            current_swing_low_idx = float(swing_idx)
            sl_ptr += 1
        
        # Store current swing values
        swing_high_arr[i] = current_swing_high
        swing_low_arr[i] = current_swing_low
        swing_high_idx_arr[i] = current_swing_high_idx
        swing_low_idx_arr[i] = current_swing_low_idx
        
        # Determine order flow
        if last_high_comparison and last_low_comparison:
            if last_high_comparison == 'HH' and last_low_comparison == 'HL':
                order_flow_arr[i] = 'bullish'
                structure_trend_arr[i] = 'bullish'
            elif last_high_comparison == 'LH' and last_low_comparison == 'LL':
                order_flow_arr[i] = 'bearish'
                structure_trend_arr[i] = 'bearish'
            else:
                order_flow_arr[i] = 'mixed'
                structure_trend_arr[i] = 'mixed'
    
    # Assign columns
    df['swing_high'] = swing_high_arr
    df['swing_low'] = swing_low_arr
    df['swing_high_idx'] = swing_high_idx_arr
    df['swing_low_idx'] = swing_low_idx_arr
    df['is_higher_high'] = is_higher_high
    df['is_lower_high'] = is_lower_high
    df['is_higher_low'] = is_higher_low
    df['is_lower_low'] = is_lower_low
    df['order_flow'] = order_flow_arr
    df['structure_break_up'] = structure_break_up
    df['structure_break_down'] = structure_break_down
    df['structure_trend'] = structure_trend_arr
    df['structure_confirmed'] = structure_break_up | structure_break_down
    
    return df


# =============================================================================
# VALIDATION
# =============================================================================

def _validate_input(df: pd.DataFrame) -> None:
    """Validate required columns exist."""
    required = ['high', 'low', 'close']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


# =============================================================================
# COLUMN MANIFEST
# =============================================================================

LAYER_4_COLUMNS = [
    # Swing tracking (4)
    'swing_high', 'swing_low', 'swing_high_idx', 'swing_low_idx',
    # HH/HL/LH/LL (4)
    'is_higher_high', 'is_lower_high', 'is_higher_low', 'is_lower_low',
    # Order flow (1)
    'order_flow',
    # Structure breaks (4)
    'structure_break_up', 'structure_break_down', 
    'structure_trend', 'structure_confirmed',
]


def get_columns() -> List[str]:
    """Return columns this layer creates."""
    return LAYER_4_COLUMNS.copy()
