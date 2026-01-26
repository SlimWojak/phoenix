"""
Layer 3: Sweeps — Phoenix Subsumption.

ORIGIN: NEX nex_lab/data/enrichment/sweeps.py
SPRINT: S27.0
STATUS: SUBSUMED

Detects liquidity sweeps across sessions.

The Sweep Formula (ALL THREE REQUIRED):
    Valid Sweep = Liquidity Taken + Swept INTO HTF PDA + Reversal Confirmation

This layer stores RAW sweep events. Strategy Evaluator validates complete formula.

COLUMNS: 37
DEPENDENCIES: L1 (sessions), L2 (pdh, pdl, pwh, pwl)

FORBIDDEN:
- forward_fill
- auto_fix
- synthetic fills

INVARIANTS:
- INV-CONTRACT-1: deterministic
"""

import pandas as pd
import numpy as np
from typing import List, Tuple


# =============================================================================
# CONSTANTS
# =============================================================================

def _pip_size(symbol: str) -> float:
    """Get pip size for symbol."""
    return 0.01 if 'JPY' in symbol.upper() else 0.0001


# =============================================================================
# TIMING HELPERS
# =============================================================================

def _get_timing_quality(hour_ny: int) -> Tuple[bool, bool, str, int]:
    """
    Determine sweep timing priority.
    
    Returns: (during_kz, during_session, timing_quality, timing_score)
    """
    # Kill Zones (score 3)
    if hour_ny == 20:  # Asia KZ
        return True, True, 'kz', 3
    elif hour_ny == 3:  # LOKZ
        return True, True, 'kz', 3
    elif hour_ny == 8:  # NYKZ
        return True, True, 'kz', 3
    
    # Main Sessions (score 2)
    elif hour_ny >= 19 or hour_ny < 1:  # Asia
        return False, True, 'session', 2
    elif 2 <= hour_ny < 5:  # London
        return False, True, 'session', 2
    elif 7 <= hour_ny < 10:  # NY
        return False, True, 'session', 2
    
    # Off-session (score 1)
    return False, False, 'off_session', 1


def _classify_extension(extension_pips: float) -> Tuple[str, bool]:
    """
    Classify sweep extension.
    
    Returns: (classification, is_valid)
    - tap: < 5 pips (not valid)
    - sweep: 5-20 pips (VALID)
    - displacement: > 20 pips (not valid)
    """
    if extension_pips < 5:
        return 'tap', False
    elif extension_pips <= 20:
        return 'sweep', True
    else:
        return 'displacement', False


# =============================================================================
# MAIN ENRICHMENT
# =============================================================================

def enrich(df: pd.DataFrame, symbol: str = 'EURUSD') -> pd.DataFrame:
    """
    Add sweep detection columns.
    
    INV-CONTRACT-1: Deterministic.
    NO forward_fill.
    
    Args:
        df: DataFrame with L1/L2 columns
        symbol: Trading pair
    
    Returns:
        DataFrame with 37 new columns
    """
    df = df.copy()
    
    _validate_input(df)
    
    pip = _pip_size(symbol)
    n = len(df)
    
    hour_ny = df['hour_ny'].values
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    
    # Get reference levels from L2
    pdh = df['pdh'].values if 'pdh' in df.columns else np.full(n, np.nan)
    pdl = df['pdl'].values if 'pdl' in df.columns else np.full(n, np.nan)
    pwh = df['pwh'].values if 'pwh' in df.columns else np.full(n, np.nan)
    pwl = df['pwl'].values if 'pwl' in df.columns else np.full(n, np.nan)
    asia_high = df['asia_high'].values if 'asia_high' in df.columns else np.full(n, np.nan)
    asia_low = df['asia_low'].values if 'asia_low' in df.columns else np.full(n, np.nan)
    
    # Initialize columns
    sweep_detected = np.zeros(n, dtype=bool)
    sweep_direction = np.full(n, None, dtype=object)
    sweep_target_type = np.full(n, None, dtype=object)
    sweep_target_level = np.full(n, np.nan)
    sweep_extension_pips = np.full(n, np.nan)
    sweep_extension_class = np.full(n, None, dtype=object)
    sweep_is_valid = np.zeros(n, dtype=bool)
    sweep_during_kz = np.zeros(n, dtype=bool)
    sweep_during_session = np.zeros(n, dtype=bool)
    sweep_timing_quality = np.full(n, None, dtype=object)
    sweep_timing_score = np.zeros(n, dtype=int)
    sweep_reversal_bars = np.zeros(n, dtype=int)
    sweep_into_pda = np.zeros(n, dtype=bool)
    sweep_mss_confirmed = np.zeros(n, dtype=bool)
    sweep_displacement_confirmed = np.zeros(n, dtype=bool)
    sweep_fvg_created = np.zeros(n, dtype=bool)
    sweep_is_setup = np.zeros(n, dtype=bool)
    
    # Scan for sweeps
    for i in range(1, n):
        # Check if high swept any level
        swept_high = False
        target_type = None
        target_level = np.nan
        direction = None
        
        # PDH sweep (bearish setup)
        if not np.isnan(pdh[i]) and high[i] > pdh[i]:
            swept_high = True
            target_type = 'pdh'
            target_level = pdh[i]
            direction = 'bearish'
        # PWH sweep
        elif not np.isnan(pwh[i]) and high[i] > pwh[i]:
            swept_high = True
            target_type = 'pwh'
            target_level = pwh[i]
            direction = 'bearish'
        # Asia high sweep
        elif not np.isnan(asia_high[i]) and high[i] > asia_high[i]:
            swept_high = True
            target_type = 'asia_high'
            target_level = asia_high[i]
            direction = 'bearish'
        
        # Check if low swept any level
        swept_low = False
        if not swept_high:
            # PDL sweep (bullish setup)
            if not np.isnan(pdl[i]) and low[i] < pdl[i]:
                swept_low = True
                target_type = 'pdl'
                target_level = pdl[i]
                direction = 'bullish'
            # PWL sweep
            elif not np.isnan(pwl[i]) and low[i] < pwl[i]:
                swept_low = True
                target_type = 'pwl'
                target_level = pwl[i]
                direction = 'bullish'
            # Asia low sweep
            elif not np.isnan(asia_low[i]) and low[i] < asia_low[i]:
                swept_low = True
                target_type = 'asia_low'
                target_level = asia_low[i]
                direction = 'bullish'
        
        if swept_high or swept_low:
            sweep_detected[i] = True
            sweep_direction[i] = direction
            sweep_target_type[i] = target_type
            sweep_target_level[i] = target_level
            
            # Calculate extension
            if swept_high:
                ext = (high[i] - target_level) / pip
            else:
                ext = (target_level - low[i]) / pip
            
            sweep_extension_pips[i] = ext
            ext_class, is_valid = _classify_extension(ext)
            sweep_extension_class[i] = ext_class
            sweep_is_valid[i] = is_valid
            
            # Timing quality
            during_kz, during_session, timing_q, timing_s = _get_timing_quality(hour_ny[i])
            sweep_during_kz[i] = during_kz
            sweep_during_session[i] = during_session
            sweep_timing_quality[i] = timing_q
            sweep_timing_score[i] = timing_s
            
            # Setup check (sweep + valid + good timing)
            sweep_is_setup[i] = is_valid and during_session
    
    # Assign to dataframe
    df['sweep_detected'] = sweep_detected
    df['sweep_direction'] = sweep_direction
    df['sweep_target_type'] = sweep_target_type
    df['sweep_target_level'] = sweep_target_level
    df['sweep_extension_pips'] = sweep_extension_pips
    df['sweep_extension_class'] = sweep_extension_class
    df['sweep_is_valid'] = sweep_is_valid
    df['sweep_during_kz'] = sweep_during_kz
    df['sweep_during_session'] = sweep_during_session
    df['sweep_timing_quality'] = sweep_timing_quality
    df['sweep_timing_score'] = sweep_timing_score
    df['sweep_reversal_bars'] = sweep_reversal_bars
    df['sweep_into_pda'] = sweep_into_pda
    df['sweep_mss_confirmed'] = sweep_mss_confirmed
    df['sweep_displacement_confirmed'] = sweep_displacement_confirmed
    df['sweep_fvg_created'] = sweep_fvg_created
    df['sweep_is_setup'] = sweep_is_setup
    
    # Add liquidity pool tracking columns (20)
    df = _add_liquidity_pools(df)
    
    return df


# =============================================================================
# LIQUIDITY POOLS
# =============================================================================

def _add_liquidity_pools(df: pd.DataFrame) -> pd.DataFrame:
    """Add liquidity pool tracking columns."""
    n = len(df)
    
    # Session liquidity (carried forward within session, NOT ffill across days)
    # These are reference levels, computed per-bar from groupby
    
    # Use existing session levels from L2 if available
    for session in ['asia', 'london', 'ny']:
        high_col = f'{session[:3]}_session_high' if session != 'asia' else 'asia_high'
        low_col = f'{session[:3]}_session_low' if session != 'asia' else 'asia_low'
        
        if high_col not in df.columns:
            df[f'liq_{session}_high'] = np.nan
            df[f'liq_{session}_low'] = np.nan
        else:
            df[f'liq_{session}_high'] = df[high_col]
            df[f'liq_{session}_low'] = df[low_col]
    
    # PDH/PDL liquidity
    df['liq_pdh'] = df['pdh'] if 'pdh' in df.columns else np.nan
    df['liq_pdl'] = df['pdl'] if 'pdl' in df.columns else np.nan
    
    # PWH/PWL liquidity
    df['liq_pwh'] = df['pwh'] if 'pwh' in df.columns else np.nan
    df['liq_pwl'] = df['pwl'] if 'pwl' in df.columns else np.nan
    
    # Pool count (number of untested levels)
    df['liq_pool_count_above'] = (
        (~df['liq_pdh'].isna()).astype(int) +
        (~df['liq_pwh'].isna()).astype(int) +
        (~df['liq_asia_high'].isna()).astype(int)
    )
    df['liq_pool_count_below'] = (
        (~df['liq_pdl'].isna()).astype(int) +
        (~df['liq_pwl'].isna()).astype(int) +
        (~df['liq_asia_low'].isna()).astype(int)
    )
    
    # Nearest liquidity
    df['nearest_liq_above'] = df[['liq_pdh', 'liq_pwh', 'liq_asia_high']].min(axis=1)
    df['nearest_liq_below'] = df[['liq_pdl', 'liq_pwl', 'liq_asia_low']].max(axis=1)
    
    # Distance to nearest
    df['dist_to_nearest_above'] = df['nearest_liq_above'] - df['close']
    df['dist_to_nearest_below'] = df['close'] - df['nearest_liq_below']
    
    return df


# =============================================================================
# VALIDATION
# =============================================================================

def _validate_input(df: pd.DataFrame) -> None:
    """Validate L1/L2 columns exist."""
    required = ['hour_ny', 'high', 'low', 'close']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


# =============================================================================
# COLUMN MANIFEST
# =============================================================================

LAYER_3_COLUMNS = [
    # Core sweep (17)
    'sweep_detected', 'sweep_direction', 'sweep_target_type', 'sweep_target_level',
    'sweep_extension_pips', 'sweep_extension_class', 'sweep_is_valid',
    'sweep_during_kz', 'sweep_during_session', 'sweep_timing_quality', 'sweep_timing_score',
    'sweep_reversal_bars', 'sweep_into_pda', 'sweep_mss_confirmed',
    'sweep_displacement_confirmed', 'sweep_fvg_created', 'sweep_is_setup',
    # Liquidity pools (20)
    'liq_asia_high', 'liq_asia_low',
    'liq_london_high', 'liq_london_low',
    'liq_ny_high', 'liq_ny_low',
    'liq_pdh', 'liq_pdl',
    'liq_pwh', 'liq_pwl',
    'liq_pool_count_above', 'liq_pool_count_below',
    'nearest_liq_above', 'nearest_liq_below',
    'dist_to_nearest_above', 'dist_to_nearest_below',
]


def get_columns() -> List[str]:
    """Return columns this layer creates."""
    return LAYER_3_COLUMNS.copy()
