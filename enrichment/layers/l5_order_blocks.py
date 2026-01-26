"""
Layer 5: Order Blocks — Phoenix Subsumption.

ORIGIN: NEX nex_lab/data/enrichment/order_blocks.py
SPRINT: S27.0
STATUS: SUBSUMED (REFACTORED)

Detects Order Blocks - Olya's #1 PDA priority.

ICT Definition:
- BULLISH OB: Last DOWN candle before bullish displacement
- BEARISH OB: Last UP candle before bearish displacement

OB Zone:
- High/Low of OB candle define the zone
- CE (Consequent Encroachment) = 50% of OB = optimal entry

COLUMNS: 14 (single timeframe, mitigated tracking)
DEPENDENCIES: L6 (displacement)

FORBIDDEN:
- forward_fill / ffill (NEX used method='ffill', REMOVED)
- Reindex with ffill
- auto_fix

REFACTOR NOTE:
NEX used `df_obs.reindex(idx_1m, method='ffill')` — THIS IS FORBIDDEN.
Phoenix uses explicit OB tracking per bar with state machine.

INVARIANTS:
- INV-CONTRACT-1: deterministic
- INV-DATA-2: no synthetic without flag
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict


# =============================================================================
# OB DETECTION
# =============================================================================

def _detect_order_blocks(
    df: pd.DataFrame,
    lookback: int = 10
) -> Dict[str, List[dict]]:
    """
    Detect Order Blocks.
    
    OB forms when:
    1. Displacement occurs (strong move)
    2. Last opposing candle before displacement = OB
    
    NO forward_fill — returns discrete OB events.
    """
    obs_bull = []
    obs_bear = []
    
    if len(df) < 5:
        return {'bull': obs_bull, 'bear': obs_bear}
    
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    
    # Check for displacement column (from L6)
    if 'is_displacement' in df.columns:
        is_disp = df['is_displacement'].values
        disp_up = df['displacement_up'].values if 'displacement_up' in df.columns else (closes > opens) & is_disp
        disp_down = df['displacement_down'].values if 'displacement_down' in df.columns else (closes < opens) & is_disp
    else:
        # Fallback: detect displacement inline
        body = np.abs(closes - opens)
        range_ = highs - lows
        body_ratio = np.where(range_ > 0, body / range_, 0)
        
        # Simple displacement: body > 70% of range
        is_disp = body_ratio > 0.7
        disp_up = is_disp & (closes > opens)
        disp_down = is_disp & (closes < opens)
    
    for i in range(2, len(df)):
        # BULLISH OB: Last bearish candle before bullish displacement
        if disp_up[i]:
            for j in range(i-1, max(i-lookback, 0), -1):
                if closes[j] < opens[j]:  # Bearish candle
                    obs_bull.append({
                        'idx': i,
                        'ob_idx': j,
                        'high': highs[j],
                        'low': lows[j],
                        'ce': (highs[j] + lows[j]) / 2,
                    })
                    break
        
        # BEARISH OB: Last bullish candle before bearish displacement
        if disp_down[i]:
            for j in range(i-1, max(i-lookback, 0), -1):
                if closes[j] > opens[j]:  # Bullish candle
                    obs_bear.append({
                        'idx': i,
                        'ob_idx': j,
                        'high': highs[j],
                        'low': lows[j],
                        'ce': (highs[j] + lows[j]) / 2,
                    })
                    break
    
    return {'bull': obs_bull, 'bear': obs_bear}


# =============================================================================
# MAIN ENRICHMENT
# =============================================================================

def enrich(df: pd.DataFrame, symbol: str = 'EURUSD') -> pd.DataFrame:
    """
    Add order block columns.
    
    INV-CONTRACT-1: Deterministic.
    NO forward_fill — uses explicit state machine.
    
    CRITICAL REFACTOR:
    NEX used `reindex(method='ffill')` — FORBIDDEN in Phoenix.
    Instead, we track active OB per bar explicitly.
    
    Args:
        df: DataFrame with OHLC and L6 columns
        symbol: Trading symbol
    
    Returns:
        DataFrame with 14 new columns
    """
    df = df.copy()
    
    _validate_input(df)
    
    n = len(df)
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    
    # Detect OBs
    obs = _detect_order_blocks(df)
    
    # Initialize arrays
    ob_bull_high = np.full(n, np.nan)
    ob_bull_low = np.full(n, np.nan)
    ob_bull_ce = np.full(n, np.nan)
    ob_bull_active = np.zeros(n, dtype=bool)
    ob_bull_mitigated = np.zeros(n, dtype=bool)
    ob_bull_age = np.zeros(n, dtype=int)
    ob_bull_touches = np.zeros(n, dtype=int)
    
    ob_bear_high = np.full(n, np.nan)
    ob_bear_low = np.full(n, np.nan)
    ob_bear_ce = np.full(n, np.nan)
    ob_bear_active = np.zeros(n, dtype=bool)
    ob_bear_mitigated = np.zeros(n, dtype=bool)
    ob_bear_age = np.zeros(n, dtype=int)
    ob_bear_touches = np.zeros(n, dtype=int)
    
    # Track active OBs (NO ffill — explicit state)
    active_bull_obs = []  # List of {'high', 'low', 'ce', 'start_idx', 'touches'}
    active_bear_obs = []
    
    # Create lookup for OB formation bars
    bull_ob_map = {ob['idx']: ob for ob in obs['bull']}
    bear_ob_map = {ob['idx']: ob for ob in obs['bear']}
    
    # Process each bar
    for i in range(n):
        # Add new OBs formed at this bar
        if i in bull_ob_map:
            ob = bull_ob_map[i]
            active_bull_obs.append({
                'high': ob['high'],
                'low': ob['low'],
                'ce': ob['ce'],
                'start_idx': i,
                'touches': 0
            })
        
        if i in bear_ob_map:
            ob = bear_ob_map[i]
            active_bear_obs.append({
                'high': ob['high'],
                'low': ob['low'],
                'ce': ob['ce'],
                'start_idx': i,
                'touches': 0
            })
        
        # Check BULLISH OBs
        mitigated_bull = []
        for j, ob in enumerate(active_bull_obs):
            # Check if price in OB zone
            if lows[i] <= ob['high'] and highs[i] >= ob['low']:
                ob['touches'] += 1
            
            # Check mitigation (price closes below OB low)
            if closes[i] < ob['low']:
                mitigated_bull.append(j)
                ob_bull_mitigated[i] = True
        
        # Remove mitigated OBs
        for j in reversed(mitigated_bull):
            active_bull_obs.pop(j)
        
        # Store most recent active bull OB (if any)
        if active_bull_obs:
            latest = active_bull_obs[-1]
            ob_bull_high[i] = latest['high']
            ob_bull_low[i] = latest['low']
            ob_bull_ce[i] = latest['ce']
            ob_bull_active[i] = True
            ob_bull_age[i] = i - latest['start_idx']
            ob_bull_touches[i] = latest['touches']
        
        # Check BEARISH OBs
        mitigated_bear = []
        for j, ob in enumerate(active_bear_obs):
            # Check if price in OB zone
            if lows[i] <= ob['high'] and highs[i] >= ob['low']:
                ob['touches'] += 1
            
            # Check mitigation (price closes above OB high)
            if closes[i] > ob['high']:
                mitigated_bear.append(j)
                ob_bear_mitigated[i] = True
        
        # Remove mitigated OBs
        for j in reversed(mitigated_bear):
            active_bear_obs.pop(j)
        
        # Store most recent active bear OB (if any)
        if active_bear_obs:
            latest = active_bear_obs[-1]
            ob_bear_high[i] = latest['high']
            ob_bear_low[i] = latest['low']
            ob_bear_ce[i] = latest['ce']
            ob_bear_active[i] = True
            ob_bear_age[i] = i - latest['start_idx']
            ob_bear_touches[i] = latest['touches']
    
    # Assign columns
    df['ob_bull_high'] = ob_bull_high
    df['ob_bull_low'] = ob_bull_low
    df['ob_bull_ce'] = ob_bull_ce
    df['ob_bull_active'] = ob_bull_active
    df['ob_bull_mitigated'] = ob_bull_mitigated
    df['ob_bull_age'] = ob_bull_age
    df['ob_bull_touches'] = ob_bull_touches
    
    df['ob_bear_high'] = ob_bear_high
    df['ob_bear_low'] = ob_bear_low
    df['ob_bear_ce'] = ob_bear_ce
    df['ob_bear_active'] = ob_bear_active
    df['ob_bear_mitigated'] = ob_bear_mitigated
    df['ob_bear_age'] = ob_bear_age
    df['ob_bear_touches'] = ob_bear_touches
    
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

LAYER_5_COLUMNS = [
    # Bullish OB (7)
    'ob_bull_high', 'ob_bull_low', 'ob_bull_ce',
    'ob_bull_active', 'ob_bull_mitigated',
    'ob_bull_age', 'ob_bull_touches',
    # Bearish OB (7)
    'ob_bear_high', 'ob_bear_low', 'ob_bear_ce',
    'ob_bear_active', 'ob_bear_mitigated',
    'ob_bear_age', 'ob_bear_touches',
]


def get_columns() -> List[str]:
    """Return columns this layer creates."""
    return LAYER_5_COLUMNS.copy()
