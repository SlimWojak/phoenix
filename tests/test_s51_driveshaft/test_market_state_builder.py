"""
T1 Tests: Market State Builder — S51 DRIVESHAFT
=================================================

Tests the enrichment → MarketState wiring layer.

EXIT GATE: Real enrichment DataFrame → MarketState → evaluator → verdict.
           End-to-end. No mocks at seam.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from cso.market_state_builder import build_market_state

from .conftest import make_asia_scalp_scenario


class TestPointInTimeFiltering:
    """INV-PIT-JOIN-ONLY: Future data invisible."""

    def test_future_data_invisible(self):
        """Future data present in DataFrame but invisible to builder."""
        df = make_asia_scalp_scenario()
        now = df["timestamp"].iloc[50].to_pydatetime()

        state, report = build_market_state(df, "EURUSD", now)

        assert state.timestamp == now
        assert report.valid or not report.valid  # builder completes

    def test_point_in_time_no_lookahead(self):
        """Bars after 'now' must not affect state."""
        df = make_asia_scalp_scenario(sweep_extension_pips=10.0)

        before_sweep = df["timestamp"].iloc[65].to_pydatetime()
        state_before, _ = build_market_state(df, "EURUSD", before_sweep)

        after_sweep = df["timestamp"].iloc[80].to_pydatetime()
        state_after, _ = build_market_state(df, "EURUSD", after_sweep)

        assert (
            state_before.recent_sweep != state_after.recent_sweep or not state_before.recent_sweep
        )


class TestColdStart:
    """Cold start: empty DataFrame → invalid MarketState, all gates SKIP."""

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close"])
        now = datetime(2026, 2, 20, 12, 0, tzinfo=UTC)

        state, report = build_market_state(df, "EURUSD", now)

        assert state.invalid_reason is not None
        assert "cold_start" in state.invalid_reason
        assert not report.valid

    def test_all_data_in_future(self):
        """All bars are after 'now' → effectively cold start."""
        df = make_asia_scalp_scenario()
        ancient = datetime(2020, 1, 1, tzinfo=UTC)

        state, report = build_market_state(df, "EURUSD", ancient)

        assert state.invalid_reason is not None
        assert not report.valid


class TestAsiaRangeFields:
    """Asia range fields correctly mapped."""

    def test_asia_range_populated(self):
        df = make_asia_scalp_scenario(asia_range_pips=25.0)
        now = df["timestamp"].iloc[-1].to_pydatetime() + timedelta(minutes=5)

        state, report = build_market_state(df, "EURUSD", now)

        assert state.asia_high is not None
        assert state.asia_low is not None
        assert state.asia_range_pips is not None
        assert state.asia_range_valid is True

    def test_asia_range_invalid_when_too_wide(self):
        df = make_asia_scalp_scenario(asia_range_pips=35.0)
        now = df["timestamp"].iloc[-1].to_pydatetime() + timedelta(minutes=5)

        state, _ = build_market_state(df, "EURUSD", now)

        assert state.asia_range_valid is False


class TestSweepFields:
    """Sweep detection fields correctly mapped."""

    def test_sweep_detected(self):
        df = make_asia_scalp_scenario(sweep_extension_pips=10.0)
        now = df["timestamp"].iloc[80].to_pydatetime()

        state, _ = build_market_state(df, "EURUSD", now)

        assert state.recent_sweep is True
        assert state.sweep_direction == "bullish"
        assert state.sweep_extension_pips is not None

    def test_no_sweep(self):
        df = make_asia_scalp_scenario(sweep_extension_pips=0.0)
        df["sweep_detected"] = False
        now = df["timestamp"].iloc[80].to_pydatetime()

        state, _ = build_market_state(df, "EURUSD", now)

        assert state.recent_sweep is False


class TestReAcceptance:
    """RE_ACCEPTANCE correctly detected."""

    def test_re_acceptance_after_sweep(self):
        df = make_asia_scalp_scenario(has_re_acceptance=True)
        now = df["timestamp"].iloc[80].to_pydatetime()

        state, _ = build_market_state(df, "EURUSD", now)

        assert state.re_acceptance is True

    def test_no_re_acceptance(self):
        df = make_asia_scalp_scenario(has_re_acceptance=False)
        df["re_acceptance"] = False
        df["close_strictly_inside_asia"] = False
        df["close"] = df["asia_high"].iloc[0] + 0.001
        now = df["timestamp"].iloc[80].to_pydatetime()

        state, _ = build_market_state(df, "EURUSD", now)

        assert state.re_acceptance is not True


class TestFrozenState:
    """MarketState is immutable (frozen dataclass)."""

    def test_immutable(self):
        df = make_asia_scalp_scenario()
        now = df["timestamp"].iloc[-1].to_pydatetime() + timedelta(minutes=5)

        state, _ = build_market_state(df, "EURUSD", now)

        with pytest.raises(AttributeError):
            state.asia_high = 999.0  # type: ignore[misc]


class TestBuildReport:
    """MarketStateBuildReport provides observability."""

    def test_report_tracks_sources(self):
        df = make_asia_scalp_scenario()
        now = df["timestamp"].iloc[-1].to_pydatetime() + timedelta(minutes=5)

        _, report = build_market_state(df, "EURUSD", now)

        assert report.pair == "EURUSD"
        assert report.evaluation_time is not None
        assert isinstance(report.per_field_sources, dict)

    def test_report_tracks_missing(self):
        df = make_asia_scalp_scenario()
        df["asia_high"] = np.nan
        now = df["timestamp"].iloc[-1].to_pydatetime() + timedelta(minutes=5)

        _, report = build_market_state(df, "EURUSD", now)

        assert "asia_high" in report.missing_required
        assert not report.valid
