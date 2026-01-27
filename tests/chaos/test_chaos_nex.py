"""
Test Chaos NEX — Attack vectors for NEX subsumption.

SPRINT: S27.0
EXIT_GATE: Track D

Vectors:
- V2-NEX-001: synthetic_leak
- V2-NEX-002: schema_drift
- V2-NEX-003: determinism_break
"""

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PHOENIX_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


# =============================================================================
# V2-NEX-001: SYNTHETIC LEAK
# =============================================================================


class TestSyntheticLeak:
    """
    Vector: NEX forward-fill survives subsumption.

    CRITICAL: Any forward_fill in subsumed code is a failure.
    """

    def test_l1_preserves_nan(self):
        """L1 doesn't fill NaN in close prices."""
        from enrichment.layers import l1_time_sessions

        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-15", periods=100, freq="1min", tz="UTC"),
                "close": [1.0850] * 50 + [np.nan] * 10 + [1.0860] * 40,
                "high": 1.0855,
                "low": 1.0845,
            }
        )

        nan_before = df["close"].isna().sum()
        result = l1_time_sessions.enrich(df)
        nan_after = result["close"].isna().sum()

        assert (
            nan_after == nan_before
        ), f"NaN count changed: {nan_before} → {nan_after} (synthetic leak!)"

    def test_l2_preserves_nan_in_source(self):
        """L2 doesn't fill NaN in OHLC data."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels

        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-15", periods=200, freq="1min", tz="UTC"),
                "open": [1.0850] * 100 + [np.nan] * 10 + [1.0850] * 90,
                "high": [1.0855] * 100 + [np.nan] * 10 + [1.0855] * 90,
                "low": [1.0845] * 100 + [np.nan] * 10 + [1.0845] * 90,
                "close": [1.0850] * 100 + [np.nan] * 10 + [1.0850] * 90,
            }
        )

        nan_before = df["close"].isna().sum()
        df = l1_time_sessions.enrich(df)
        result = l2_reference_levels.enrich(df)
        nan_after = result["close"].isna().sum()

        assert nan_after == nan_before

    def test_pdh_pdl_nan_for_first_day(self):
        """PDH/PDL should be NaN for first day (no previous day)."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels

        # Only 1 day of data
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-15", periods=1440, freq="1min", tz="UTC"),
                "open": 1.0850,
                "high": 1.0855,
                "low": 1.0845,
                "close": 1.0852,
            }
        )

        df = l1_time_sessions.enrich(df)
        result = l2_reference_levels.enrich(df)

        # All rows should have NaN PDH/PDL (no previous day)
        assert result["pdh"].isna().all(), "PDH should be NaN for first day"
        assert result["pdl"].isna().all(), "PDL should be NaN for first day"


# =============================================================================
# V2-NEX-002: SCHEMA DRIFT
# =============================================================================


class TestSchemaDrift:
    """
    Vector: Enrichment produces wrong column count.
    """

    def test_l1_column_count(self):
        """L1 produces exactly 25 columns."""
        from enrichment.layers import l1_time_sessions

        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-15", periods=100, freq="1min", tz="UTC"),
                "close": 1.0850,
                "high": 1.0855,
                "low": 1.0845,
            }
        )

        result = l1_time_sessions.enrich(df)
        actual_new = len([c for c in l1_time_sessions.LAYER_1_COLUMNS if c in result.columns])
        expected = len(l1_time_sessions.LAYER_1_COLUMNS)

        assert actual_new == expected, f"L1 column count: {actual_new}, expected {expected}"

    def test_l2_column_count(self):
        """L2 produces expected columns."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels

        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-13", periods=2880, freq="1min", tz="UTC"),
                "open": 1.0850,
                "high": 1.0855,
                "low": 1.0845,
                "close": 1.0852,
            }
        )

        df = l1_time_sessions.enrich(df)
        result = l2_reference_levels.enrich(df)

        for col in l2_reference_levels.LAYER_2_COLUMNS:
            assert col in result.columns, f"Missing L2 column: {col}"

    def test_l3_column_count(self):
        """L3 produces expected columns."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels, l3_sweeps

        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-13", periods=2880, freq="1min", tz="UTC"),
                "open": 1.0850,
                "high": 1.0855,
                "low": 1.0845,
                "close": 1.0852,
            }
        )

        df = l1_time_sessions.enrich(df)
        df = l2_reference_levels.enrich(df)
        result = l3_sweeps.enrich(df)

        for col in l3_sweeps.LAYER_3_COLUMNS:
            assert col in result.columns, f"Missing L3 column: {col}"


# =============================================================================
# V2-NEX-003: DETERMINISM BREAK
# =============================================================================


class TestDeterminismBreak:
    """
    Vector: Same input produces different output.

    INV-CONTRACT-1: Deterministic (same input → same output)
    """

    def test_l1_deterministic(self):
        """L1 produces identical output for identical input."""
        from enrichment.layers import l1_time_sessions

        np.random.seed(42)
        df1 = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-15", periods=100, freq="1min", tz="UTC"),
                "close": 1.0850 + np.random.randn(100) * 0.001,
                "high": 1.0855,
                "low": 1.0845,
            }
        )

        np.random.seed(42)
        df2 = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-15", periods=100, freq="1min", tz="UTC"),
                "close": 1.0850 + np.random.randn(100) * 0.001,
                "high": 1.0855,
                "low": 1.0845,
            }
        )

        result1 = l1_time_sessions.enrich(df1)
        result2 = l1_time_sessions.enrich(df2)

        # Compare key columns
        for col in ["hour_ny", "is_asia_session", "kz_active"]:
            assert (result1[col] == result2[col]).all(), f"Non-deterministic column: {col}"

    def test_l2_deterministic(self):
        """L2 produces identical output for identical input."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels

        np.random.seed(42)
        base = 1.0850 + np.random.randn(2880) * 0.001

        df1 = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-13", periods=2880, freq="1min", tz="UTC"),
                "open": base - 0.0002,
                "high": base + 0.0003,
                "low": base - 0.0003,
                "close": base,
            }
        )

        np.random.seed(42)
        base = 1.0850 + np.random.randn(2880) * 0.001

        df2 = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-13", periods=2880, freq="1min", tz="UTC"),
                "open": base - 0.0002,
                "high": base + 0.0003,
                "low": base - 0.0003,
                "close": base,
            }
        )

        df1 = l1_time_sessions.enrich(df1)
        df2 = l1_time_sessions.enrich(df2)

        result1 = l2_reference_levels.enrich(df1)
        result2 = l2_reference_levels.enrich(df2)

        # Compare key columns (handle NaN)
        for col in ["asia_high", "asia_low", "pdh", "pdl"]:
            r1_filled = result1[col].fillna(-999)
            r2_filled = result2[col].fillna(-999)
            assert np.allclose(r1_filled, r2_filled), f"Non-deterministic column: {col}"

    def test_hash_reproducibility(self):
        """Output hash is reproducible."""
        from enrichment.layers import l1_time_sessions

        np.random.seed(123)
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-15", periods=100, freq="1min", tz="UTC"),
                "close": 1.0850 + np.random.randn(100) * 0.001,
                "high": 1.0855,
                "low": 1.0845,
            }
        )

        result1 = l1_time_sessions.enrich(df.copy())
        result2 = l1_time_sessions.enrich(df.copy())

        # Hash the hour_ny column (should be identical)
        h1 = hashlib.sha256(result1["hour_ny"].to_numpy().tobytes()).hexdigest()
        h2 = hashlib.sha256(result2["hour_ny"].to_numpy().tobytes()).hexdigest()

        assert h1 == h2, "Hash mismatch — non-deterministic"
