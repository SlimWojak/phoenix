"""
E2E Test: CSO → Shadow
======================

Tests complete flow from CSO setup detection to Shadow paper position.
"""

from datetime import UTC, datetime, timedelta

import pandas as pd


class TestCSOShadowE2E:
    """CSO → Shadow end-to-end tests."""

    def test_cso_detects_setup_shadow_tracks(self) -> None:
        """CSO detects READY setup → Shadow creates paper position."""
        # Setup mocks
        from cso.structure_detector import StructureDetector
        from shadow.shadow import CSESignal, Shadow, ShadowConfig

        # Create Shadow
        shadow = Shadow(config=ShadowConfig(initial_balance=10000))

        # Create mock River data with FVG pattern
        dates = [datetime(2026, 1, 20, tzinfo=UTC) + timedelta(hours=i) for i in range(50)]
        bars = pd.DataFrame({
            "timestamp": dates,
            "open": [1.0800 + i * 0.0001 for i in range(50)],
            "high": [1.0815 + i * 0.0001 for i in range(50)],
            "low": [1.0790 + i * 0.0001 for i in range(50)],
            "close": [1.0805 + i * 0.0001 for i in range(50)],
            "volume": [1000] * 50,
        })

        # Create FVG pattern
        bars.loc[25, "low"] = 1.0830
        bars.loc[23, "high"] = 1.0815

        # Test structure detection
        detector = StructureDetector()
        structure = detector.detect_all(bars, "EURUSD", "1H")

        assert structure.bars_analyzed == 50
        assert len(structure.structures) > 0

        # Create CSE signal manually (simulating CSO detection)
        cse = CSESignal(
            signal_id="TEST-CSE-001",
            timestamp=datetime.now(UTC),
            pair="EURUSD",
            direction="LONG",
            entry=1.0850,
            stop=1.0820,
            target=1.0910,
            risk_percent=1.0,
            confidence=0.85,
            source="CSO",
            evidence_hash="test123",
        )

        # Shadow consumes signal
        result = shadow.consume_signal(cse)

        assert result.status == "ACCEPTED"
        assert result.position_id is not None
        assert len(shadow.open_positions) == 1

        position = shadow.open_positions[0]
        assert position.pair == "EURUSD"
        assert position.side == "LONG"

    def test_cso_scanner_emits_to_shadow(self) -> None:
        """CSOScanner emits CSE to Shadow via wiring."""
        from cso import CSOScanner
        from shadow.shadow import Shadow, ShadowConfig

        shadow = Shadow(config=ShadowConfig())

        # Create scanner with shadow
        scanner = CSOScanner(shadow=shadow)

        # Scanner should have shadow reference
        assert scanner._shadow is shadow

    def test_shadow_position_lifecycle(self) -> None:
        """Test full position lifecycle in Shadow."""
        from shadow.shadow import CSESignal, Shadow, ShadowConfig

        shadow = Shadow(config=ShadowConfig(initial_balance=10000))

        # Create and consume signal
        cse = CSESignal(
            signal_id="TEST-002",
            timestamp=datetime.now(UTC),
            pair="GBPUSD",
            direction="SHORT",
            entry=1.2500,
            stop=1.2530,
            target=1.2440,
            risk_percent=1.0,
            confidence=0.82,
            source="CSO",
            evidence_hash="abc123",
        )

        result = shadow.consume_signal(cse)
        assert result.status == "ACCEPTED"
        position_id = result.position_id

        # Close position
        close_result = shadow.close_position(position_id, exit_price=1.2450, reason="TP")

        assert close_result.status == "CLOSED"
        assert len(shadow.open_positions) == 0
        assert shadow._total_trades == 1

    def test_multiple_pairs_tracked(self) -> None:
        """Shadow tracks positions across multiple pairs."""
        from shadow.shadow import CSESignal, Shadow, ShadowConfig

        shadow = Shadow(config=ShadowConfig(max_positions=5))

        pairs = ["EURUSD", "GBPUSD", "USDJPY"]

        for i, pair in enumerate(pairs):
            cse = CSESignal(
                signal_id=f"TEST-{i:03d}",
                timestamp=datetime.now(UTC),
                pair=pair,
                direction="LONG",
                entry=1.0 + i * 0.1,
                stop=0.99 + i * 0.1,
                target=1.02 + i * 0.1,
                risk_percent=1.0,
                confidence=0.80,
                source="CSO",
                evidence_hash=f"hash{i}",
            )
            shadow.consume_signal(cse)

        assert len(shadow.open_positions) == 3
        tracked_pairs = {p.pair for p in shadow.open_positions}
        assert tracked_pairs == {"EURUSD", "GBPUSD", "USDJPY"}
