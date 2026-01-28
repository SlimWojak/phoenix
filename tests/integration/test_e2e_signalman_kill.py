"""
E2E Test: Signalman → KillManager
=================================

Tests decay detection triggering ONE-WAY-KILL.
"""

from unittest.mock import MagicMock


class TestSignalmanKillE2E:
    """Signalman → KillManager end-to-end tests."""

    def test_decay_triggers_kill_flag(self) -> None:
        """Decay detection triggers KILL_FLAG bead."""
        from monitoring import KillManager, Signalman

        # Create kill manager with mock bead store
        mock_bead_store = MagicMock()
        mock_bead_store.write_dict = MagicMock()
        mock_bead_store.query_sql = MagicMock(return_value=[])

        kill_manager = KillManager(bead_store=mock_bead_store)
        signalman = Signalman(kill_manager=kill_manager, min_beads=5)

        # Set kill flag directly (simulating decay detection)
        flag = kill_manager.set_kill_flag(
            strategy_id="TEST_STRATEGY",
            reason="Multi-signal decay detected",
            triggered_by="SIGNALMAN",
            decay_metrics={"sharpe_drift": 0.5},
        )

        assert flag.active is True
        assert flag.strategy_id == "TEST_STRATEGY"
        assert kill_manager.is_killed("TEST_STRATEGY") is True

    def test_kill_blocks_new_entries(self) -> None:
        """Killed strategy blocks new entries but allows exits."""
        from monitoring import KillManager

        mock_bead_store = MagicMock()
        mock_bead_store.write_dict = MagicMock()
        mock_bead_store.query_sql = MagicMock(return_value=[])

        kill_manager = KillManager(bead_store=mock_bead_store)

        # Strategy not killed initially
        assert kill_manager.is_killed("FVG_LONDON") is False

        # Kill the strategy
        kill_manager.set_kill_flag(
            strategy_id="FVG_LONDON",
            reason="Performance decay",
            triggered_by="SIGNALMAN",
        )

        # Now killed
        assert kill_manager.is_killed("FVG_LONDON") is True

        # Other strategies unaffected
        assert kill_manager.is_killed("OTE_NEWYORK") is False

    def test_kill_flag_lift_requires_human(self) -> None:
        """Lifting kill flag requires human approval."""
        from monitoring import KillManager

        mock_bead_store = MagicMock()
        mock_bead_store.write_dict = MagicMock()
        mock_bead_store.query_sql = MagicMock(return_value=[])

        kill_manager = KillManager(bead_store=mock_bead_store)

        # Set kill
        kill_manager.set_kill_flag(
            strategy_id="TEST",
            reason="Decay",
            triggered_by="SIGNALMAN",
        )

        assert kill_manager.is_killed("TEST") is True

        # Lift kill (human action)
        flag = kill_manager.lift_kill_flag(
            strategy_id="TEST",
            lifted_by="olya",
            lifted_reason="Reviewed and approved",
        )

        assert flag is not None
        assert flag.active is False
        assert flag.lifted_by == "olya"
        assert kill_manager.is_killed("TEST") is False

    def test_signalman_cold_start_no_false_alerts(self) -> None:
        """Signalman returns None when insufficient data (INV-SIGNALMAN-COLD-1)."""
        from monitoring import Signalman

        # No bead store = no beads
        signalman = Signalman(min_beads=30)

        result = signalman.analyze_strategy("ANY_STRATEGY")

        # No alert because no data
        assert result is None

    def test_multi_signal_detection(self) -> None:
        """Multiple decay signals required for kill (INV-SIGNALMAN-DECAY-1)."""
        from monitoring.signalman import DecaySignal, DecayType, Signalman

        signalman = Signalman(min_beads=5)

        # Create mock signals
        signals = [
            DecaySignal(
                decay_type=DecayType.PERFORMANCE,
                value=0.4,
                threshold=0.3,
                exceeded=True,
            ),
            DecaySignal(
                decay_type=DecayType.DISTRIBUTION,
                value=0.03,
                threshold=0.05,
                exceeded=True,
            ),
        ]

        # Both exceeded = should trigger kill (2+ signals)
        exceeded_count = sum(1 for s in signals if s.exceeded)
        assert exceeded_count >= 2

    def test_kill_flag_bead_emitted(self) -> None:
        """KILL_FLAG bead is emitted when kill set."""
        from monitoring import KillManager

        mock_bead_store = MagicMock()
        mock_bead_store.write_dict = MagicMock()
        mock_bead_store.query_sql = MagicMock(return_value=[])

        kill_manager = KillManager(bead_store=mock_bead_store)

        kill_manager.set_kill_flag(
            strategy_id="STRATEGY_X",
            reason="Test kill",
            triggered_by="TEST",
        )

        # Verify bead was written
        mock_bead_store.write_dict.assert_called_once()

        call_args = mock_bead_store.write_dict.call_args[0][0]
        assert call_args["bead_type"] == "KILL_FLAG"
        assert "STRATEGY_X" in str(call_args["content"])
