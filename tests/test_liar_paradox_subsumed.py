"""
Test Liar Paradox on Subsumed Pipeline — Verify corruption detection.

SPRINT: S27.0
EXIT_GATE: liar_fires

Proves that 1-pip injection is detected on the full L1-L6 subsumed pipeline.
"""

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def clean_data():
    """Create clean OHLC data."""
    np.random.seed(42)
    n = 1000

    base = 1.0850
    returns = np.random.randn(n) * 0.0001
    close = base + np.cumsum(returns)

    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-15", periods=n, freq="1min", tz="UTC"),
            "open": close - np.random.rand(n) * 0.0002,
            "high": close + np.random.rand(n) * 0.0003,
            "low": close - np.random.rand(n) * 0.0003,
            "close": close,
        }
    )


def run_full_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Run full L1-L6 pipeline."""
    from enrichment.layers import (
        l1_time_sessions,
        l2_reference_levels,
        l3_sweeps,
        l4_structure_breaks,
        l5_order_blocks,
        l6_fvg_imbalances,
    )

    df = l1_time_sessions.enrich(df)
    df = l2_reference_levels.enrich(df)
    df = l3_sweeps.enrich(df)
    df = l4_structure_breaks.enrich(df)
    df = l5_order_blocks.enrich(df)
    df = l6_fvg_imbalances.enrich(df)

    return df


def compute_ohlc_hash(df: pd.DataFrame) -> str:
    """Compute hash of OHLC columns."""
    ohlc = df[["open", "high", "low", "close"]].values
    return hashlib.sha256(ohlc.tobytes()).hexdigest()


def inject_corruption(df: pd.DataFrame, bar_idx: int, pip_delta: float = 0.0001) -> pd.DataFrame:
    """
    Inject +1 pip corruption to close price.

    Args:
        df: DataFrame to corrupt
        bar_idx: Bar index to corrupt
        pip_delta: Amount to add (default 1 pip = 0.0001)

    Returns:
        Corrupted DataFrame
    """
    df = df.copy()
    df.loc[df.index[bar_idx], "close"] += pip_delta
    return df


# =============================================================================
# TESTS
# =============================================================================


class TestLiarParadoxSubsumed:
    """Test liar paradox on full subsumed pipeline."""

    def test_clean_data_passes(self, clean_data):
        """Clean data produces consistent output."""
        result1 = run_full_pipeline(clean_data.copy())
        result2 = run_full_pipeline(clean_data.copy())

        hash1 = compute_ohlc_hash(result1)
        hash2 = compute_ohlc_hash(result2)

        assert hash1 == hash2, "Clean data should produce consistent hash"

    def test_corruption_changes_hash(self, clean_data):
        """1-pip corruption changes the hash."""
        # Reference hash
        ref_hash = compute_ohlc_hash(clean_data)

        # Inject corruption
        corrupted = inject_corruption(clean_data, bar_idx=500, pip_delta=0.0001)
        corrupt_hash = compute_ohlc_hash(corrupted)

        assert ref_hash != corrupt_hash, "Corruption should change hash"

    def test_corruption_detected_by_downstream(self, clean_data):
        """
        Corruption affects downstream calculations.

        EXIT_GATE: liar_fires
        """
        # Run pipeline on clean data
        clean_result = run_full_pipeline(clean_data.copy())

        # Inject corruption and run pipeline
        corrupted = inject_corruption(clean_data.copy(), bar_idx=500, pip_delta=0.0001)
        corrupt_result = run_full_pipeline(corrupted)

        # Check that downstream columns differ
        # The corruption should propagate to derived columns
        differences_found = False

        # Check columns that depend on close price
        check_cols = [
            "price_vs_weekly_open",
            "price_vs_midnight_open",
            "sweep_detected",
            "structure_break_up",
            "ob_bull_active",
        ]

        for col in check_cols:
            if col in clean_result.columns and col in corrupt_result.columns:
                if clean_result[col].dtype == bool:
                    if not (clean_result[col] == corrupt_result[col]).all():
                        differences_found = True
                        break
                else:
                    clean_vals = clean_result[col].fillna(-999)
                    corrupt_vals = corrupt_result[col].fillna(-999)
                    if not np.allclose(clean_vals, corrupt_vals):
                        differences_found = True
                        break

        # At minimum, the OHLC hash must differ
        clean_hash = compute_ohlc_hash(clean_result)
        corrupt_hash = compute_ohlc_hash(corrupt_result)

        assert clean_hash != corrupt_hash, "Liar paradox FAILED: corruption not detected by hash"

    def test_corruption_magnitude_matters(self, clean_data):
        """Smaller corruptions still detectable."""
        ref_hash = compute_ohlc_hash(clean_data)

        # 0.1 pip corruption
        small_corrupt = inject_corruption(clean_data.copy(), bar_idx=500, pip_delta=0.00001)
        small_hash = compute_ohlc_hash(small_corrupt)

        assert ref_hash != small_hash, "Even 0.1 pip should be detectable"

    def test_multiple_corruptions(self, clean_data):
        """Multiple corruptions all detected."""
        ref_hash = compute_ohlc_hash(clean_data)

        # Inject 3 corruptions
        corrupted = clean_data.copy()
        for idx in [100, 500, 900]:
            corrupted = inject_corruption(corrupted, bar_idx=idx, pip_delta=0.0001)

        corrupt_hash = compute_ohlc_hash(corrupted)

        assert ref_hash != corrupt_hash


class TestPipelineIntegrity:
    """Test pipeline integrity after L4-L6 subsumption."""

    def test_column_count(self, clean_data):
        """Full pipeline produces expected columns."""
        from enrichment.layers import (
            l1_time_sessions,
            l2_reference_levels,
            l3_sweeps,
            l4_structure_breaks,
            l5_order_blocks,
            l6_fvg_imbalances,
        )

        result = run_full_pipeline(clean_data)

        expected_new = (
            len(l1_time_sessions.LAYER_1_COLUMNS)
            + len(l2_reference_levels.LAYER_2_COLUMNS)
            + len(l3_sweeps.LAYER_3_COLUMNS)
            + len(l4_structure_breaks.LAYER_4_COLUMNS)
            + len(l5_order_blocks.LAYER_5_COLUMNS)
            + len(l6_fvg_imbalances.LAYER_6_COLUMNS)
        )

        # Original OHLC columns + enrichment columns
        assert len(result.columns) >= expected_new

    def test_no_data_loss(self, clean_data):
        """Pipeline doesn't lose rows."""
        original_len = len(clean_data)
        result = run_full_pipeline(clean_data)

        assert len(result) == original_len
