"""
E2E Test: Shadow → Autopsy
==========================

Tests position close triggering autopsy bead emission.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock


class TestAutopsyFlowE2E:
    """Shadow → Autopsy end-to-end tests."""

    def test_position_close_triggers_autopsy(self) -> None:
        """Closed position triggers autopsy via _trigger_autopsy method."""
        from shadow.shadow import CSESignal, Shadow, ShadowConfig

        # Create mock autopsy that tracks calls
        mock_autopsy = MagicMock()
        mock_autopsy.analyze = MagicMock(return_value=MagicMock(autopsy_bead_id="TEST"))

        shadow = Shadow(
            config=ShadowConfig(),
            autopsy=mock_autopsy,
        )

        # Open position
        cse = CSESignal(
            signal_id="AUTOPSY-TEST-001",
            timestamp=datetime.now(UTC),
            pair="EURUSD",
            direction="LONG",
            entry=1.0850,
            stop=1.0820,
            target=1.0910,
            risk_percent=1.0,
            confidence=0.85,
            source="CSO",
            evidence_hash="autopsy_test",
        )

        result = shadow.consume_signal(cse)
        position_id = result.position_id

        # Close position (should trigger autopsy)
        shadow.close_position(position_id, exit_price=1.0900, reason="TP")

        # Verify autopsy.analyze was called
        mock_autopsy.analyze.assert_called_once()

    def test_autopsy_bead_contains_learnings(self) -> None:
        """Autopsy bead contains extracted learnings."""
        from analysis import Autopsy

        mock_bead_store = MagicMock()
        mock_bead_store.write_dict = MagicMock()

        autopsy = Autopsy(bead_store=mock_bead_store)

        result = autopsy.analyze(
            position_id="POS-001",
            entry_thesis={"confidence": 0.8, "setup_type": "FVG_ENTRY"},
            outcome={"result": "WIN", "pnl_percent": 2.5},
        )

        assert result.autopsy_bead_id.startswith("AUTOPSY-")
        assert result.comparison.thesis_valid is True
        assert len(result.comparison.learnings) > 0

    def test_autopsy_fallback_no_llm(self) -> None:
        """Autopsy uses rule-based extraction when LLM unavailable."""
        from analysis import LearningExtractor
        from analysis.learning_extractor import ExtractionMethod

        extractor = LearningExtractor(llm_client=None)

        result = extractor.extract(
            trade_data={
                "outcome": {"result": "LOSS", "pnl_percent": -1.5},
                "entry_thesis": {"confidence": 0.7},
            }
        )

        assert result.method_used == ExtractionMethod.RULE_BASED
        assert result.llm_available is False
        assert len(result.learnings) > 0

    def test_autopsy_win_vs_loss_learnings(self) -> None:
        """Different learnings for wins vs losses."""
        from analysis import Autopsy

        autopsy = Autopsy()

        # Win
        win_result = autopsy.analyze(
            position_id="WIN-001",
            entry_thesis={"confidence": 0.85},
            outcome={"result": "WIN", "pnl_percent": 3.0},
        )

        # Loss
        loss_result = autopsy.analyze(
            position_id="LOSS-001",
            entry_thesis={"confidence": 0.85},
            outcome={"result": "LOSS", "pnl_percent": -1.5},
        )

        # Win should have valid thesis
        assert win_result.comparison.thesis_valid is True

        # Loss with high confidence = invalid thesis
        assert loss_result.comparison.thesis_valid is False

    def test_autopsy_bead_schema(self) -> None:
        """Autopsy bead matches expected schema."""
        from analysis import Autopsy

        mock_bead_store = MagicMock()
        captured_bead = None

        def capture_bead(bead_dict: dict) -> None:
            nonlocal captured_bead
            captured_bead = bead_dict

        mock_bead_store.write_dict = capture_bead

        autopsy = Autopsy(bead_store=mock_bead_store)

        autopsy.analyze(
            position_id="SCHEMA-TEST",
            entry_thesis={"confidence": 0.7, "setup_type": "OTE"},
            outcome={"result": "WIN", "pnl_percent": 1.0},
        )

        assert captured_bead is not None
        assert captured_bead["bead_type"] == "AUTOPSY"
        assert "content" in captured_bead
        assert "position_id" in captured_bead["content"]
        assert "comparison" in captured_bead["content"]
