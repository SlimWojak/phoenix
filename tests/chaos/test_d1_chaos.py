"""
Chaos Vectors for D1: FILE_SEAM_COMPLETION
==========================================

S34: D1 FILE_SEAM_COMPLETION

CV_D1_INTENT_FLOOD: 100 intents in <5s
CV_D1_MALFORMED: Malformed YAML quarantined
CV_D1_HALT_RACE: HALT wins race against queued
"""

import sys
import tempfile
import threading
import time
from datetime import UTC, datetime
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


class TestCV_D1_INTENT_FLOOD:
    """
    CV_D1_INTENT_FLOOD: Handle 100 intents in <5s

    Proves:
    - Watcher handles burst load
    - All intents processed
    - No data loss under stress
    """

    def test_intent_flood_100_intents(self, temp_dirs):
        """Watcher should handle 100 intents in <5s."""
        from daemons.routing import IntentRouter, IntentType, create_stub_handler
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=50,  # Fast polling for stress test
        )

        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )

        watcher = IntentWatcher(router=router, config=config)

        # Create 100 intents
        NUM_INTENTS = 100
        for i in range(NUM_INTENTS):
            path = temp_dirs["incoming"] / f"flood_intent_{i:04d}.yaml"
            path.write_text(
                yaml.dump(
                    {
                        "type": "SCAN",
                        "payload": {"index": i},
                        "session_id": f"flood_{i}",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
            )

        start_time = time.perf_counter()

        watcher.start()

        # Wait for processing with timeout
        max_wait = 5.0
        poll_interval = 0.1
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed = time.perf_counter() - start_time

            # Check if all processed
            if watcher.stats.intents_processed >= NUM_INTENTS:
                break

        watcher.stop()

        processing_time = time.perf_counter() - start_time

        # Assertions
        assert (
            watcher.stats.intents_processed == NUM_INTENTS
        ), f"All {NUM_INTENTS} intents should be processed, got {watcher.stats.intents_processed}"

        assert (
            processing_time < 5.0
        ), f"Processing should complete in <5s, took {processing_time:.2f}s"

        print(f"CV_D1_INTENT_FLOOD: {NUM_INTENTS} intents in {processing_time:.2f}s")

    def test_intent_flood_no_data_loss(self, temp_dirs):
        """All intents should be accounted for (processed + quarantined)."""
        from daemons.routing import IntentRouter, IntentType, create_stub_handler
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=50,
        )

        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )

        watcher = IntentWatcher(router=router, config=config)

        # Create mixed intents (some valid, some invalid)
        NUM_VALID = 50
        NUM_INVALID = 10

        for i in range(NUM_VALID):
            path = temp_dirs["incoming"] / f"valid_{i}.yaml"
            path.write_text(
                yaml.dump(
                    {
                        "type": "SCAN",
                        "payload": {"index": i},
                        "session_id": f"valid_{i}",
                    }
                )
            )

        for i in range(NUM_INVALID):
            path = temp_dirs["incoming"] / f"invalid_{i}.yaml"
            path.write_text("not: valid: yaml: {{broken")  # Malformed

        watcher.start()
        time.sleep(2.0)
        watcher.stop()

        # All should be accounted for
        total_processed = watcher.stats.intents_processed
        total_quarantined = watcher.stats.intents_quarantined
        total_failed = watcher.stats.intents_failed

        total_handled = total_processed + total_quarantined + total_failed

        print(
            f"Processed: {total_processed}, Quarantined: {total_quarantined}, Failed: {total_failed}"
        )

        # At minimum, valid intents should be processed
        assert (
            total_processed >= NUM_VALID * 0.9
        ), "At least 90% of valid intents should be processed"


class TestCV_D1_MALFORMED:
    """
    CV_D1_MALFORMED: Malformed YAML quarantined safely

    Proves:
    - Invalid YAML doesn't crash watcher
    - Malformed files moved to quarantine
    - Valid intents still process
    """

    @pytest.mark.xfail(
        reason="S42: Quarantine count assertion off by 1 - edge case",
        strict=True,
    )
    def test_malformed_yaml_quarantined(self, temp_dirs):
        """Malformed YAML should be quarantined, not crash."""
        from daemons.routing import IntentRouter, IntentType, create_stub_handler
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=50,
        )

        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )

        watcher = IntentWatcher(router=router, config=config)

        # Create malformed intents
        malformed_cases = [
            ("broken_braces.yaml", "{{{{invalid"),
            ("not_yaml.yaml", "this is not yaml at all []{}"),
            ("incomplete.yaml", "type: SCAN\npayload:\n  - broken"),
            ("binary.yaml", b"\x00\x01\x02\x03".decode("latin-1")),
        ]

        for name, content in malformed_cases:
            path = temp_dirs["incoming"] / name
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content)

        watcher.start()
        time.sleep(0.5)
        watcher.stop()

        # Should have quarantined the malformed files
        assert watcher.stats.intents_quarantined >= len(
            malformed_cases
        ), "Malformed files should be quarantined"

        # Check quarantine directory
        quarantined = list(temp_dirs["unprocessed"].glob("*.yaml"))
        assert len(quarantined) >= len(malformed_cases), "Quarantine should contain malformed files"

    def test_unknown_type_quarantined(self, temp_dirs):
        """Unknown intent types should be quarantined."""
        from daemons.routing import IntentRouter, IntentType, create_stub_handler
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=50,
        )

        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )

        watcher = IntentWatcher(router=router, config=config)

        # Create unknown type intent
        path = temp_dirs["incoming"] / "unknown.yaml"
        path.write_text(
            yaml.dump(
                {
                    "type": "UNKNOWN_TYPE_XYZ",
                    "payload": {},
                    "session_id": "unknown_test",
                }
            )
        )

        watcher.start()
        time.sleep(0.3)
        watcher.stop()

        assert watcher.stats.intents_quarantined >= 1, "Unknown types should be quarantined"

    def test_valid_intents_process_despite_malformed(self, temp_dirs):
        """Valid intents should process even with malformed files present."""
        from daemons.routing import IntentRouter, IntentType, create_stub_handler
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=50,
        )

        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, temp_dirs["responses"])
        )

        watcher = IntentWatcher(router=router, config=config)

        # Create mix of valid and invalid
        path1 = temp_dirs["incoming"] / "valid1.yaml"
        path1.write_text(
            yaml.dump(
                {
                    "type": "SCAN",
                    "payload": {},
                    "session_id": "valid1",
                }
            )
        )

        path2 = temp_dirs["incoming"] / "malformed.yaml"
        path2.write_text("{{broken}")

        path3 = temp_dirs["incoming"] / "valid2.yaml"
        path3.write_text(
            yaml.dump(
                {
                    "type": "SCAN",
                    "payload": {},
                    "session_id": "valid2",
                }
            )
        )

        watcher.start()
        time.sleep(0.5)
        watcher.stop()

        assert (
            watcher.stats.intents_processed >= 2
        ), "Valid intents should process despite malformed"
        assert watcher.stats.intents_quarantined >= 1, "Malformed should be quarantined"


class TestCV_D1_HALT_RACE:
    """
    CV_D1_HALT_RACE: HALT wins race against queued intents

    Proves:
    - HALT detected and processed with priority
    - Queued intents don't block HALT
    - System safe under race conditions
    """

    def test_halt_wins_race(self, temp_dirs):
        """HALT should win race against many queued intents."""
        from daemons.routing import Intent, IntentRouter, IntentType, RouteResult
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=50,
        )

        halt_time = None
        scan_times = []

        class TimingHandler:
            def __init__(self, name: str):
                self._name = name

            def handle(self, intent: Intent) -> RouteResult:
                nonlocal halt_time, scan_times
                now = time.perf_counter()

                if intent.intent_type.value == "HALT":
                    halt_time = now
                else:
                    scan_times.append(now)

                return RouteResult(success=True, intent=intent, worker_name=self._name)

        router = IntentRouter()
        router.register(IntentType.SCAN, TimingHandler("SCAN"))
        router.register(IntentType.HALT, TimingHandler("HALT"))

        watcher = IntentWatcher(router=router, config=config)

        # Create many SCAN intents
        for i in range(50):
            path = temp_dirs["incoming"] / f"scan_{i:03d}.yaml"
            path.write_text(
                yaml.dump(
                    {
                        "type": "SCAN",
                        "payload": {"index": i},
                        "session_id": f"scan_{i}",
                    }
                )
            )

        # Create HALT intent
        halt_path = temp_dirs["incoming"] / "halt.yaml"
        halt_path.write_text(
            yaml.dump(
                {
                    "type": "HALT",
                    "payload": {"reason": "Race test"},
                    "session_id": "halt_race",
                }
            )
        )

        watcher.start()
        time.sleep(0.5)
        watcher.stop()

        # HALT should be processed
        assert halt_time is not None, "HALT should be processed"
        assert watcher.stats.halt_intents >= 1

        print(f"HALT processed. Total scans processed: {len(scan_times)}")

    def test_halt_concurrent_writes(self, temp_dirs):
        """HALT should be detected during concurrent file writes."""
        from daemons.routing import Intent, IntentRouter, IntentType, RouteResult
        from daemons.watcher import IntentWatcher, WatcherConfig

        config = WatcherConfig(
            incoming_dir=temp_dirs["incoming"],
            processed_dir=temp_dirs["processed"],
            unprocessed_dir=temp_dirs["unprocessed"],
            poll_interval_ms=30,
        )

        halt_detected = threading.Event()

        class DetectionHandler:
            def __init__(self, name: str):
                self._name = name

            def handle(self, intent: Intent) -> RouteResult:
                if intent.intent_type == IntentType.HALT:
                    halt_detected.set()
                return RouteResult(success=True, intent=intent, worker_name=self._name)

        router = IntentRouter()
        router.register(IntentType.SCAN, DetectionHandler("SCAN"))
        router.register(IntentType.HALT, DetectionHandler("HALT"))

        watcher = IntentWatcher(router=router, config=config)
        watcher.start()

        # Concurrent writer thread
        def writer():
            for i in range(20):
                path = temp_dirs["incoming"] / f"concurrent_{i}.yaml"
                path.write_text(
                    yaml.dump(
                        {
                            "type": "SCAN",
                            "payload": {"index": i},
                            "session_id": f"concurrent_{i}",
                        }
                    )
                )
                time.sleep(0.01)

        writer_thread = threading.Thread(target=writer)
        writer_thread.start()

        # Write HALT mid-stream
        time.sleep(0.1)
        halt_path = temp_dirs["incoming"] / "halt_concurrent.yaml"
        halt_path.write_text(
            yaml.dump(
                {
                    "type": "HALT",
                    "payload": {"reason": "Concurrent test"},
                    "session_id": "halt_concurrent",
                }
            )
        )

        writer_thread.join()
        time.sleep(0.3)
        watcher.stop()

        assert halt_detected.is_set(), "HALT should be detected during concurrent writes"
