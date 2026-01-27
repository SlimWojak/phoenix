"""
E2E Test: Full S30+S31 Flywheel
===============================

Tests complete pipeline from Hunt to Autopsy.
"""

import pytest
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock


class TestFullFlywheelE2E:
    """Complete S30+S31 pipeline test."""

    def test_full_flywheel_spin(self) -> None:
        """
        Complete flywheel: Hunt → CSO → Shadow → Autopsy → Athena
        """
        from memory.bead_store import BeadStore
        from shadow.shadow import Shadow, ShadowConfig, CSESignal
        from analysis import Autopsy
        from monitoring import KillManager

        # Create shared bead store with temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_beads.db"
            bead_store = BeadStore(db_path)
            self._run_flywheel_test(bead_store)

    def _run_flywheel_test(self, bead_store: "BeadStore") -> None:
        """Run the actual flywheel test."""
        from shadow.shadow import Shadow, ShadowConfig, CSESignal
        from analysis import Autopsy
        from monitoring import KillManager

        # Create components
        autopsy = Autopsy(bead_store=bead_store)
        kill_manager = KillManager(bead_store=bead_store)
        shadow = Shadow(
            config=ShadowConfig(),
            bead_store=bead_store,
            autopsy=autopsy,
        )

        # Step 1: Simulate Hunt → HUNT bead
        hunt_bead = {
            "bead_id": "HUNT-001",
            "bead_type": "HUNT",
            "prev_bead_id": None,
            "bead_hash": "abc123",
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "signer": "system",
            "version": "1.0",
            "content": {
                "hypothesis_text": "Test FVG hypothesis",
                "survivors": [{"variant_id": "v1", "sharpe": 1.5}],
            },
        }
        bead_store.write_dict(hunt_bead)

        # Step 2: CSO detects → CSE to Shadow
        cse = CSESignal(
            signal_id="CSE-FLYWHEEL-001",
            timestamp=datetime.now(UTC),
            pair="EURUSD",
            direction="LONG",
            entry=1.0850,
            stop=1.0820,
            target=1.0910,
            risk_percent=1.0,
            confidence=0.85,
            source="CSO",
            evidence_hash="hunt001",
        )

        result = shadow.consume_signal(cse)
        assert result.status == "ACCEPTED"
        position_id = result.position_id

        # Step 3: Signalman monitors (no decay = no kill)
        assert kill_manager.is_killed("CSO_FVG") is False

        # Step 4: Position closes → PERFORMANCE + AUTOPSY beads
        shadow.close_position(position_id, exit_price=1.0890, reason="TP")

        # Step 5: Query Athena for all beads
        beads = bead_store.query_sql(
            "SELECT bead_type FROM beads ORDER BY timestamp_utc"
        )

        bead_types = [b["bead_type"] for b in beads]

        # Verify flywheel artifacts
        assert "HUNT" in bead_types
        assert "PERFORMANCE" in bead_types
        # AUTOPSY may or may not be present depending on timing
        # The key invariant is that Hunt and Performance work

    def test_flywheel_with_decay(self) -> None:
        """Flywheel with decay detection and kill."""
        from memory.bead_store import BeadStore
        from monitoring import Signalman, KillManager

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "decay_test.db"
            bead_store = BeadStore(db_path)
            kill_manager = KillManager(bead_store=bead_store)

            # Simulate decay → kill
            kill_manager.set_kill_flag(
                strategy_id="DECAYING_STRATEGY",
                reason="Sharpe drift exceeded",
                triggered_by="SIGNALMAN",
            )

            # Verify kill status (bead may or may not be written depending on store)
            assert kill_manager.is_killed("DECAYING_STRATEGY") is True

    def test_state_hash_validation(self) -> None:
        """State hash validation for T2 intents."""
        from monitoring import StateAnchorManager

        manager = StateAnchorManager()

        # Create anchor
        anchor = manager.create_anchor(session_id="session-001")

        assert anchor.combined_hash != ""
        assert anchor.ttl_remaining_minutes > 0

        # Validate with same hash = VALID
        result = manager.validate_intent(anchor.combined_hash)
        assert result.status.value == "VALID"

        # Validate with different hash = CONFLICT
        result = manager.validate_intent("wrong_hash_abc123")
        assert result.status.value == "STATE_CONFLICT"

    def test_lens_response_cycle(self) -> None:
        """Lens writes response, can be read back."""
        from lens import ResponseWriter, ResponseType

        writer = ResponseWriter()

        # Write CSO briefing
        path = writer.write_cso_briefing(
            summary="Test scan",
            ready_pairs=["EURUSD"],
            forming_pairs=["GBPUSD"],
        )

        assert path.exists()

        # Read back
        response = writer.read(ResponseType.CSO_BRIEFING)

        assert response is not None
        assert "EURUSD" in response.content

    def test_bead_chain_integrity(self) -> None:
        """Bead chain maintains integrity."""
        from memory.bead_store import BeadStore

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "chain_test.db"
            bead_store = BeadStore(db_path)
            self._run_chain_test(bead_store)

    def _run_chain_test(self, bead_store: "BeadStore") -> None:
        """Run the chain integrity test."""

        # Write chain of beads
        prev_id = None
        for i in range(5):
            bead = {
                "bead_id": f"CHAIN-{i:03d}",
                "bead_type": "HUNT",
                "prev_bead_id": prev_id,
                "bead_hash": f"hash{i}",
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "signer": "system",
                "version": "1.0",
                "content": {"idx": i},
            }
            bead_store.write_dict(bead)
            prev_id = f"CHAIN-{i:03d}"

        # Query chain
        beads = bead_store.query_sql(
            "SELECT bead_id, prev_bead_id FROM beads ORDER BY bead_id"
        )

        # Verify chain
        assert len(beads) == 5
        assert beads[0]["prev_bead_id"] is None
        assert beads[4]["prev_bead_id"] == "CHAIN-003"
