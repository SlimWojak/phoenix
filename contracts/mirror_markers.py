"""
Mirror Marker Columns — Boolean markers for cross-vendor XOR comparison.

Source: ICT_DATA_CONTRACT.md v1.0.0
Schema Hash: b848ffe506fd3fff

These are the 110 boolean columns that should match exactly between
Dukascopy and IBKR data after passing through the same enrichment pipeline.

EXCLUDED from mirror comparison:
- volume (vendors non-comparable)
- dxy_* columns (different source/timing)
- smt_* columns (depends on DXY)
"""

MIRROR_MARKER_COLUMNS = [
    # Layer 0: HTF Analysis
    "dealing_range_premium",
    "dealing_range_discount",
    "ipda_20d_premium",
    "ipda_20d_discount",
    "ipda_20d_consolidating",
    "ipda_40d_premium",
    
    # Layer 0.5: HTF Bias
    "in_ote_bull",
    "in_ote_bear",
    "in_htf_pda",
    "counter_trend_allowed",
    
    # Layer 1: Time Sessions
    "is_dst_us",
    "is_asia_session",
    "is_london_session",
    "is_ny_session",
    "is_session_overlap",
    "is_kz_asia",
    "is_kz_lokz",
    "is_kz_nykz",
    "kz_active",
    "is_manipulation_hour",
    "is_how_low_day",
    "is_trading_hours",
    
    # Layer 2: Reference Levels
    "above_weekly_open",
    "above_midnight_open",
    "above_asia_range",
    "below_asia_range",
    "inside_asia_range",
    "above_pdh",
    "below_pdl",
    "between_pd_levels",
    "in_pd_fvg_bull",
    "in_pd_fvg_bear",
    "in_pd_ob_bull",
    "in_pd_ob_bear",
    "in_ifvg_bull",
    "in_ifvg_bear",
    "in_bpr",
    "above_pwh",
    "below_pwl",
    "above_london_high",
    "below_london_low",
    "above_ny_high",
    "below_ny_low",
    
    # Layer 3: Sweeps
    "sweep_detected",
    "sweep_is_valid",
    "sweep_during_kz",
    "sweep_during_session",
    "sweep_into_pda",
    "sweep_mss_confirmed",
    "sweep_displacement_confirmed",
    "sweep_fvg_created",
    "sweep_is_setup",
    
    # Layer 5: FVG (all timeframes)
    "in_5m_fvg_up",
    "in_5m_fvg_down",
    "5m_fvg_up_created",
    "5m_fvg_down_created",
    "in_15m_fvg_up",
    "in_15m_fvg_down",
    "15m_fvg_up_created",
    "15m_fvg_down_created",
    "in_1h_fvg_up",
    "in_1h_fvg_down",
    "1h_fvg_up_created",
    "1h_fvg_down_created",
    "in_4h_fvg_up",
    "in_4h_fvg_down",
    "4h_fvg_up_created",
    "4h_fvg_down_created",
    "in_daily_fvg_up",
    "in_daily_fvg_down",
    "daily_fvg_up_created",
    "daily_fvg_down_created",
    "in_weekly_fvg_up",
    "in_weekly_fvg_down",
    "weekly_fvg_up_created",
    "weekly_fvg_down_created",
    "in_monthly_fvg_up",
    "in_monthly_fvg_down",
    "monthly_fvg_up_created",
    "monthly_fvg_down_created",
    "entry_fvg_present",
    "htf_fvg_present",
    
    # Layer 6: Displacement
    "displacement_up",
    "displacement_down",
    "is_displacement",
    
    # Layer 7: Structure
    "is_higher_high",
    "is_lower_high",
    "is_higher_low",
    "is_lower_low",
    "structure_break_up",
    "structure_break_down",
    
    # Layer 7B: DXY/SMT - EXCLUDED from XOR due to vendor variance
    # "smt_bullish",
    # "smt_bearish",
    
    # Layer 8: Premium/Discount
    "in_premium",
    "in_discount",
    "in_ote",
    
    # Layer 9: Order Blocks
    "in_15m_ob_bull",
    "in_15m_ob_bear",
    "in_1h_ob_bull",
    "in_1h_ob_bear",
    "in_ob_bull",
    "in_ob_bear",
    
    # Layer 11: Alignment
    "htf_unanimous",
    "entry_direction_unanimous",
    "conflicting_signals",
    "htf_supports_long",
    "htf_supports_short",
    "entry_matches_htf_long",
    "entry_matches_htf_short",
    
    # Layer 12: MMM
    "mmm_htf_aligned",
]

# Columns excluded from mirror comparison due to known vendor variance
EXCLUDED_FROM_MIRROR = [
    "volume",  # Vendors non-comparable
    "smt_bullish",  # Depends on DXY
    "smt_bearish",  # Depends on DXY
]

# All columns starting with these prefixes are excluded
EXCLUDED_PREFIXES = [
    "dxy_",  # DXY data may have different source
]


def get_mirror_columns():
    """Return list of columns for Mirror XOR test."""
    return MIRROR_MARKER_COLUMNS.copy()


def is_mirror_column(col_name: str) -> bool:
    """Check if a column should be included in Mirror XOR."""
    if col_name in EXCLUDED_FROM_MIRROR:
        return False
    for prefix in EXCLUDED_PREFIXES:
        if col_name.startswith(prefix):
            return False
    return col_name in MIRROR_MARKER_COLUMNS
