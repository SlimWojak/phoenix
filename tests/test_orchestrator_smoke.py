"""
Strategy Orchestrator Smoke Test — DEPLOY.P1.5
================================================

BOAR's Monday readiness gate.

PRIMARY: Replay known ARS trade through full constitutional path.
CHAOS: Pre-flight failure, halt block, invalid setup, shadow enforcement.

EXIT GATE:
  - Full constitutional path exercised on known data
  - Paper position would open if shadow_mode=False
  - All governance gates verified
  - Chaos scenarios handled (no silent failures)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd

from daemons.strategy_orchestrator import (
    BarOutcome,
    OrchestratorConfig,
    StrategyOrchestrator,
)


def _build_valid_ars_df() -> pd.DataFrame:
    """
    Build enriched DataFrame for a known valid ARS setup.

    Scenario: EURUSD, 20-pip Asia range, bullish 8-pip sweep,
    re-acceptance, FVG present, candle C inside range.
    """
    pip = 0.0001
    base = 1.0850
    asia_high = 1.0860
    asia_low = 1.0840

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
    df["trading_day"] = ny_hours.apply(
        lambda x: x.date() if x.hour >= 17 else (x - timedelta(days=1)).date()
    )
    df["session_name"] = "off_session"
    df["is_asia_session"] = False
    df["is_london_session"] = False
    df["is_ny_session"] = False
    df["kz_active"] = False

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

    # FVG placed at bar 100 (~06:40 UTC) so it's within the 12-bar tail
    # window when evaluated at now=06:50 UTC
    fvg_bar = 100
    df.loc[fvg_bar, "fvg_bull"] = True
    df.loc[fvg_bar, "fvg_bull_high"] = base + 1.0 * pip
    df.loc[fvg_bar, "fvg_bull_low"] = base - 1.0 * pip
    df.loc[fvg_bar, "close"] = 1.0842

    df["knowledge_time"] = df["timestamp"] + timedelta(seconds=1)

    return df


# =============================================================================
# PRIMARY: Constitutional path on known valid setup
# =============================================================================


class TestConstitutionalPath:
    """Full constitutional chain on known ARS data."""

    def test_pre_flight_passes(self) -> None:
        orch = StrategyOrchestrator()
        result = orch.pre_flight()
        assert result.healthy
        assert result.checks["enrichment_importable"]
        assert result.checks["halt_clear"]
        assert result.checks["registry_loaded"]

    def test_valid_setup_detected_shadow_mode(self) -> None:
        """Known valid setup → all drawers pass → shadow observation recorded."""
        config = OrchestratorConfig(shadow_mode=True)
        orch = StrategyOrchestrator(config)

        df = _build_valid_ars_df()
        # FVG at bar 100 (~08:20 UTC); evaluate just after
        now = datetime(2026, 2, 21, 8, 25, tzinfo=UTC)

        result = orch.process_bar(df, "EURUSD", now)

        assert result.outcome == BarOutcome.SHADOW_OBSERVATION, (
            f"Expected SHADOW_OBSERVATION, got {result.outcome}: "
            f"{result.rejection_reason or result.error}"
        )
        assert result.shadow_observation is not None
        assert result.proposal is not None
        assert result.intent is not None
        assert len(orch.shadow_observations) == 1

    def test_valid_setup_produces_intent_when_not_shadow(self) -> None:
        """Same setup with shadow_mode=False → INTENT_CREATED."""
        config = OrchestratorConfig(shadow_mode=False)
        orch = StrategyOrchestrator(config)

        df = _build_valid_ars_df()
        now = datetime(2026, 2, 21, 8, 25, tzinfo=UTC)

        result = orch.process_bar(df, "EURUSD", now)

        assert result.outcome == BarOutcome.INTENT_CREATED
        assert result.intent is not None
        assert result.proposal is not None

    def test_five_drawer_result_present(self) -> None:
        config = OrchestratorConfig(shadow_mode=True)
        orch = StrategyOrchestrator(config)

        df = _build_valid_ars_df()
        now = datetime(2026, 2, 21, 8, 25, tzinfo=UTC)

        result = orch.process_bar(df, "EURUSD", now)
        assert result.five_drawer is not None
        assert all(result.five_drawer.drawer_status.values())

    def test_proposal_has_full_geometry(self) -> None:
        config = OrchestratorConfig(shadow_mode=True)
        orch = StrategyOrchestrator(config)

        df = _build_valid_ars_df()
        now = datetime(2026, 2, 21, 8, 25, tzinfo=UTC)

        result = orch.process_bar(df, "EURUSD", now)
        assert result.proposal is not None
        assert result.proposal.entry_price > 0
        assert result.proposal.stop_loss > 0
        assert result.proposal.take_profit > 0
        assert result.proposal.rr_ratio >= 1.5
        assert result.proposal.position_size_lots > 0


# =============================================================================
# CHAOS: Governance failures handled correctly
# =============================================================================


class TestChaosVectors:
    """BOAR: No silent failures."""

    def test_halt_blocks_execution(self) -> None:
        config = OrchestratorConfig(
            shadow_mode=False,
            halt_check_fn=lambda: True,
        )
        orch = StrategyOrchestrator(config)

        df = _build_valid_ars_df()
        now = datetime(2026, 2, 21, 8, 25, tzinfo=UTC)

        result = orch.process_bar(df, "EURUSD", now)
        assert result.outcome == BarOutcome.HALT_BLOCKED

    def test_pre_flight_catches_halt(self) -> None:
        config = OrchestratorConfig(halt_check_fn=lambda: True)
        orch = StrategyOrchestrator(config)
        result = orch.pre_flight()
        assert not result.healthy
        assert "HALT" in result.errors[0]

    def test_invalid_setup_rejected(self) -> None:
        """Range > 30 pips → rejected."""
        config = OrchestratorConfig(shadow_mode=True)
        orch = StrategyOrchestrator(config)

        df = _build_valid_ars_df()
        df["asia_range_pips"] = 50.0
        df["asia_high"] = 1.0875
        now = datetime(2026, 2, 21, 8, 25, tzinfo=UTC)

        result = orch.process_bar(df, "EURUSD", now)
        assert result.outcome in (BarOutcome.SETUP_REJECTED, BarOutcome.NO_SETUP)

    def test_empty_dataframe_handled(self) -> None:
        config = OrchestratorConfig(shadow_mode=True)
        orch = StrategyOrchestrator(config)

        df = pd.DataFrame()
        now = datetime(2026, 2, 21, 8, 25, tzinfo=UTC)

        result = orch.process_bar(df, "EURUSD", now)
        assert result.outcome in (BarOutcome.NO_SETUP, BarOutcome.ERROR)

    def test_shadow_mode_prevents_execution(self) -> None:
        """Even with valid setup, shadow_mode=True → no INTENT_CREATED."""
        config = OrchestratorConfig(shadow_mode=True)
        orch = StrategyOrchestrator(config)

        df = _build_valid_ars_df()
        now = datetime(2026, 2, 21, 8, 25, tzinfo=UTC)

        result = orch.process_bar(df, "EURUSD", now)
        assert result.outcome != BarOutcome.INTENT_CREATED

    def test_halt_check_error_doesnt_crash(self) -> None:
        def bad_halt() -> bool:
            raise ConnectionError("IBKR gateway unreachable")

        config = OrchestratorConfig(
            shadow_mode=False,
            halt_check_fn=bad_halt,
        )
        orch = StrategyOrchestrator(config)

        df = _build_valid_ars_df()
        now = datetime(2026, 2, 21, 8, 25, tzinfo=UTC)

        result = orch.process_bar(df, "EURUSD", now)
        assert result.outcome == BarOutcome.ERROR
        assert "halt check failed" in (result.error or "")


# =============================================================================
# REPLAY: Historical bar processing
# =============================================================================


class TestReplayHistorical:
    """Replay enriched bars through the chain."""

    def test_replay_processes_multiple_bars(self) -> None:
        config = OrchestratorConfig(shadow_mode=True)
        orch = StrategyOrchestrator(config)

        df = _build_valid_ars_df()
        timestamps = [
            datetime(2026, 2, 21, 6, 0, tzinfo=UTC),
            datetime(2026, 2, 21, 7, 0, tzinfo=UTC),
            datetime(2026, 2, 21, 7, 30, tzinfo=UTC),
        ]

        results = orch.replay_historical(df, "EURUSD", timestamps)
        assert len(results) == 3
        assert all(r.pair == "EURUSD" for r in results)
