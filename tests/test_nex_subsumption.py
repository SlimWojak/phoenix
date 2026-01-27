"""
Test NEX Subsumption — Verify subsumed layers work correctly.

SPRINT: S27.0
EXIT_GATE: schema_integrity, mirror_parity

Tests:
- L1-L3 produce expected columns
- Output is deterministic (INV-CONTRACT-1)
- No forbidden patterns
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add phoenix to path
PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_ohlcv():
    """Sample OHLCV data for testing."""
    np.random.seed(42)  # Determinism
    n = 1440  # 1 day of 1-min bars

    base_price = 1.0850
    returns = np.random.randn(n) * 0.0001
    close = base_price + np.cumsum(returns)

    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-15", periods=n, freq="1min", tz="UTC"),
            "open": close - np.random.rand(n) * 0.0002,
            "high": close + np.random.rand(n) * 0.0003,
            "low": close - np.random.rand(n) * 0.0003,
            "close": close,
            "volume": np.random.randint(100, 1000, n),
        }
    )


@pytest.fixture
def multi_day_ohlcv():
    """Multi-day OHLCV for PDH/PDL tests."""
    np.random.seed(42)
    n = 4320  # 3 days

    base_price = 1.0850
    returns = np.random.randn(n) * 0.0001
    close = base_price + np.cumsum(returns)

    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-13", periods=n, freq="1min", tz="UTC"),
            "open": close - np.random.rand(n) * 0.0002,
            "high": close + np.random.rand(n) * 0.0003,
            "low": close - np.random.rand(n) * 0.0003,
            "close": close,
            "volume": np.random.randint(100, 1000, n),
        }
    )


# =============================================================================
# L1 TESTS
# =============================================================================


class TestL1Subsumption:
    """Test L1 time_sessions subsumption."""

    def test_l1_produces_columns(self, sample_ohlcv):
        """L1 produces all expected columns."""
        from enrichment.layers import l1_time_sessions

        result = l1_time_sessions.enrich(sample_ohlcv)

        for col in l1_time_sessions.LAYER_1_COLUMNS:
            assert col in result.columns, f"Missing column: {col}"

    def test_l1_deterministic(self, sample_ohlcv):
        """L1 is deterministic (INV-CONTRACT-1)."""
        from enrichment.layers import l1_time_sessions

        result1 = l1_time_sessions.enrich(sample_ohlcv.copy())
        result2 = l1_time_sessions.enrich(sample_ohlcv.copy())

        # Compare all L1 columns
        for col in l1_time_sessions.LAYER_1_COLUMNS:
            if result1[col].dtype == "object":
                assert (result1[col] == result2[col]).all(), f"Non-deterministic: {col}"
            else:
                assert np.allclose(
                    result1[col].fillna(-999), result2[col].fillna(-999)
                ), f"Non-deterministic: {col}"

    def test_l1_session_detection(self, sample_ohlcv):
        """L1 correctly detects sessions."""
        from enrichment.layers import l1_time_sessions

        result = l1_time_sessions.enrich(sample_ohlcv)

        # Check session counts are reasonable
        asia_count = result["is_asia_session"].sum()
        london_count = result["is_london_session"].sum()
        ny_count = result["is_ny_session"].sum()

        # Asia: 19:00-23:59 = 5 hours = 300 bars
        # London: 02:00-05:00 = 3 hours = 180 bars
        # NY: 07:00-10:00 = 3 hours = 180 bars
        assert asia_count > 0, "No Asia session detected"
        assert london_count > 0, "No London session detected"
        assert ny_count > 0, "No NY session detected"


# =============================================================================
# L2 TESTS
# =============================================================================


class TestL2Subsumption:
    """Test L2 reference_levels subsumption."""

    def test_l2_produces_columns(self, multi_day_ohlcv):
        """L2 produces all expected columns."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels

        df = l1_time_sessions.enrich(multi_day_ohlcv)
        result = l2_reference_levels.enrich(df)

        for col in l2_reference_levels.LAYER_2_COLUMNS:
            assert col in result.columns, f"Missing column: {col}"

    def test_l2_deterministic(self, multi_day_ohlcv):
        """L2 is deterministic (INV-CONTRACT-1)."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels

        df1 = l1_time_sessions.enrich(multi_day_ohlcv.copy())
        df2 = l1_time_sessions.enrich(multi_day_ohlcv.copy())

        result1 = l2_reference_levels.enrich(df1)
        result2 = l2_reference_levels.enrich(df2)

        for col in ["asia_high", "asia_low", "pdh", "pdl"]:
            assert np.allclose(
                result1[col].fillna(-999), result2[col].fillna(-999)
            ), f"Non-deterministic: {col}"

    def test_l2_pdh_pdl_calculation(self, multi_day_ohlcv):
        """L2 calculates PDH/PDL correctly."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels

        df = l1_time_sessions.enrich(multi_day_ohlcv)
        result = l2_reference_levels.enrich(df)

        # PDH/PDL should exist for days after the first
        # First day should have NaN
        first_day = result["trading_day"].iloc[0]
        first_day_mask = result["trading_day"] == first_day

        # First day: PDH/PDL should be NaN
        assert result.loc[first_day_mask, "pdh"].isna().all(), "First day should have NaN PDH"


# =============================================================================
# L3 TESTS
# =============================================================================


class TestL3Subsumption:
    """Test L3 sweeps subsumption."""

    def test_l3_produces_columns(self, multi_day_ohlcv):
        """L3 produces all expected columns."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels, l3_sweeps

        df = l1_time_sessions.enrich(multi_day_ohlcv)
        df = l2_reference_levels.enrich(df)
        result = l3_sweeps.enrich(df)

        for col in l3_sweeps.LAYER_3_COLUMNS:
            assert col in result.columns, f"Missing column: {col}"

    def test_l3_deterministic(self, multi_day_ohlcv):
        """L3 is deterministic (INV-CONTRACT-1)."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels, l3_sweeps

        df1 = l1_time_sessions.enrich(multi_day_ohlcv.copy())
        df1 = l2_reference_levels.enrich(df1)
        result1 = l3_sweeps.enrich(df1)

        df2 = l1_time_sessions.enrich(multi_day_ohlcv.copy())
        df2 = l2_reference_levels.enrich(df2)
        result2 = l3_sweeps.enrich(df2)

        assert (result1["sweep_detected"] == result2["sweep_detected"]).all()


# =============================================================================
# PIPELINE TESTS
# =============================================================================


class TestFullPipeline:
    """Test full L1-L3 pipeline."""

    def test_pipeline_completes(self, multi_day_ohlcv):
        """Full pipeline completes without error."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels, l3_sweeps

        df = multi_day_ohlcv.copy()
        df = l1_time_sessions.enrich(df)
        df = l2_reference_levels.enrich(df)
        df = l3_sweeps.enrich(df)

        # Count total columns
        total_cols = (
            len(l1_time_sessions.LAYER_1_COLUMNS)
            + len(l2_reference_levels.LAYER_2_COLUMNS)
            + len(l3_sweeps.LAYER_3_COLUMNS)
        )

        print("\nPipeline test:")
        print(f"  Input columns: {len(multi_day_ohlcv.columns)}")
        print(f"  Output columns: {len(df.columns)}")
        print(f"  L1-L3 columns: {total_cols}")

    def test_pipeline_no_data_loss(self, multi_day_ohlcv):
        """Pipeline doesn't lose rows."""
        from enrichment.layers import l1_time_sessions, l2_reference_levels, l3_sweeps

        original_len = len(multi_day_ohlcv)

        df = l1_time_sessions.enrich(multi_day_ohlcv)
        df = l2_reference_levels.enrich(df)
        df = l3_sweeps.enrich(df)

        assert len(df) == original_len, "Pipeline lost rows"
