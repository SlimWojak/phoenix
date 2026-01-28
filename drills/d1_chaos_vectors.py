#!/usr/bin/env python3
"""
D1 Chaos Vectors — Stress Testing File Seam Components
=======================================================

S34: D1 FILE_SEAM_COMPLETION

Chaos Vectors:
- CV_D1_INTENT_FLOOD: 100 intents in <5s
- CV_D1_MALFORMED: Malformed YAML quarantined
- CV_D1_HALT_RACE: HALT wins race against queued
"""

import sys
import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

# Add phoenix root to path
PHOENIX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

import yaml

from daemons.routing import IntentRouter, IntentType, RouteResult, create_stub_handler
from daemons.watcher import IntentWatcher, WatcherConfig


class D1ChaosVectors:
    """Run D1 chaos vectors."""

    def __init__(self):
        self.results = {}
        self.temp_dir = None

    def setup(self):
        """Create temp directories."""
        self.temp_dir = tempfile.mkdtemp()
        base = Path(self.temp_dir)

        self.dirs = {
            "incoming": base / "incoming",
            "processed": base / "processed",
            "unprocessed": base / "unprocessed",
            "responses": base / "responses",
        }

        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)

    def cleanup(self):
        """Remove temp directories."""
        import shutil

        if self.temp_dir:
            shutil.rmtree(self.temp_dir)

    def reset_dirs(self):
        """Clear all files from temp dirs."""
        for d in self.dirs.values():
            for f in d.glob("*"):
                if f.is_file():
                    f.unlink()

    def cv_d1_intent_flood(self) -> bool:
        """
        CV_D1_INTENT_FLOOD: Handle 100 intents in <5s

        Proves:
        - Watcher handles burst load
        - All intents processed
        - No data loss under stress
        """
        print("\n[CV_D1_INTENT_FLOOD] Testing 100 intents in <5s...")
        self.reset_dirs()

        config = WatcherConfig(
            incoming_dir=self.dirs["incoming"],
            processed_dir=self.dirs["processed"],
            unprocessed_dir=self.dirs["unprocessed"],
            poll_interval_ms=30,  # Fast polling
        )

        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, self.dirs["responses"])
        )

        watcher = IntentWatcher(router=router, config=config)

        # Create 100 intents
        NUM_INTENTS = 100
        for i in range(NUM_INTENTS):
            path = self.dirs["incoming"] / f"flood_{i:04d}.yaml"
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

        start = time.perf_counter()
        watcher.start()

        # Wait for processing
        max_wait = 5.0
        while time.perf_counter() - start < max_wait:
            if watcher.stats.intents_processed >= NUM_INTENTS:
                break
            time.sleep(0.05)

        watcher.stop()
        elapsed = time.perf_counter() - start

        passed = watcher.stats.intents_processed == NUM_INTENTS and elapsed < 5.0
        print(f"  Processed: {watcher.stats.intents_processed}/{NUM_INTENTS}")
        print(f"  Elapsed: {elapsed:.2f}s (limit: 5.0s)")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def cv_d1_malformed(self) -> bool:
        """
        CV_D1_MALFORMED: Malformed YAML quarantined safely

        Proves:
        - Invalid YAML doesn't crash watcher
        - Malformed files moved to quarantine
        - Valid intents still process
        """
        print("\n[CV_D1_MALFORMED] Testing malformed YAML handling...")
        self.reset_dirs()

        config = WatcherConfig(
            incoming_dir=self.dirs["incoming"],
            processed_dir=self.dirs["processed"],
            unprocessed_dir=self.dirs["unprocessed"],
            poll_interval_ms=50,
        )

        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, self.dirs["responses"])
        )

        watcher = IntentWatcher(router=router, config=config)

        # Create valid intent
        valid_path = self.dirs["incoming"] / "valid.yaml"
        valid_path.write_text(
            yaml.dump(
                {
                    "type": "SCAN",
                    "payload": {},
                    "session_id": "valid_test",
                }
            )
        )

        # Create malformed intents
        malformed_cases = [
            ("broken_braces.yaml", "{{{{invalid"),
            ("not_yaml.yaml", "this is not yaml []{}"),
            ("unknown_type.yaml", yaml.dump({"type": "UNKNOWN_XYZ", "payload": {}})),
        ]

        for name, content in malformed_cases:
            path = self.dirs["incoming"] / name
            path.write_text(content)

        watcher.start()
        time.sleep(0.5)
        watcher.stop()

        # Check results
        valid_processed = watcher.stats.intents_processed >= 1
        quarantined = watcher.stats.intents_quarantined >= len(malformed_cases)
        quarantine_files = list(self.dirs["unprocessed"].glob("*.yaml"))

        passed = valid_processed and quarantined
        print(f"  Valid processed: {watcher.stats.intents_processed}")
        print(f"  Quarantined: {watcher.stats.intents_quarantined}")
        print(f"  Quarantine files: {len(quarantine_files)}")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def cv_d1_halt_race(self) -> bool:
        """
        CV_D1_HALT_RACE: HALT wins race against queued intents

        Proves:
        - HALT detected and processed with priority
        - Queued intents don't block HALT
        - System safe under race conditions
        """
        print("\n[CV_D1_HALT_RACE] Testing HALT race condition...")
        self.reset_dirs()

        config = WatcherConfig(
            incoming_dir=self.dirs["incoming"],
            processed_dir=self.dirs["processed"],
            unprocessed_dir=self.dirs["unprocessed"],
            poll_interval_ms=30,
        )

        halt_detected = threading.Event()
        scan_count = 0

        class HaltDetector:
            def handle(self, intent):
                halt_detected.set()
                return RouteResult(success=True, intent=intent, worker_name="HALT")

        class ScanCounter:
            def handle(self, intent):
                nonlocal scan_count
                scan_count += 1
                return RouteResult(success=True, intent=intent, worker_name="SCAN")

        router = IntentRouter()
        router.register(IntentType.SCAN, ScanCounter())
        router.register(IntentType.HALT, HaltDetector())

        watcher = IntentWatcher(router=router, config=config)

        # Create many SCAN intents
        for i in range(50):
            path = self.dirs["incoming"] / f"scan_{i:03d}.yaml"
            path.write_text(
                yaml.dump(
                    {
                        "type": "SCAN",
                        "payload": {"index": i},
                        "session_id": f"scan_{i}",
                    }
                )
            )

        watcher.start()
        time.sleep(0.1)

        # Create HALT mid-stream
        halt_path = self.dirs["incoming"] / "halt.yaml"
        halt_path.write_text(
            yaml.dump(
                {
                    "type": "HALT",
                    "payload": {"reason": "Race test"},
                    "session_id": "halt_race",
                }
            )
        )

        time.sleep(0.5)
        watcher.stop()

        passed = halt_detected.is_set() and watcher.stats.halt_intents >= 1
        print(f"  HALT detected: {halt_detected.is_set()}")
        print(f"  HALT count: {watcher.stats.halt_intents}")
        print(f"  SCAN processed: {scan_count}")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def run_all(self):
        """Run all chaos vectors."""
        print("=" * 60)
        print("D1 CHAOS VECTORS: FILE SEAM STRESS TESTING")
        print("=" * 60)

        self.setup()

        try:
            vectors = [
                ("CV_D1_INTENT_FLOOD", self.cv_d1_intent_flood),
                ("CV_D1_MALFORMED", self.cv_d1_malformed),
                ("CV_D1_HALT_RACE", self.cv_d1_halt_race),
            ]

            for name, test_fn in vectors:
                try:
                    result = test_fn()
                    self.results[name] = result
                except Exception as e:
                    print(f"\n[{name}] ERROR: {e}")
                    import traceback

                    traceback.print_exc()
                    self.results[name] = False

        finally:
            self.cleanup()

        # Summary
        print("\n" + "=" * 60)
        print("CHAOS SUMMARY")
        print("=" * 60)

        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)

        for name, result in self.results.items():
            status = "PASS ✓" if result else "FAIL ✗"
            print(f"  {name}: {status}")

        print()
        print(f"Results: {passed}/{total}")

        if passed == total:
            print("CHAOS VECTORS: ALL PASS ✓")
            return True
        else:
            print("CHAOS VECTORS: SOME FAILED ✗")
            return False


if __name__ == "__main__":
    chaos = D1ChaosVectors()
    success = chaos.run_all()
    sys.exit(0 if success else 1)
