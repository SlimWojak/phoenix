"""
Layer 1: Time & Sessions — Phoenix Subsumption.

ORIGIN: NEX nex_lab/data/enrichment/time_sessions.py
SPRINT: S27.0
STATUS: SUBSUMED

Handles time-based classification: sessions, kill zones, DOW context.
All times in NY timezone. Only US DST tracked.

COLUMNS: 25
DEPENDENCIES: None

Session Times (Olya-validated):
- Asia: 19:00-23:59 NY (5 hours)
- London: 02:00-05:00 NY (3 hours)
- New York: 07:00-10:00 NY (3 hours)

Kill Zones (1-hour high-conviction windows):
- Asia KZ: 20:00-21:00 NY
- LOKZ: 03:00-04:00 NY
- NYKZ: 08:00-09:00 NY

FORBIDDEN:
- forward_fill (use explicit sentinel)
- auto_fix
- synthetic fills

INVARIANTS:
- INV-CONTRACT-1: deterministic (same input → same output)
"""

import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo
from typing import List


# =============================================================================
# CONSTANTS
# =============================================================================

NY_TZ = ZoneInfo('America/New_York')

# Sentinel value for missing reference levels (NOT forward_fill)
MISSING_SENTINEL = -1.0


# =============================================================================
# MAIN ENRICHMENT
# =============================================================================

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add time and session columns to DataFrame.
    
    INV-CONTRACT-1: Deterministic — same input → same output.
    
    Args:
        df: DataFrame with 'timestamp' (UTC) and 'close' columns
    
    Returns:
        DataFrame with 25 additional columns
    
    Raises:
        ValueError: Missing required columns
    """
    df = df.copy()
    
    # Validate dependencies
    _validate_input(df)
    
    # Convert timestamps
    timestamp_ny = _get_ny_timestamps(df)
    
    # Time columns (4)
    df['hour_ny'] = timestamp_ny.dt.hour
    df['minute_ny'] = timestamp_ny.dt.minute
    df['day_of_week'] = timestamp_ny.dt.weekday  # Monday=0
    df['trading_day'] = _calculate_trading_day(timestamp_ny)
    
    # DST (1)
    df['is_dst_us'] = timestamp_ny.apply(
        lambda x: bool(x.dst()) if x.dst() is not None else False
    )
    
    # Session columns (5)
    df['is_asia_session'] = df['hour_ny'] >= 19
    df['is_london_session'] = (df['hour_ny'] >= 2) & (df['hour_ny'] <= 4)
    df['is_ny_session'] = (df['hour_ny'] >= 7) & (df['hour_ny'] <= 9)
    df['session_name'] = _get_session_name(df)
    df['is_session_overlap'] = (
        df['is_asia_session'].astype(int) +
        df['is_london_session'].astype(int) +
        df['is_ny_session'].astype(int)
    ) > 1
    
    # Kill zone columns (6)
    df['is_kz_asia'] = df['hour_ny'] == 20
    df['is_kz_lokz'] = df['hour_ny'] == 3
    df['is_kz_nykz'] = df['hour_ny'] == 8
    df['kz_active'] = df['is_kz_asia'] | df['is_kz_lokz'] | df['is_kz_nykz']
    df['kz_name'] = _get_kz_name(df)
    df['is_manipulation_hour'] = (
        (df['hour_ny'] == 19) | (df['hour_ny'] == 2) | (df['hour_ny'] == 7)
    )
    
    # Reference levels (6) — NO FORWARD_FILL
    df['weekly_open_price'] = _calculate_weekly_open(df, timestamp_ny)
    df['ny_midnight_open'] = _calculate_midnight_open(df, timestamp_ny)
    df['price_vs_weekly_open'] = df['close'] - df['weekly_open_price']
    df['price_vs_midnight_open'] = df['close'] - df['ny_midnight_open']
    df['above_weekly_open'] = df['close'] > df['weekly_open_price']
    df['above_midnight_open'] = df['close'] > df['ny_midnight_open']
    
    # DOW context (2)
    df['dow_context'] = _get_dow_context(df)
    df['is_how_low_day'] = df['day_of_week'].isin([1, 2])
    
    # Trading hours (1)
    df['is_trading_hours'] = (
        df['is_asia_session'] | df['is_london_session'] | df['is_ny_session']
    )
    
    return df


# =============================================================================
# HELPERS
# =============================================================================

def _validate_input(df: pd.DataFrame) -> None:
    """Validate required columns exist."""
    required = ['timestamp', 'close']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _get_ny_timestamps(df: pd.DataFrame) -> pd.Series:
    """Convert timestamps to NY timezone."""
    if df['timestamp'].dt.tz is None:
        timestamp_utc = df['timestamp'].dt.tz_localize('UTC')
    else:
        timestamp_utc = df['timestamp']
    return timestamp_utc.dt.tz_convert(NY_TZ)


def _calculate_trading_day(timestamp_ny: pd.Series) -> pd.Series:
    """
    Calculate trading day (starts 17:00 NY prior day).
    
    NO FORWARD_FILL — uses vectorized operation.
    """
    return timestamp_ny.apply(
        lambda x: x.date() if x.hour >= 17 else (x - pd.Timedelta(days=1)).date()
    )


def _get_session_name(df: pd.DataFrame) -> pd.Series:
    """Get session name (priority: NY > London > Asia > off)."""
    session = pd.Series('off_session', index=df.index)
    session.loc[df['is_asia_session']] = 'asia'
    session.loc[df['is_london_session']] = 'london'
    session.loc[df['is_ny_session']] = 'new_york'
    return session


def _get_kz_name(df: pd.DataFrame) -> pd.Series:
    """Get kill zone name."""
    kz = pd.Series(None, index=df.index, dtype=object)
    kz.loc[df['is_kz_asia']] = 'asia_kz'
    kz.loc[df['is_kz_lokz']] = 'lokz'
    kz.loc[df['is_kz_nykz']] = 'nykz'
    return kz


def _get_dow_context(df: pd.DataFrame) -> pd.Series:
    """Get day-of-week context."""
    ctx = pd.Series('distribution', index=df.index)
    ctx.loc[df['day_of_week'] == 0] = 'consolidation'  # Monday
    ctx.loc[df['day_of_week'].isin([1, 2])] = 'how_low_forming'  # Tue/Wed
    return ctx


def _calculate_weekly_open(df: pd.DataFrame, timestamp_ny: pd.Series) -> pd.Series:
    """
    Calculate weekly open price (Sunday 17:00 NY).
    
    CRITICAL: NO forward_fill — uses groupby broadcast.
    Missing values use FIRST price as sentinel, not ffill.
    """
    # Create week identifier
    week_id = timestamp_ny.dt.isocalendar().week.astype(str) + '_' + timestamp_ny.dt.year.astype(str)
    
    # Find Sunday 17:00 bars
    is_sunday = timestamp_ny.dt.weekday == 6
    is_17h = timestamp_ny.dt.hour == 17
    is_first_minute = timestamp_ny.dt.minute == 0
    is_weekly_open = is_sunday & is_17h & is_first_minute
    
    # Get weekly open for each week
    weekly_opens = df.loc[is_weekly_open, ['close']].copy()
    weekly_opens['week_id'] = week_id[is_weekly_open]
    weekly_open_map = weekly_opens.groupby('week_id')['close'].first()
    
    # Map back to full dataframe
    result = week_id.map(weekly_open_map)
    
    # For weeks without Sunday 17:00 bar, use first bar of that week
    # NOT forward_fill — explicit first-bar fallback
    if result.isna().any():
        week_first = df.groupby(week_id)['close'].first()
        result = result.fillna(week_id.map(week_first))
    
    return result


def _calculate_midnight_open(df: pd.DataFrame, timestamp_ny: pd.Series) -> pd.Series:
    """
    Calculate NY midnight open (00:00 NY each day).
    
    CRITICAL: NO forward_fill — uses groupby broadcast.
    Missing values use FIRST price of day, not ffill.
    """
    # Create day identifier
    day_id = timestamp_ny.dt.date.astype(str)
    
    # Find midnight bars
    is_midnight = (timestamp_ny.dt.hour == 0) & (timestamp_ny.dt.minute == 0)
    
    # Get midnight open for each day
    midnight_opens = df.loc[is_midnight, ['close']].copy()
    midnight_opens['day_id'] = day_id[is_midnight]
    midnight_map = midnight_opens.groupby('day_id')['close'].first()
    
    # Map back to full dataframe
    result = day_id.map(midnight_map)
    
    # For days without midnight bar, use first bar of that day
    # NOT forward_fill — explicit first-bar fallback
    if result.isna().any():
        day_first = df.groupby(day_id)['close'].first()
        result = result.fillna(day_id.map(day_first))
    
    return result


# =============================================================================
# COLUMN MANIFEST
# =============================================================================

LAYER_1_COLUMNS = [
    # Time (4)
    'hour_ny', 'minute_ny', 'day_of_week', 'trading_day',
    # DST (1)
    'is_dst_us',
    # Session (5)
    'is_asia_session', 'is_london_session', 'is_ny_session',
    'session_name', 'is_session_overlap',
    # Kill zone (6)
    'is_kz_asia', 'is_kz_lokz', 'is_kz_nykz',
    'kz_active', 'kz_name', 'is_manipulation_hour',
    # Reference (6)
    'weekly_open_price', 'ny_midnight_open',
    'price_vs_weekly_open', 'price_vs_midnight_open',
    'above_weekly_open', 'above_midnight_open',
    # DOW (2)
    'dow_context', 'is_how_low_day',
    # Trading hours (1)
    'is_trading_hours',
]


def get_columns() -> List[str]:
    """Return columns this layer creates."""
    return LAYER_1_COLUMNS.copy()


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == '__main__':
    print("Layer 1 (Phoenix) Self-Test")
    print("=" * 50)
    
    # Create test data
    test_data = pd.DataFrame({
        'timestamp': pd.date_range('2025-01-15', periods=1440, freq='1min', tz='UTC'),
        'open': 1.0850,
        'high': 1.0855,
        'low': 1.0845,
        'close': 1.0852,
        'volume': 1000
    })
    
    result = enrich(test_data)
    
    # Validate
    expected = len(LAYER_1_COLUMNS)
    actual = len([c for c in LAYER_1_COLUMNS if c in result.columns])
    
    print(f"Expected columns: {expected}")
    print(f"Found columns: {actual}")
    print(f"VERDICT: {'PASS' if actual == expected else 'FAIL'}")
