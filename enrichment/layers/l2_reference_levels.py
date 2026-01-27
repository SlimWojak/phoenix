"""
Layer 2: Reference Levels — Phoenix Subsumption.

ORIGIN: NEX nex_lab/data/enrichment/reference_levels.py
SPRINT: S27.0
STATUS: SUBSUMED

Handles price reference levels: Asia range, PDH/PDL, session levels.

COLUMNS: 46 (core) + 28 (stubbed for Phase 3)
DEPENDENCIES: Layer 1 (session columns)

FORBIDDEN:
- forward_fill (use explicit sentinel or groupby broadcast)
- auto_fix
- synthetic fills

INVARIANTS:
- INV-CONTRACT-1: deterministic
- INV-DATA-2: no synthetic without flag
"""


import numpy as np
import pandas as pd

# =============================================================================
# CONSTANTS
# =============================================================================

PIP_MULTIPLIERS = {
    "USDJPY": 100,
    "EURJPY": 100,
    "GBPJPY": 100,
    "AUDJPY": 100,
    "CADJPY": 100,
    "CHFJPY": 100,
    "NZDJPY": 100,
}
DEFAULT_PIP_MULTIPLIER = 10000

# Sentinel for missing values (NOT forward_fill)
MISSING_LEVEL = np.nan


# =============================================================================
# MAIN ENRICHMENT
# =============================================================================


def enrich(df: pd.DataFrame, symbol: str = None) -> pd.DataFrame:
    """
    Add reference level columns.

    INV-CONTRACT-1: Deterministic.
    NO forward_fill — uses groupby broadcast.

    Args:
        df: DataFrame with L1 columns
        symbol: Trading pair (for pip multiplier)

    Returns:
        DataFrame with 74 additional columns
    """
    df = df.copy()

    # Validate L1 dependencies
    _validate_input(df)

    pip_mult = (
        PIP_MULTIPLIERS.get(symbol.upper(), DEFAULT_PIP_MULTIPLIER)
        if symbol
        else DEFAULT_PIP_MULTIPLIER
    )

    # Asia range (9)
    df = _calculate_asia_range(df, pip_mult)

    # PDH/PDL (9)
    df = _calculate_pdh_pdl(df, pip_mult)

    # Weekly levels (11)
    df = _calculate_weekly_levels(df)

    # London session (7)
    df = _calculate_session_levels(df, "london", pip_mult)

    # NY session (7)
    df = _calculate_session_levels(df, "ny", pip_mult)

    # Stubbed columns for Phase 3 (28)
    df = _add_stubbed_columns(df)

    return df


# =============================================================================
# ASIA RANGE
# =============================================================================


def _calculate_asia_range(df: pd.DataFrame, pip_mult: int) -> pd.DataFrame:
    """
    Calculate Asia range (19:00-23:59 NY).

    NO forward_fill — uses groupby per trading_day.
    """
    if "trading_day" not in df.columns:
        raise ValueError("Missing trading_day from L1")

    asia_mask = df["is_asia_session"] == True

    # Groupby trading_day for Asia bars only
    asia_stats = (
        df[asia_mask]
        .groupby("trading_day")
        .agg({"high": "max", "low": "min"})
        .rename(columns={"high": "_asia_high", "low": "_asia_low"})
    )

    # Map back to full dataframe (NO ffill)
    df["asia_high"] = df["trading_day"].map(asia_stats["_asia_high"])
    df["asia_low"] = df["trading_day"].map(asia_stats["_asia_low"])

    # Derived columns
    df["asia_range"] = df["asia_high"] - df["asia_low"]
    df["asia_range_pips"] = df["asia_range"] * pip_mult
    df["asia_range_ce"] = (df["asia_high"] + df["asia_low"]) / 2

    # Position relative to Asia
    df["above_asia_range"] = df["close"] > df["asia_high"]
    df["below_asia_range"] = df["close"] < df["asia_low"]
    df["inside_asia_range"] = ~(df["above_asia_range"] | df["below_asia_range"])
    df["price_vs_asia_ce"] = df["close"] - df["asia_range_ce"]

    return df


# =============================================================================
# PDH/PDL
# =============================================================================


def _calculate_pdh_pdl(df: pd.DataFrame, pip_mult: int) -> pd.DataFrame:
    """
    Calculate Previous Day High/Low.

    NO forward_fill — uses shift on daily aggregation.
    """
    # Daily stats
    daily_stats = (
        df.groupby("trading_day")
        .agg({"high": "max", "low": "min"})
        .rename(columns={"high": "_day_high", "low": "_day_low"})
    )

    # Shift to get PREVIOUS day (NO ffill)
    daily_stats["_pdh"] = daily_stats["_day_high"].shift(1)
    daily_stats["_pdl"] = daily_stats["_day_low"].shift(1)

    # Map back
    df["pdh"] = df["trading_day"].map(daily_stats["_pdh"])
    df["pdl"] = df["trading_day"].map(daily_stats["_pdl"])

    # Derived
    df["pd_range"] = df["pdh"] - df["pdl"]
    df["pd_range_pips"] = df["pd_range"] * pip_mult
    df["pd_ce"] = (df["pdh"] + df["pdl"]) / 2

    # Position
    df["above_pdh"] = df["close"] > df["pdh"]
    df["below_pdl"] = df["close"] < df["pdl"]
    df["between_pd_levels"] = ~(df["above_pdh"] | df["below_pdl"])
    df["price_vs_pd_ce"] = df["close"] - df["pd_ce"]

    return df


# =============================================================================
# WEEKLY LEVELS
# =============================================================================


def _calculate_weekly_levels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate PWH/PWL (Previous Week High/Low).

    NO forward_fill — uses shift on weekly aggregation.
    """
    # Create week identifier from trading_day
    df["_week"] = pd.to_datetime(df["trading_day"]).dt.isocalendar().week
    df["_year"] = pd.to_datetime(df["trading_day"]).dt.year
    df["_week_id"] = df["_year"].astype(str) + "_" + df["_week"].astype(str)

    # Weekly stats
    weekly_stats = (
        df.groupby("_week_id")
        .agg({"high": "max", "low": "min"})
        .rename(columns={"high": "_week_high", "low": "_week_low"})
    )

    # Sort by week_id to ensure proper shift
    weekly_stats = weekly_stats.sort_index()

    # Shift to get PREVIOUS week
    weekly_stats["_pwh"] = weekly_stats["_week_high"].shift(1)
    weekly_stats["_pwl"] = weekly_stats["_week_low"].shift(1)

    # Map back
    df["pwh"] = df["_week_id"].map(weekly_stats["_pwh"])
    df["pwl"] = df["_week_id"].map(weekly_stats["_pwl"])

    # Derived
    df["pw_range"] = df["pwh"] - df["pwl"]
    df["pw_ce"] = (df["pwh"] + df["pwl"]) / 2

    # Position
    df["above_pwh"] = df["close"] > df["pwh"]
    df["below_pwl"] = df["close"] < df["pwl"]
    df["between_pw_levels"] = ~(df["above_pwh"] | df["below_pwl"])
    df["price_vs_pw_ce"] = df["close"] - df["pw_ce"]

    # is_weekly_open (from L1, verify exists)
    if "weekly_open_price" not in df.columns:
        df["weekly_open_price"] = MISSING_LEVEL

    # Cleanup temp columns
    df = df.drop(columns=["_week", "_year", "_week_id"], errors="ignore")

    return df


# =============================================================================
# SESSION LEVELS
# =============================================================================


def _calculate_session_levels(df: pd.DataFrame, session: str, pip_mult: int) -> pd.DataFrame:
    """
    Calculate session high/low (London or NY).

    NO forward_fill — uses groupby per trading_day.
    """
    session_col = f"is_{session}_session"
    if session_col not in df.columns:
        raise ValueError(f"Missing {session_col} from L1")

    session_mask = df[session_col] == True
    prefix = session[:3]  # 'lon' or 'ny_'

    # Groupby
    session_stats = df[session_mask].groupby("trading_day").agg({"high": "max", "low": "min"})

    # Map back
    df[f"{prefix}_session_high"] = df["trading_day"].map(session_stats["high"])
    df[f"{prefix}_session_low"] = df["trading_day"].map(session_stats["low"])

    # Derived
    df[f"{prefix}_session_range"] = df[f"{prefix}_session_high"] - df[f"{prefix}_session_low"]
    df[f"{prefix}_session_range_pips"] = df[f"{prefix}_session_range"] * pip_mult

    # Position
    df[f"above_{session}_high"] = df["close"] > df[f"{prefix}_session_high"]
    df[f"below_{session}_low"] = df["close"] < df[f"{prefix}_session_low"]
    df[f"inside_{session}_range"] = ~(df[f"above_{session}_high"] | df[f"below_{session}_low"])

    return df


# =============================================================================
# STUBBED COLUMNS (Phase 3)
# =============================================================================


def _add_stubbed_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add stubbed columns for Phase 3 (FVG, OB, IFVG, BPR)."""
    # PD FVGs (10)
    df["pd_fvg_bull_high"] = MISSING_LEVEL
    df["pd_fvg_bull_low"] = MISSING_LEVEL
    df["pd_fvg_bull_ce"] = MISSING_LEVEL
    df["in_pd_fvg_bull"] = False
    df["pd_fvg_bear_high"] = MISSING_LEVEL
    df["pd_fvg_bear_low"] = MISSING_LEVEL
    df["pd_fvg_bear_ce"] = MISSING_LEVEL
    df["in_pd_fvg_bear"] = False
    df["pd_fvg_count_bull"] = 0
    df["pd_fvg_count_bear"] = 0

    # PD Order Blocks (6)
    df["pd_ob_bull_high"] = MISSING_LEVEL
    df["pd_ob_bull_low"] = MISSING_LEVEL
    df["in_pd_ob_bull"] = False
    df["pd_ob_bear_high"] = MISSING_LEVEL
    df["pd_ob_bear_low"] = MISSING_LEVEL
    df["in_pd_ob_bear"] = False

    # IFVG (6)
    df["ifvg_bull_high"] = MISSING_LEVEL
    df["ifvg_bull_low"] = MISSING_LEVEL
    df["in_ifvg_bull"] = False
    df["ifvg_bear_high"] = MISSING_LEVEL
    df["ifvg_bear_low"] = MISSING_LEVEL
    df["in_ifvg_bear"] = False

    # BPR (6)
    df["bpr_high"] = MISSING_LEVEL
    df["bpr_low"] = MISSING_LEVEL
    df["bpr_mid"] = MISSING_LEVEL
    df["in_bpr"] = False
    df["bpr_type"] = None
    df["bpr_strength"] = MISSING_LEVEL

    return df


# =============================================================================
# VALIDATION
# =============================================================================


def _validate_input(df: pd.DataFrame) -> None:
    """Validate L1 columns exist."""
    required = [
        "is_asia_session",
        "is_london_session",
        "is_ny_session",
        "trading_day",
        "close",
        "high",
        "low",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing L1 columns: {missing}")


# =============================================================================
# COLUMN MANIFEST
# =============================================================================

LAYER_2_COLUMNS = [
    # Asia (9)
    "asia_high",
    "asia_low",
    "asia_range",
    "asia_range_pips",
    "asia_range_ce",
    "above_asia_range",
    "below_asia_range",
    "inside_asia_range",
    "price_vs_asia_ce",
    # PDH/PDL (9)
    "pdh",
    "pdl",
    "pd_range",
    "pd_range_pips",
    "pd_ce",
    "above_pdh",
    "below_pdl",
    "between_pd_levels",
    "price_vs_pd_ce",
    # Weekly (11)
    "pwh",
    "pwl",
    "pw_range",
    "pw_ce",
    "above_pwh",
    "below_pwl",
    "between_pw_levels",
    "price_vs_pw_ce",
    # London (7)
    "lon_session_high",
    "lon_session_low",
    "lon_session_range",
    "lon_session_range_pips",
    "above_london_high",
    "below_london_low",
    "inside_london_range",
    # NY (7)
    "ny__session_high",
    "ny__session_low",
    "ny__session_range",
    "ny__session_range_pips",
    "above_ny_high",
    "below_ny_low",
    "inside_ny_range",
    # Stubbed (28)
    "pd_fvg_bull_high",
    "pd_fvg_bull_low",
    "pd_fvg_bull_ce",
    "in_pd_fvg_bull",
    "pd_fvg_bear_high",
    "pd_fvg_bear_low",
    "pd_fvg_bear_ce",
    "in_pd_fvg_bear",
    "pd_fvg_count_bull",
    "pd_fvg_count_bear",
    "pd_ob_bull_high",
    "pd_ob_bull_low",
    "in_pd_ob_bull",
    "pd_ob_bear_high",
    "pd_ob_bear_low",
    "in_pd_ob_bear",
    "ifvg_bull_high",
    "ifvg_bull_low",
    "in_ifvg_bull",
    "ifvg_bear_high",
    "ifvg_bear_low",
    "in_ifvg_bear",
    "bpr_high",
    "bpr_low",
    "bpr_mid",
    "in_bpr",
    "bpr_type",
    "bpr_strength",
]


def get_columns() -> list[str]:
    """Return columns this layer creates."""
    return LAYER_2_COLUMNS.copy()
