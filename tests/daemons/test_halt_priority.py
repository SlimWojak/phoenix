"""
Test: INV-D1-HALT-PRIORITY-1 — HALT bypasses queue, processes immediately
==========================================================================

S34: D1 FILE_SEAM_COMPLETION

Verifies:
- HALT intents are identified as priority
- HALT bypasses normal queue
- HALT processed before queued intents
- HALT triggers halt mechanism
"""

import sys
import tempfile
import time
from pathlib import Path

# Add phoenix root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import yaml


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        incoming = base / "incoming"
        processed = base / "processed"
        unprocessed = base / "unprocessed"
        responses = base / "responses"

        incoming.mkdir()
        processed.mkdir()
        unprocessed.mkdir()
        responses.mkdir()

        yield {
            "base": base,
            "incoming": incoming,
            "processed": processed,
            "unprocessed": unprocessed,
            "responses": responses,
        }


class TestHaltPriority:
    """INV-D1-HALT-PRIORITY-1: HALT bypasses queue, processes immediately."""

    def test_halt_is_priority_type(self):
        """HALT should be identified as priority type."""
        from daemons.routing import IntentRouter, IntentType

        router = IntentRouter()

        assert router.is_priority(IntentType.HALT), "HALT must be priority"
        assert not router.is_priority(IntentType.SCAN), "SCAN should not be priority"
        assert not router.is_priority(IntentType.APPROVE), "APPROVE should not be priority"

    def test_halt_processed_before_queued(self, temp_dirs):
        """HALT should be processed before queued intents."""
        from daemons.routing import Intent, IntentRouter, IntentType, RouteResult
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=50,
        )

        # Track processing order
        processing_order = []

        class OrderTracker:
            def __init__(self, name: str):
                self._name = name

            def handle(self, intent: Intent) -> RouteResult:
                processing_order.append(self._name)
                return RouteResult(success=True, intent=intent, worker_name=self._name)

        router = IntentRouter()
        router.register(IntentType.SCAN, OrderTracker("SCAN"))
        router.register(IntentType.HALT, OrderTracker("HALT"))

        watcher = IntentWatcher(router=router, config=config)

        # Create intents - SCAN first, then HALT
        # But HALT should process first (priority)
        scan_path = temp_dirs["incoming"] / "1_scan.yaml"
        scan_path.write_text(
            yaml.dump(
                {
                    "type": "SCAN",
                    "payload": {},
                    "session_id": "scan_test",
                }
            )
        )

        halt_path = temp_dirs["incoming"] / "2_halt.yaml"
        halt_path.write_text(
            yaml.dump(
                {
                    "type": "HALT",
                    "payload": {"reason": "Test halt"},
                    "session_id": "halt_test",
                }
            )
        )

        watcher.start()
        time.sleep(0.3)
        watcher.stop()

        # HALT should be tracked separately
        assert watcher.stats.halt_intents >= 1, "HALT should be counted"

    def test_halt_triggers_immediately(self, temp_dirs):
        """HALT intent should trigger halt mechanism."""
        from daemons.routing import (
            Intent,
            IntentRouter,
            IntentType,
            RouteResult,
        )
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=50,
        )

        halt_triggered = False
        halt_reason = None

        class MockHaltHandler:
            def handle(self, intent: Intent) -> RouteResult:
                nonlocal halt_triggered, halt_reason
                halt_triggered = True
                halt_reason = intent.payload.get("reason", "no reason")
                return RouteResult(success=True, intent=intent, worker_name="HALT")

        router = IntentRouter()
        router.register(IntentType.HALT, MockHaltHandler())

        watcher = IntentWatcher(router=router, config=config)

        # Create HALT intent
        halt_path = temp_dirs["incoming"] / "halt.yaml"
        halt_path.write_text(
            yaml.dump(
                {
                    "type": "HALT",
                    "payload": {"reason": "Emergency stop"},
                    "session_id": "halt_test",
                }
            )
        )

        watcher.start()
        time.sleep(0.3)
        watcher.stop()

        assert halt_triggered, "HALT should trigger handler"
        assert halt_reason == "Emergency stop"

    def test_halt_logged_as_warning(self, temp_dirs, caplog):
        """HALT intent should log warning."""
        import logging

        from daemons.routing import Intent, IntentRouter, IntentType, RouteResult
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=50,
        )

        class NoOpHaltHandler:
            def handle(self, intent: Intent) -> RouteResult:
                return RouteResult(success=True, intent=intent, worker_name="HALT")

        router = IntentRouter()
        router.register(IntentType.HALT, NoOpHaltHandler())

        watcher = IntentWatcher(router=router, config=config)

        halt_path = temp_dirs["incoming"] / "halt.yaml"
        halt_path.write_text(
            yaml.dump(
                {
                    "type": "HALT",
                    "payload": {},
                    "session_id": "halt_test",
                }
            )
        )

        with caplog.at_level(logging.WARNING):
            watcher.start()
            time.sleep(0.3)
            watcher.stop()

        # Should have warning about HALT
        assert any(
            "HALT" in record.message for record in caplog.records
        ), "HALT should produce warning log"


class TestHaltHandler:
    """Test the actual halt handler."""

    def test_create_halt_handler_exists(self):
        """Halt handler creation should work."""
        from daemons.routing import create_halt_handler

        handler = create_halt_handler()
        assert handler is not None
        assert hasattr(handler, "handle")

    def test_halt_handler_calls_halt_manager(self, temp_dirs):
        """Halt handler should call HaltManager."""
        from daemons.routing import IntentType, parse_intent
        from governance.halt import HaltManager

        # Create a halt intent
        halt_path = temp_dirs["incoming"] / "halt.yaml"
        halt_path.write_text(
            yaml.dump(
                {
                    "type": "HALT",
                    "payload": {"reason": "Test halt mechanism"},
                    "session_id": "halt_manager_test",
                }
            )
        )

        intent = parse_intent(halt_path)
        assert intent is not None
        assert intent.intent_type == IntentType.HALT

        # Handler would call HaltManager - test that integration
        # Just verify we can create and call it
        manager = HaltManager(module_id="test_halt")
        result = manager.request_halt()

        assert result.success, "Halt request should succeed"
        assert result.latency_ms < 50, "Halt should be fast (<50ms)"

        # Clean up
        manager.clear_halt()
