"""
Test L4 Structure Breaks — Verify swing detection and order flow.

SPRINT: S27.0
EXIT_GATE: schema_integrity
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


@pytest.fixture
def sample_data():
    """Create sample OHLC data with clear structure."""
    np.random.seed(42)
    n = 500

    # Create trending data with swings
    base = 1.0850
    trend = np.linspace(0, 0.005, n)  # Uptrend
    noise = np.cumsum(np.random.randn(n) * 0.0002)

    close = base + trend + noise

    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-15", periods=n, freq="1min", tz="UTC"),
            "open": close - np.random.rand(n) * 0.0002,
            "high": close + np.random.rand(n) * 0.0003,
            "low": close - np.random.rand(n) * 0.0003,
            "close": close,
        }
    )


class TestL4StructureBreaks:
    """Test L4 structure detection."""

    def test_produces_columns(self, sample_data):
        """L4 produces all expected columns."""
        from enrichment.layers import l4_structure_breaks

        result = l4_structure_breaks.enrich(sample_data)

        for col in l4_structure_breaks.LAYER_4_COLUMNS:
            assert col in result.columns, f"Missing: {col}"

    def test_deterministic(self, sample_data):
        """L4 is deterministic (INV-CONTRACT-1)."""
        from enrichment.layers import l4_structure_breaks

        r1 = l4_structure_breaks.enrich(sample_data.copy())
        r2 = l4_structure_breaks.enrich(sample_data.copy())

        for col in ["swing_high", "order_flow", "structure_break_up"]:
            if r1[col].dtype == "object":
                assert (r1[col] == r2[col]).all()
            else:
                assert np.allclose(r1[col].fillna(-999), r2[col].fillna(-999))

    def test_swing_detection(self, sample_data):
        """Swings are detected."""
        from enrichment.layers import l4_structure_breaks

        result = l4_structure_breaks.enrich(sample_data)

        # Should have some swing highs/lows
        has_swings = (~result["swing_high"].isna()).any()
        assert has_swings, "No swings detected"

    def test_order_flow_values(self, sample_data):
        """Order flow has valid values."""
        from enrichment.layers import l4_structure_breaks

        result = l4_structure_breaks.enrich(sample_data)

        valid_values = {"bullish", "bearish", "mixed", "neutral"}
        unique_values = set(result["order_flow"].unique())

        assert unique_values.issubset(valid_values)

    def test_no_forward_fill(self, sample_data):
        """L4 doesn't use forward_fill."""
        import inspect

        from enrichment.layers import l4_structure_breaks

        source = inspect.getsource(l4_structure_breaks)

        assert ".ffill(" not in source
        assert ".forward_fill(" not in source
        assert "method='ffill'" not in source
