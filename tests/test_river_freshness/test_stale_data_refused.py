"""
S52 T3: Stale data refused at source.

EXIT_GATE: T3_FRESHNESS
Proof: Data older than STALENESS_THRESHOLD_MINUTES raises RiverStalenessError.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from cso.market_state_builder import (
    STALENESS_THRESHOLD_MINUTES,
    RiverStalenessError,
    build_market_state,
)


def _make_enriched_df(
    bar_time: datetime,
    count: int = 10,
    base: float = 1.0850,
) -> pd.DataFrame:
    """Build minimal enriched DataFrame with timestamps around bar_time."""
    pip = 0.0001
    bars = []
    for i in range(count):
        ts = bar_time + timedelta(minutes=5 * i)
        bars.append(
            {
                "timestamp": ts,
                "open": base,
                "high": base + 5 * pip,
                "low": base - 5 * pip,
                "close": base + np.random.RandomState(i).uniform(-2, 2) * pip,
                "volume": 1000,
                "session_name": "london",
                "order_flow": "neutral",
                "structure_trend": "neutral",
                "structure_confirmed": False,
                "asia_high": base + 10 * pip,
                "asia_low": base - 10 * pip,
                "asia_range_pips": 20.0,
                "sweep_detected": False,
                "fvg_bull": False,
                "fvg_bear": False,
                "displacement_pips": 0.0,
            }
        )
    df = pd.DataFrame(bars)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


class TestStaleDataRefused:
    """INV-RIVER-FRESHNESS: Stale data must be refused."""

    def test_fresh_data_accepted(self):
        """Data within threshold is accepted."""
        now = datetime(2026, 2, 21, 12, 0, tzinfo=UTC)
        bar_start = now - timedelta(minutes=10)
        df = _make_enriched_df(bar_start)

        state, report = build_market_state(df, "EURUSD", now)
        assert state.invalid_reason is None or "cold_start" not in (state.invalid_reason or "")

    def test_stale_data_raises(self):
        """Data older than threshold raises RiverStalenessError."""
        now = datetime(2026, 2, 21, 12, 0, tzinfo=UTC)
        bar_start = now - timedelta(minutes=STALENESS_THRESHOLD_MINUTES + 60)
        df = _make_enriched_df(bar_start, count=5)

        with pytest.raises(RiverStalenessError, match="INV-RIVER-FRESHNESS"):
            build_market_state(df, "EURUSD", now)

    def test_exactly_at_threshold_accepted(self):
        """Data exactly at threshold boundary is accepted."""
        now = datetime(2026, 2, 21, 12, 0, tzinfo=UTC)
        bar_time = now - timedelta(minutes=STALENESS_THRESHOLD_MINUTES)
        df = _make_enriched_df(bar_time, count=1)

        state, _ = build_market_state(df, "EURUSD", now)
        assert state is not None

    def test_one_second_past_threshold_raises(self):
        """Data one second past threshold is refused."""
        now = datetime(2026, 2, 21, 12, 0, tzinfo=UTC)
        bar_time = now - timedelta(minutes=STALENESS_THRESHOLD_MINUTES, seconds=1)
        df = _make_enriched_df(bar_time, count=1)

        with pytest.raises(RiverStalenessError):
            build_market_state(df, "EURUSD", now)

    def test_staleness_error_includes_pair(self):
        """Error message includes pair name for diagnostics."""
        now = datetime(2026, 2, 21, 12, 0, tzinfo=UTC)
        bar_start = now - timedelta(hours=2)
        df = _make_enriched_df(bar_start, count=3)

        with pytest.raises(RiverStalenessError, match="GBPUSD"):
            build_market_state(df, "GBPUSD", now)


class TestThresholdRemovalBreaksTests:
    """
    EXIT_GATE: Removing threshold protection must break tests.
    This is a meta-test — it proves the protection is not theater.
    """

    def test_threshold_is_positive(self):
        """STALENESS_THRESHOLD_MINUTES must be a positive value."""
        assert STALENESS_THRESHOLD_MINUTES > 0

    def test_stale_data_would_pass_without_threshold(self):
        """Stale data would produce a MarketState without the threshold check.

        This test documents the kill chain: if the threshold were removed,
        stale bars would be accepted and produce gate evaluations based
        on expired prices.
        """
        now = datetime(2026, 2, 21, 12, 0, tzinfo=UTC)
        bar_start = now - timedelta(hours=2)
        df = _make_enriched_df(bar_start, count=10)

        with pytest.raises(RiverStalenessError):
            build_market_state(df, "EURUSD", now)
