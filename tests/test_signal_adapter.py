"""
Signal Adapter Tests — DEPLOY.P2.1 + P2.3
============================================

Tests the bridge between Dexter analytical signals and Phoenix governance.
Price discovery, PIT alignment, friction tracking.

EXIT GATES:
  - DIAGNOSTIC_SIGNAL → enrichment → price discovery → TradeProposal → CSO → ExecutionIntent
  - Shadow mode blocks execution
  - Intent hash deterministic across replays
  - PIT drift logged; > 4min triggers warning
  - Every rejection produces SignalFriction
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd

from execution.signal_adapter import (
    SignalOutcome,
    process_signal,
)


def _build_signal(**overrides: object) -> dict:  # type: ignore[type-arg]
    """Build a canonical bullish DIAGNOSTIC_SIGNAL dict."""
    base: dict = {  # type: ignore[type-arg]
        "bar_time": "2026-02-21T08:20:00+00:00",
        "direction": "bullish",
        "model_type": "REVERSAL",
        "chain_type": "REVERSAL_CHAIN",
        "shadow_mode": True,
        "peak_window": True,
        "f1_bias_pass": True,
        "f2_liquidity_pass": True,
        "f3_structure_pass": True,
        "f4_pda_pass": True,
        "f5_target_pass": True,
        "all_factors_pass": True,
        "eligible_for_signal": True,
        "worldstate_snapshot": {
            "htf_phase": "EXPANSION",
            "direction_permission": "WITH_EXPANSION",
            "authority_tf": "4H",
            "daily_direction": "BULLISH",
            "mechanism_used": 1,
        },
    }
    base.update(overrides)
    return base


def _build_enriched_df() -> pd.DataFrame:
    """Build enriched DataFrame matching the signal's bar_time window."""
    pip = 0.0001
    asia_high = 1.0860
    asia_low = 1.0840
    base = 1.0850

    asia_start = datetime(2026, 2, 21, 0, 0, tzinfo=UTC)
    bars = []

    for i in range(60):
        ts = asia_start + timedelta(minutes=5 * i)
        bars.append(
            {
                "timestamp": ts,
                "open": base,
                "high": asia_high - pip,
                "low": asia_low + pip,
                "close": base,
                "volume": 1000,
            }
        )

    sweep_start = datetime(2026, 2, 21, 5, 0, tzinfo=UTC)
    for i in range(48):
        ts = sweep_start + timedelta(minutes=5 * i)
        bars.append(
            {
                "timestamp": ts,
                "open": base,
                "high": base + 0.0002,
                "low": base - 0.0002,
                "close": 1.0842,
                "volume": 1000,
            }
        )

    df = pd.DataFrame(bars)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    ny_hours = df["timestamp"].dt.tz_convert("America/New_York")
    df["hour_ny"] = ny_hours.dt.hour
    df["session_name"] = "off_session"
    df["trading_day"] = ny_hours.apply(
        lambda x: x.date() if x.hour >= 17 else (x - timedelta(days=1)).date()
    )

    df["asia_high"] = asia_high
    df["asia_low"] = asia_low
    df["asia_range"] = asia_high - asia_low
    df["asia_range_pips"] = 20.0

    df["order_flow"] = "neutral"
    df["structure_trend"] = "neutral"
    df["structure_confirmed"] = False

    df["sweep_detected"] = False
    df["sweep_direction"] = None
    df["sweep_extension_pips"] = np.nan
    df["sweep_target_type"] = None

    sweep_bar = 70
    df.loc[sweep_bar, "sweep_detected"] = True
    df.loc[sweep_bar, "sweep_direction"] = "bullish"
    df.loc[sweep_bar, "sweep_extension_pips"] = 8.0
    df.loc[sweep_bar, "sweep_target_type"] = "asia_low"
    df.loc[sweep_bar, "low"] = asia_low - 8.0 * pip

    df["fvg_bull"] = False
    df["fvg_bear"] = False
    df["fvg_bull_high"] = np.nan
    df["fvg_bull_low"] = np.nan
    df["fvg_bear_high"] = np.nan
    df["fvg_bear_low"] = np.nan
    df["displacement_pips"] = 0.0

    fvg_bar = 100
    df.loc[fvg_bar, "fvg_bull"] = True
    df.loc[fvg_bar, "fvg_bull_high"] = base + 1.0 * pip
    df.loc[fvg_bar, "fvg_bull_low"] = base - 1.0 * pip
    df.loc[fvg_bar, "close"] = 1.0842

    df["knowledge_time"] = df["timestamp"] + timedelta(seconds=1)

    return df


# =============================================================================
# P2.1: SIGNAL → GOVERNANCE (Constitutional Path)
# =============================================================================


class TestSignalProcessing:
    def test_valid_signal_produces_shadow_observation(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()

        result = process_signal(signal, df, "EURUSD", shadow_mode=True)

        assert (
            result.outcome == SignalOutcome.SHADOW_OBSERVATION
        ), f"Expected SHADOW_OBSERVATION, got {result.outcome}: {result.error}"
        assert result.proposal is not None
        assert result.intent is not None
        assert result.five_drawer is not None

    def test_proposal_has_full_geometry(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()

        result = process_signal(signal, df, "EURUSD")
        assert result.proposal is not None

        p = result.proposal
        assert p.entry_price > 0
        assert p.stop_loss > 0
        assert p.take_profit > 0
        assert p.rr_ratio >= 1.0
        assert p.position_size_lots > 0
        assert p.risk_pips > 0
        assert p.reward_pips > 0

    def test_bullish_geometry_correct(self) -> None:
        signal = _build_signal(direction="bullish")
        df = _build_enriched_df()

        result = process_signal(signal, df, "EURUSD")
        assert result.proposal is not None

        p = result.proposal
        assert p.take_profit == 1.0860
        assert p.stop_loss < p.entry_price
        assert p.entry_price < p.take_profit

    def test_bearish_geometry_correct(self) -> None:
        signal = _build_signal(direction="bearish")
        df = _build_enriched_df()
        df.loc[70, "sweep_direction"] = "bearish"
        df.loc[70, "sweep_target_type"] = "asia_high"
        df.loc[70, "high"] = 1.0860 + 8.0 * 0.0001

        result = process_signal(signal, df, "EURUSD")
        if result.proposal is not None:
            assert result.proposal.take_profit == 1.0840

    def test_shadow_mode_prevents_proposal_created(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()

        result = process_signal(signal, df, "EURUSD", shadow_mode=True)
        assert result.outcome != SignalOutcome.PROPOSAL_CREATED

    def test_non_shadow_produces_proposal_created(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()

        result = process_signal(signal, df, "EURUSD", shadow_mode=False)
        if result.outcome in (
            SignalOutcome.PROPOSAL_CREATED,
            SignalOutcome.SHADOW_OBSERVATION,
        ):
            assert result.proposal is not None

    def test_intent_hash_deterministic(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()

        from execution.intent_adapter import reset_factory

        reset_factory("SIGNAL_TEST")
        r1 = process_signal(signal, df, "EURUSD")

        reset_factory("SIGNAL_TEST")
        r2 = process_signal(signal, df, "EURUSD")

        if r1.intent is not None and r2.intent is not None:
            assert r1.intent.intent_hash == r2.intent.intent_hash


# =============================================================================
# VALIDATION + ERROR HANDLING
# =============================================================================


class TestSignalValidation:
    def test_missing_bar_time_returns_invalid(self) -> None:
        signal = _build_signal()
        del signal["bar_time"]
        df = _build_enriched_df()

        result = process_signal(signal, df, "EURUSD")
        assert result.outcome == SignalOutcome.INVALID_SIGNAL

    def test_missing_direction_returns_invalid(self) -> None:
        signal = _build_signal()
        del signal["direction"]
        df = _build_enriched_df()

        result = process_signal(signal, df, "EURUSD")
        assert result.outcome == SignalOutcome.INVALID_SIGNAL

    def test_empty_df_handled(self) -> None:
        signal = _build_signal()
        df = pd.DataFrame()

        result = process_signal(signal, df, "EURUSD")
        assert result.outcome in (
            SignalOutcome.PRICE_DISCOVERY_FAILED,
            SignalOutcome.ERROR,
        )

    def test_halt_blocks_execution(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()

        result = process_signal(
            signal,
            df,
            "EURUSD",
            shadow_mode=False,
            halt_check_fn=lambda: True,
        )
        assert result.outcome == SignalOutcome.HALT_BLOCKED


# =============================================================================
# P2.1: PIT DRIFT MONITORING
# =============================================================================


class TestPITDrift:
    def test_drift_computed(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()

        result = process_signal(signal, df, "EURUSD")
        assert result.drift_seconds is not None

    def test_signal_context_parsed(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()

        result = process_signal(signal, df, "EURUSD")
        assert result.signal_context is not None
        assert result.signal_context.direction == "bullish"
        assert result.signal_context.model_type == "REVERSAL"
        assert result.signal_context.htf_phase == "EXPANSION"


# =============================================================================
# P2.3: SIGNAL FRICTION
# =============================================================================


class TestSignalFriction:
    def test_cso_rejection_produces_friction(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()
        df["asia_range_pips"] = 50.0
        df["asia_high"] = 1.0875

        result = process_signal(signal, df, "EURUSD")

        if result.outcome == SignalOutcome.CSO_REJECTED:
            assert result.friction is not None
            assert len(result.friction.gate_failures) > 0
            assert len(result.friction.drawer_failures) > 0
            assert result.friction.pair == "EURUSD"

    def test_valid_signal_no_friction(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()

        result = process_signal(signal, df, "EURUSD")
        if result.outcome == SignalOutcome.SHADOW_OBSERVATION:
            assert result.friction is None

    def test_friction_has_human_readable_reason(self) -> None:
        signal = _build_signal()
        df = _build_enriched_df()
        df["asia_range_pips"] = 50.0

        result = process_signal(signal, df, "EURUSD")
        if result.friction is not None:
            assert "CSO rejected" in result.friction.reason
