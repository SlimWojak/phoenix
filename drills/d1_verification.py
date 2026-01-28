#!/usr/bin/env python3
"""
D1 Verification Script — File Seam Components
==============================================

S34: D1 FILE_SEAM_COMPLETION

Verifies all D1 invariants:
- INV-D1-WATCHER-1: Every intent processed exactly once
- INV-D1-WATCHER-IMMUTABLE-1: Watcher may not modify intent payloads
- INV-D1-LENS-1: Response injection adds ≤50 tokens to context
- INV-D1-HALT-PRIORITY-1: HALT bypasses queue, processes immediately
"""

import hashlib
import json
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

# Add phoenix root to path
PHOENIX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

import yaml

from daemons.lens import LensConfig, ResponseLens
from daemons.routing import IntentRouter, IntentType, create_stub_handler, parse_intent
from daemons.watcher import IntentWatcher, WatcherConfig


def estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token)."""
    return len(text) // 4


class D1Verification:
    """Run all D1 invariant tests."""

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
            "state": base / "state",
        }

        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)

    def cleanup(self):
        """Remove temp directories."""
        import shutil

        if self.temp_dir:
            shutil.rmtree(self.temp_dir)

    def test_inv_d1_watcher_1_exactly_once(self) -> bool:
        """INV-D1-WATCHER-1: Every intent processed exactly once."""
        print("\n[INV-D1-WATCHER-1] Testing exactly-once processing...")

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

        processed_count = 0

        def on_processed(intent, result):
            nonlocal processed_count
            processed_count += 1

        watcher = IntentWatcher(router=router, config=config, on_intent_processed=on_processed)

        # Create 5 unique intents
        for i in range(5):
            path = self.dirs["incoming"] / f"intent_{i}.yaml"
            path.write_text(
                yaml.dump(
                    {
                        "type": "SCAN",
                        "payload": {"index": i},
                        "session_id": f"session_{i}",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
            )

        watcher.start()
        time.sleep(0.5)
        watcher.stop()

        passed = processed_count == 5 and watcher.stats.intents_processed == 5
        print(f"  Processed: {processed_count}/5, Stats: {watcher.stats.intents_processed}/5")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_inv_d1_watcher_1_duplicate_skipped(self) -> bool:
        """INV-D1-WATCHER-1: Duplicates skipped."""
        print("\n[INV-D1-WATCHER-1] Testing duplicate detection...")

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

        # Create same content twice
        content = yaml.dump(
            {
                "type": "SCAN",
                "payload": {"test": True},
                "session_id": "duplicate_test",
                "timestamp": "2026-01-28T10:00:00Z",
            }
        )

        path1 = self.dirs["incoming"] / "intent1.yaml"
        path1.write_text(content)

        watcher.start()
        time.sleep(0.2)

        path2 = self.dirs["incoming"] / "intent2.yaml"
        path2.write_text(content)  # Same content!

        time.sleep(0.2)
        watcher.stop()

        passed = watcher.stats.intents_processed == 1 and watcher.stats.duplicates_skipped >= 1
        print(
            f"  Processed: {watcher.stats.intents_processed}, Duplicates skipped: {watcher.stats.duplicates_skipped}"
        )
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_inv_d1_watcher_immutable_1(self) -> bool:
        """INV-D1-WATCHER-IMMUTABLE-1: No payload modification."""
        print("\n[INV-D1-WATCHER-IMMUTABLE-1] Testing immutability...")

        content = yaml.dump(
            {
                "type": "SCAN",
                "payload": {"data": "test", "nested": {"value": 123}},
                "session_id": "immutable_test",
            }
        )

        path = self.dirs["incoming"] / "immutable_test.yaml"
        path.write_text(content)
        original_hash = hashlib.sha256(content.encode()).hexdigest()

        intent = parse_intent(path)
        passed = intent is not None and intent.content_hash == original_hash

        # Verify verification works
        if intent:
            verified = intent.verify_immutable(content)
            passed = passed and verified

            # Modified content should fail verification
            modified = content + "\n# comment"
            modified_check = not intent.verify_immutable(modified)
            passed = passed and modified_check

        print(f"  Hash match: {intent is not None and intent.content_hash == original_hash}")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_inv_d1_lens_1_context_cost(self) -> bool:
        """INV-D1-LENS-1: ≤50 tokens context cost."""
        print("\n[INV-D1-LENS-1] Testing context cost...")

        lens_config = LensConfig(
            responses_dir=self.dirs["responses"],
            state_dir=self.dirs["state"],
        )

        lens = ResponseLens(config=lens_config)

        # Create test response
        response_path = self.dirs["responses"] / "test_response.md"
        response_path.write_text(
            """---
type: cso_briefing
generated: 2026-01-28T10:00:00Z
expires: 2026-01-28T10:30:00Z
---
# Test Response
Content here...
"""
        )

        lens._on_new_response(response_path)

        # Check flag file tokens
        flag_content = lens.flag_path.read_text()
        flag_tokens = estimate_tokens(flag_content)

        # Check metadata tokens
        metadata = lens.get_latest_response()
        meta_tokens = estimate_tokens(json.dumps(metadata)) if metadata else 0

        passed = flag_tokens <= 50 and meta_tokens <= 50
        print(f"  Flag tokens: {flag_tokens} (limit: 50)")
        print(f"  Metadata tokens: {meta_tokens} (limit: 50)")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_inv_d1_halt_priority_1(self) -> bool:
        """INV-D1-HALT-PRIORITY-1: HALT bypasses queue."""
        print("\n[INV-D1-HALT-PRIORITY-1] Testing HALT priority...")

        config = WatcherConfig(
            incoming_dir=self.dirs["incoming"],
            processed_dir=self.dirs["processed"],
            unprocessed_dir=self.dirs["unprocessed"],
            poll_interval_ms=50,
        )

        halt_detected = False

        class HaltDetector:
            def handle(self, intent):
                nonlocal halt_detected
                halt_detected = True
                from daemons.routing import RouteResult

                return RouteResult(success=True, intent=intent, worker_name="HALT")

        router = IntentRouter()
        router.register(
            IntentType.SCAN, create_stub_handler(IntentType.SCAN, self.dirs["responses"])
        )
        router.register(IntentType.HALT, HaltDetector())

        watcher = IntentWatcher(router=router, config=config)

        # Verify is_priority
        is_priority = router.is_priority(IntentType.HALT)

        # Create HALT intent
        halt_path = self.dirs["incoming"] / "halt.yaml"
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

        passed = is_priority and halt_detected and watcher.stats.halt_intents >= 1
        print(f"  is_priority(HALT): {is_priority}")
        print(f"  HALT detected: {halt_detected}")
        print(f"  HALT count: {watcher.stats.halt_intents}")
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def run_all(self):
        """Run all verification tests."""
        print("=" * 60)
        print("D1 VERIFICATION: FILE SEAM COMPONENTS")
        print("=" * 60)

        self.setup()

        try:
            tests = [
                ("INV-D1-WATCHER-1 (exactly once)", self.test_inv_d1_watcher_1_exactly_once),
                ("INV-D1-WATCHER-1 (duplicate)", self.test_inv_d1_watcher_1_duplicate_skipped),
                ("INV-D1-WATCHER-IMMUTABLE-1", self.test_inv_d1_watcher_immutable_1),
                ("INV-D1-LENS-1 (context cost)", self.test_inv_d1_lens_1_context_cost),
                ("INV-D1-HALT-PRIORITY-1", self.test_inv_d1_halt_priority_1),
            ]

            for name, test_fn in tests:
                try:
                    # Fresh temp dir for each test
                    for d in self.dirs.values():
                        for f in d.glob("*"):
                            if f.is_file():
                                f.unlink()

                    result = test_fn()
                    self.results[name] = result
                except Exception as e:
                    print(f"\n[{name}] ERROR: {e}")
                    self.results[name] = False

        finally:
            self.cleanup()

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)

        for name, result in self.results.items():
            status = "PASS ✓" if result else "FAIL ✗"
            print(f"  {name}: {status}")

        print()
        print(f"Results: {passed}/{total}")

        if passed == total:
            print("D1 VERIFICATION: ALL PASS ✓")
            return True
        else:
            print("D1 VERIFICATION: SOME FAILED ✗")
            return False


if __name__ == "__main__":
    verifier = D1Verification()
    success = verifier.run_all()
    sys.exit(0 if success else 1)
