"""
T2 Tests: Asia Range Scalp Primitives — S51 DRIVESHAFT
========================================================

Tests RE_ACCEPTANCE, sweep extension tracking, and FVG Asia validation.
"""

from __future__ import annotations

from enrichment.layers.l7_asia_scalp import (
    enrich,
)

from .conftest import make_asia_scalp_scenario


class TestReAcceptance:
    """RE_ACCEPTANCE: 5m close strictly inside Asia range after sweep."""

    def test_sweep_then_close_inside_valid(self):
        """Sweep then 5m close inside → re_acceptance = True."""
        df = make_asia_scalp_scenario(has_re_acceptance=True)
        result = enrich(df)
        assert result["re_acceptance"].any()

    def test_close_on_boundary_invalid(self):
        """Close ON boundary → not strictly inside → re_acceptance = False."""
        df = make_asia_scalp_scenario()
        asia_high = df["asia_high"].iloc[0]
        sweep_bar = 70
        for idx in range(sweep_bar + 1, sweep_bar + 10):
            df.loc[idx, "close"] = asia_high
        result = enrich(df)
        post_sweep = result.iloc[sweep_bar + 1 : sweep_bar + 10]
        assert not post_sweep["re_acceptance"].any()

    def test_no_close_inside_before_window_end_invalid(self):
        """No close inside range before sweep window ends → no re_acceptance."""
        df = make_asia_scalp_scenario()
        asia_high = df["asia_high"].iloc[0]
        for idx in range(71, len(df)):
            df.loc[idx, "close"] = asia_high + 0.001
        result = enrich(df)
        assert not result.iloc[71:]["re_acceptance"].any()


class TestSweepExtension:
    """Per-direction sweep extension tracking."""

    def test_21_pip_high_sweep_invalidates_high_direction(self):
        """Extension > 20 pips in high direction → that direction dead."""
        df = make_asia_scalp_scenario(sweep_direction="bearish", sweep_extension_pips=21.0)
        asia_high = df["asia_high"].iloc[0]
        df.loc[70, "high"] = asia_high + 21 * 0.0001
        result = enrich(df)
        assert not result.iloc[-1]["asia_high_direction_valid"]
        assert result.iloc[-1]["asia_low_direction_valid"]

    def test_valid_extension_range(self):
        """Extension 1-20 pips → valid."""
        df = make_asia_scalp_scenario(sweep_direction="bullish", sweep_extension_pips=10.0)
        asia_low = df["asia_low"].iloc[0]
        df.loc[70, "low"] = asia_low - 10 * 0.0001
        result = enrich(df)
        assert result["asia_sweep_low_valid"].iloc[-1]

    def test_opposite_direction_still_valid(self):
        """High direction invalid but low direction still valid."""
        df = make_asia_scalp_scenario(sweep_direction="bearish", sweep_extension_pips=25.0)
        asia_high = df["asia_high"].iloc[0]
        df.loc[70, "high"] = asia_high + 25 * 0.0001
        result = enrich(df)
        assert not result.iloc[-1]["asia_high_direction_valid"]
        assert result.iloc[-1]["asia_low_direction_valid"]


class TestFVGAsiaValidation:
    """FVG validation specific to Asia Scalp."""

    def test_fvg_under_1_pip_rejected(self):
        """FVG untouched < 1.0 pip → fvg_asia_*_valid = False."""
        df = make_asia_scalp_scenario(fvg_gap_pips=0.9, candle_c_inside=True)
        result = enrich(df)
        fvg_bar = 75
        assert not result.loc[fvg_bar, "fvg_asia_bull_valid"]

    def test_fvg_1_pip_valid(self):
        """FVG untouched >= 1.0 pip + Candle C inside → valid."""
        df = make_asia_scalp_scenario(fvg_gap_pips=1.5, candle_c_inside=True)
        result = enrich(df)
        fvg_bar = 75
        assert result.loc[fvg_bar, "fvg_asia_bull_valid"]

    def test_candle_c_on_boundary_rejected(self):
        """Candle C close == asia_high → rejected."""
        df = make_asia_scalp_scenario(fvg_gap_pips=2.0, candle_c_inside=False)
        asia_high = df["asia_high"].iloc[0]
        df.loc[75, "close"] = asia_high
        result = enrich(df)
        assert not result.loc[75, "fvg_asia_bull_valid"]


class TestAsiaScalpStateMachine:
    """Composite state machine: WAIT_RANGE → SETUP_VALID."""

    def test_valid_setup_produces_setup_valid(self):
        df = make_asia_scalp_scenario(
            asia_range_pips=20.0,
            sweep_direction="bullish",
            sweep_extension_pips=10.0,
            has_re_acceptance=True,
            has_fvg=True,
            fvg_gap_pips=2.0,
            candle_c_inside=True,
        )
        result = enrich(df)
        assert result["asia_scalp_setup_valid"].any()

    def test_range_too_wide_no_setup(self):
        df = make_asia_scalp_scenario(asia_range_pips=35.0)
        result = enrich(df)
        assert not result["asia_scalp_setup_valid"].any()
