"""
Test: INV-D1-WATCHER-1 — Every intent processed exactly once
=============================================================

S34: D1 FILE_SEAM_COMPLETION

Verifies:
- Duplicate intents are skipped
- Each unique intent processed exactly once
- Hash-based tracking prevents reprocessing
"""

import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

# MUST be before any phoenix imports
_PHOENIX_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PHOENIX_ROOT))

import pytest
import yaml

# Now import phoenix modules
from daemons.routing import IntentRouter, IntentType, create_stub_handler
from daemons.watcher import IntentWatcher, WatcherConfig


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


@pytest.fixture
def watcher_config(temp_dirs):
    """Create watcher config with temp directories."""
    config = WatcherConfig(
        incoming_dir=temp_dirs["incoming"],
        processed_dir=temp_dirs["processed"],
        unprocessed_dir=temp_dirs["unprocessed"],
        poll_interval_ms=100,
    )
    return config


def create_intent(path: Path, intent_type: str = "SCAN", session_id: str = "test"):
    """Create a test intent file."""
    content = {
        "type": intent_type,
        "payload": {"test": True},
        "timestamp": datetime.now(UTC).isoformat(),
        "session_id": session_id,
    }
    path.write_text(yaml.dump(content))
    return content


class TestExactlyOnceProcessing:
    """INV-D1-WATCHER-1: Every intent processed exactly once."""

    def test_single_intent_processed_once(self, temp_dirs, watcher_config):
        """Single intent should be processed exactly once."""
        # Setup router with stub handler
        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )

        # Track processing
        processed_count = 0

        def on_processed(intent, result):
            nonlocal processed_count
            processed_count += 1

        # Create watcher
        watcher = IntentWatcher(
            router=router,
            config=watcher_config,
            on_intent_processed=on_processed,
        )

        # Create single intent
        intent_path = temp_dirs["incoming"] / "test_intent.yaml"
        create_intent(intent_path)

        # Start watcher
        watcher.start()
        time.sleep(0.3)  # Wait for processing
        watcher.stop()

        # Verify exactly once
        assert processed_count == 1, "Intent should be processed exactly once"
        assert watcher.stats.intents_processed == 1

    def test_duplicate_intent_skipped(self, temp_dirs, watcher_config):
        """Duplicate intent (same content) should be skipped."""
        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )

        processed_intents = []

        def on_processed(intent, result):
            processed_intents.append(intent.content_hash)

        watcher = IntentWatcher(
            router=router,
            config=watcher_config,
            on_intent_processed=on_processed,
        )

        # Create first intent
        content = {
            "type": "SCAN",
            "payload": {"test": True},
            "timestamp": "2026-01-28T10:00:00Z",  # Fixed timestamp
            "session_id": "duplicate_test",
        }
        intent1 = temp_dirs["incoming"] / "intent1.yaml"
        intent1.write_text(yaml.dump(content))

        watcher.start()
        time.sleep(0.3)

        # Create duplicate (same content, different filename)
        intent2 = temp_dirs["incoming"] / "intent2.yaml"
        intent2.write_text(yaml.dump(content))  # Same content!

        time.sleep(0.3)
        watcher.stop()

        # Should process once, skip duplicate
        assert len(processed_intents) == 1, "Duplicate should be skipped"
        assert watcher.stats.duplicates_skipped >= 1

    def test_different_intents_all_processed(self, temp_dirs, watcher_config):
        """Different intents should all be processed."""
        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )
        router.register(
            IntentType.HUNT, create_stub_handler(IntentType.HUNT, temp_dirs["responses"])
        )

        processed_sessions = []

        def on_processed(intent, result):
            processed_sessions.append(intent.session_id)

        watcher = IntentWatcher(
            router=router,
            config=watcher_config,
            on_intent_processed=on_processed,
        )

        watcher.start()

        # Create 5 different intents
        for i in range(5):
            path = temp_dirs["incoming"] / f"intent_{i}.yaml"
            create_intent(path, session_id=f"session_{i}")
            time.sleep(0.15)

        time.sleep(0.3)
        watcher.stop()

        # All should be processed
        assert (
            len(processed_sessions) == 5
        ), f"All 5 intents should be processed, got {len(processed_sessions)}"
        assert watcher.stats.intents_processed == 5

    def test_hash_collision_handling(self, temp_dirs, watcher_config):
        """Hash collision (if any) should not cause issues."""
        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )

        watcher = IntentWatcher(router=router, config=watcher_config)

        # Process first intent
        content1 = yaml.dump(
            {
                "type": "SCAN",
                "payload": {"data": "first"},
                "session_id": "hash_test_1",
            }
        )

        intent1 = temp_dirs["incoming"] / "intent1.yaml"
        intent1.write_text(content1)

        watcher.start()
        time.sleep(0.3)

        # Second intent with different content
        content2 = yaml.dump(
            {
                "type": "SCAN",
                "payload": {"data": "second"},
                "session_id": "hash_test_2",
            }
        )

        intent2 = temp_dirs["incoming"] / "intent2.yaml"
        intent2.write_text(content2)

        time.sleep(0.3)
        watcher.stop()

        # Both should be processed (different hashes)
        assert watcher.stats.intents_processed == 2


class TestHashTracking:
    """Test hash-based duplicate detection."""

    def test_cleanup_old_hashes(self, temp_dirs, watcher_config):
        """Old hashes should be cleaned up."""
        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )

        watcher = IntentWatcher(router=router, config=watcher_config)

        # Add some hashes manually
        from datetime import timedelta

        old_time = datetime.now(UTC) - timedelta(hours=25)

        watcher._processed_hashes["old_hash_1"] = old_time
        watcher._processed_hashes["old_hash_2"] = old_time
        watcher._processed_hashes["recent_hash"] = datetime.now(UTC)

        # Cleanup
        removed = watcher.cleanup_old_hashes(max_age_hours=24)

        assert removed == 2
        assert "old_hash_1" not in watcher._processed_hashes
        assert "recent_hash" in watcher._processed_hashes
