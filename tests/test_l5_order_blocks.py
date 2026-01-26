"""
Test L5 Order Blocks — Verify OB detection and mitigation.

SPRINT: S27.0
EXIT_GATE: schema_integrity
"""

import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np

PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


@pytest.fixture
def sample_data_with_displacement():
    """Create data with displacement candles (for OB detection)."""
    np.random.seed(42)
    n = 500
    
    base = 1.0850
    close = np.full(n, base)
    
    # Add some displacement moves
    for i in [100, 200, 300, 400]:
        close[i:] += 0.003 if i % 200 == 0 else -0.003
    
    # Add noise
    close = close + np.cumsum(np.random.randn(n) * 0.0001)
    
    return pd.DataFrame({
        'timestamp': pd.date_range('2025-01-15', periods=n, freq='1min', tz='UTC'),
        'open': close - np.random.rand(n) * 0.0002,
        'high': close + np.random.rand(n) * 0.0003,
        'low': close - np.random.rand(n) * 0.0003,
        'close': close,
    })


class TestL5OrderBlocks:
    """Test L5 order block detection."""
    
    def test_produces_columns(self, sample_data_with_displacement):
        """L5 produces all expected columns."""
        from enrichment.layers import l5_order_blocks
        
        result = l5_order_blocks.enrich(sample_data_with_displacement)
        
        for col in l5_order_blocks.LAYER_5_COLUMNS:
            assert col in result.columns, f"Missing: {col}"
    
    def test_deterministic(self, sample_data_with_displacement):
        """L5 is deterministic (INV-CONTRACT-1)."""
        from enrichment.layers import l5_order_blocks
        
        r1 = l5_order_blocks.enrich(sample_data_with_displacement.copy())
        r2 = l5_order_blocks.enrich(sample_data_with_displacement.copy())
        
        for col in ['ob_bull_active', 'ob_bear_active']:
            assert (r1[col] == r2[col]).all()
    
    def test_ob_levels_valid(self, sample_data_with_displacement):
        """OB levels are valid when active."""
        from enrichment.layers import l5_order_blocks
        
        result = l5_order_blocks.enrich(sample_data_with_displacement)
        
        # Where OB is active, levels should not be NaN
        bull_active = result['ob_bull_active']
        if bull_active.any():
            assert not result.loc[bull_active, 'ob_bull_high'].isna().all()
    
    def test_ce_is_midpoint(self, sample_data_with_displacement):
        """CE is midpoint of OB zone."""
        from enrichment.layers import l5_order_blocks
        
        result = l5_order_blocks.enrich(sample_data_with_displacement)
        
        # For active OBs, CE should be (high + low) / 2
        active = result['ob_bull_active']
        if active.any():
            expected_ce = (result.loc[active, 'ob_bull_high'] + 
                          result.loc[active, 'ob_bull_low']) / 2
            actual_ce = result.loc[active, 'ob_bull_ce']
            assert np.allclose(expected_ce.dropna(), actual_ce.dropna())
    
    def test_no_forward_fill_in_code(self, sample_data_with_displacement):
        """L5 doesn't use forward_fill method calls."""
        from enrichment.layers import l5_order_blocks
        import inspect
        
        source = inspect.getsource(l5_order_blocks.enrich)
        
        # The actual code shouldn't have ffill calls
        assert '.ffill(' not in source
        assert "method='ffill'" not in source
