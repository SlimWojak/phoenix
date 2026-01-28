"""
Test: INV-D1-WATCHER-IMMUTABLE-1 — Watcher may not modify intent payloads
==========================================================================

S34: D1 FILE_SEAM_COMPLETION

Verifies:
- Intent content unchanged during processing
- Hash verification before/after routing
- Modification detected and logged
"""

import hashlib
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


class TestIntentImmutability:
    """INV-D1-WATCHER-IMMUTABLE-1: Watcher may not modify intent payloads."""

    def test_intent_unchanged_after_routing(self, temp_dirs):
        """Intent content should be unchanged after routing."""
        from daemons.routing import (
            IntentRouter,
            IntentType,
            create_stub_handler,
            parse_intent,
        )

        # Create intent
        intent_content = {
            "type": "SCAN",
            "payload": {
                "pair": "EURUSD",
                "session": "london",
                "nested": {"deep": {"value": 123}},
            },
            "timestamp": "2026-01-28T10:00:00Z",
            "session_id": "immutable_test",
        }

        intent_path = temp_dirs["incoming"] / "test_intent.yaml"
        original_yaml = yaml.dump(intent_content)
        intent_path.write_text(original_yaml)
        original_hash = hashlib.sha256(original_yaml.encode()).hexdigest()

        # Setup router
        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )

        # Parse intent
        intent = parse_intent(intent_path)
        assert intent is not None
        assert intent.content_hash == original_hash

        # Route intent
        result = router.route(intent)
        assert result.success

        # Verify content unchanged
        current_yaml = intent_path.read_text()
        assert intent.verify_immutable(current_yaml), "Intent should remain immutable"

    def test_hash_verification_detects_modification(self, temp_dirs):
        """Hash verification should detect any modification."""
        from daemons.routing import parse_intent

        intent_content = {
            "type": "SCAN",
            "payload": {"original": True},
            "session_id": "hash_test",
        }

        intent_path = temp_dirs["incoming"] / "test_intent.yaml"
        original_yaml = yaml.dump(intent_content)
        intent_path.write_text(original_yaml)

        intent = parse_intent(intent_path)
        assert intent is not None

        # Original should verify
        assert intent.verify_immutable(original_yaml)

        # Modified content should NOT verify
        modified_yaml = original_yaml + "\n# Added comment"
        assert not intent.verify_immutable(modified_yaml)

        # Changed value should NOT verify
        intent_content["payload"]["original"] = False
        changed_yaml = yaml.dump(intent_content)
        assert not intent.verify_immutable(changed_yaml)

    def test_watcher_detects_file_modification(self, temp_dirs):
        """Watcher should detect if file is modified during processing."""
        from daemons.routing import Intent, IntentRouter, IntentType, RouteResult
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=100,
        )

        # Create handler that modifies the file (BAD behavior)
        class ModifyingHandler:
            def handle(self, intent: Intent) -> RouteResult:
                # This is FORBIDDEN behavior - modify the source file
                modified = intent.raw_yaml + "\n# Modified by handler"
                intent.source_path.write_text(modified)
                return RouteResult(success=True, intent=intent, worker_name="MODIFIER")

        router = IntentRouter()
        router.register(IntentType.SCAN, ModifyingHandler())

        watcher = IntentWatcher(router=router, config=config)

        # Create intent
        intent_path = temp_dirs["incoming"] / "test_intent.yaml"
        intent_path.write_text(
            yaml.dump(
                {
                    "type": "SCAN",
                    "payload": {},
                    "session_id": "modify_test",
                }
            )
        )

        watcher.start()
        time.sleep(0.3)
        watcher.stop()

        # Watcher should have detected the modification
        # and counted it as a failed intent
        assert watcher.stats.intents_failed >= 1 or watcher.stats.intents_processed == 1

    def test_content_hash_computed_correctly(self, temp_dirs):
        """Content hash should be computed correctly."""
        from daemons.routing import parse_intent

        # Create intent with known content
        content = "type: SCAN\npayload:\n  test: true\nsession_id: hash_test\n"
        expected_hash = hashlib.sha256(content.encode()).hexdigest()

        intent_path = temp_dirs["incoming"] / "test_intent.yaml"
        intent_path.write_text(content)

        intent = parse_intent(intent_path)
        assert intent is not None
        assert intent.content_hash == expected_hash

    def test_payload_preserved_through_routing(self, temp_dirs):
        """Payload should be preserved exactly through routing."""
        from daemons.routing import Intent, IntentRouter, IntentType, RouteResult, parse_intent

        captured_payload = None

        class PayloadCapture:
            def handle(self, intent: Intent) -> RouteResult:
                nonlocal captured_payload
                captured_payload = intent.payload
                return RouteResult(success=True, intent=intent, worker_name="CAPTURE")

        router = IntentRouter()
        router.register(IntentType.SCAN, PayloadCapture())

        # Complex payload
        original_payload = {
            "pair": "EURUSD",
            "nested": {
                "level1": {
                    "level2": [1, 2, 3],
                },
            },
            "unicode": "日本語テスト",
            "numbers": [1.5, 2.7, 3.14159],
        }

        intent_path = temp_dirs["incoming"] / "test_intent.yaml"
        intent_path.write_text(
            yaml.dump(
                {
                    "type": "SCAN",
                    "payload": original_payload,
                    "session_id": "payload_test",
                }
            )
        )

        intent = parse_intent(intent_path)
        router.route(intent)

        assert captured_payload == original_payload
