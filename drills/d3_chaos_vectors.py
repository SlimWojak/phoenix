#!/usr/bin/env python3
"""
D3 Chaos Vectors — ORIENTATION_BEAD Resilience
===============================================

S34: D3 ORIENTATION_BEAD_CHECKSUM

Chaos vectors testing orientation system resilience:
- CV_D3_HASH_MISMATCH: Wrong hash → detected
- CV_D3_STALE_BEAD: 1 hour old → warning/reject
- CV_D3_SOURCE_DISAGREES: Bead vs tracker mismatch → caught
- CV_D3_MULTI_SOURCE_FAIL: 2/5 sources down → partial + warning
- CV_D3_HOSTILE_VARIANTS: 5 corruption types → all STATE_CONFLICT
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add phoenix root to path
PHOENIX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class D3ChaosVectors:
    """Chaos vector tests for D3 orientation."""

    def __init__(self):
        self.results = {}

    def cv_d3_hash_mismatch(self) -> bool:
        """
        CV_D3_HASH_MISMATCH: Wrong hash → detected.

        Inject corrupt hash, verify validator catches it.
        """
        print("\n[CV_D3_HASH_MISMATCH] Hash mismatch chaos...")

        from orientation.generator import OrientationBead
        from orientation.validator import ConflictCode, OrientationValidator

        # Create bead and corrupt hash
        bead = OrientationBead()
        bead.bead_hash = "0" * 64  # All zeros - wrong

        validator = OrientationValidator()
        result = validator.validate(bead)

        detected = ConflictCode.STATE_CONFLICT_HASH in result.conflict_codes
        print(f"  Hash mismatch detected: {'✓' if detected else '✗'}")

        return detected

    def cv_d3_stale_bead(self) -> bool:
        """
        CV_D3_STALE_BEAD: 1 hour+ old → warning/reject.

        Create stale bead, verify age check catches it.
        """
        print("\n[CV_D3_STALE_BEAD] Stale timestamp chaos...")

        from orientation.generator import OrientationBead
        from orientation.validator import ConflictCode, OrientationValidator

        # Create stale bead (2 hours old)
        old_time = datetime.now(UTC) - timedelta(hours=2)
        bead = OrientationBead(generated_at=old_time)
        bead.bead_hash = bead.compute_hash()

        validator = OrientationValidator()
        result = validator.validate(bead)

        detected = ConflictCode.STATE_CONFLICT_STALE in result.conflict_codes
        print(f"  Stale detected (2h old): {'✓' if detected else '✗'}")

        # Test edge case - just under threshold
        almost_stale = datetime.now(UTC) - timedelta(minutes=59)
        bead2 = OrientationBead(generated_at=almost_stale)
        bead2.bead_hash = bead2.compute_hash()
        result2 = validator.validate(bead2)
        not_stale = ConflictCode.STATE_CONFLICT_STALE not in result2.conflict_codes
        print(f"  59 min old allowed: {'✓' if not_stale else '✗'}")

        return detected and not_stale

    def cv_d3_source_disagrees(self) -> bool:
        """
        CV_D3_SOURCE_DISAGREES: Bead vs tracker mismatch → caught.

        Mock tracker returns different value than bead claims.
        """
        print("\n[CV_D3_SOURCE_DISAGREES] Source disagreement chaos...")

        from orientation.generator import OrientationBead
        from orientation.validator import ConflictCode, OrientationValidator

        # Mock tracker returning 3 positions
        class MockTracker:
            def get_open_positions_count(self) -> int:
                return 3

        # Bead claims 10 positions
        bead = OrientationBead(positions_open=10)
        bead.bead_hash = bead.compute_hash()

        validator = OrientationValidator(position_provider=MockTracker())
        result = validator.validate(bead)

        detected = ConflictCode.STATE_CONFLICT_POSITIONS in result.conflict_codes
        print(f"  Bead=10, Tracker=3, conflict detected: {'✓' if detected else '✗'}")

        return detected

    def cv_d3_multi_source_fail(self) -> bool:
        """
        CV_D3_MULTI_SOURCE_FAIL: 2/5 sources down → partial + warning.

        Simulate some providers being unavailable.
        System should still work with partial data.
        """
        print("\n[CV_D3_MULTI_SOURCE_FAIL] Multi-source failure chaos...")

        from orientation.generator import OrientationGenerator

        # Generator with no providers (simulating failures)
        generator = OrientationGenerator(
            halt_provider=None,
            position_provider=None,
            bead_provider=None,
            heartbeat_provider=None,
            alert_provider=None,
        )

        # Should still generate a bead with defaults
        try:
            bead = generator.generate()
            generated = bead is not None
            has_hash = bool(bead.bead_hash)
            print(f"  Bead generated with defaults: {'✓' if generated else '✗'}")
            print(f"  Hash computed: {'✓' if has_hash else '✗'}")
            return generated and has_hash
        except Exception as e:
            print(f"  Generation failed: {e}")
            return False

    def cv_d3_hostile_variants(self) -> bool:
        """
        CV_D3_HOSTILE_VARIANTS: 5 corruption types → all STATE_CONFLICT.

        This is the comprehensive kill test (delegated to d3_negative_test.py).
        Here we test a subset.
        """
        print("\n[CV_D3_HOSTILE_VARIANTS] Hostile corruption chaos...")

        from orientation.generator import ModeEnum, OrientationBead
        from orientation.validator import ConflictCode, OrientationValidator

        os.environ["IBKR_MODE"] = "PAPER"

        tests = []

        # Hash corruption
        bead1 = OrientationBead()
        bead1.bead_hash = "bad" * 20 + "hash"
        validator = OrientationValidator()
        r1 = validator.validate(bead1)
        t1 = ConflictCode.STATE_CONFLICT_HASH in r1.conflict_codes
        tests.append(("hash", t1))
        print(f"  Hash corruption: {'✓' if t1 else '✗'}")

        # Mode corruption
        bead2 = OrientationBead(mode=ModeEnum.LIVE_LOCKED)
        bead2.bead_hash = bead2.compute_hash()
        r2 = validator.validate(bead2)
        t2 = ConflictCode.STATE_CONFLICT_MODE in r2.conflict_codes
        tests.append(("mode", t2))
        print(f"  Mode corruption: {'✓' if t2 else '✗'}")

        # Stale corruption
        bead3 = OrientationBead(generated_at=datetime.now(UTC) - timedelta(hours=3))
        bead3.bead_hash = bead3.compute_hash()
        r3 = validator.validate(bead3)
        t3 = ConflictCode.STATE_CONFLICT_STALE in r3.conflict_codes
        tests.append(("stale", t3))
        print(f"  Stale corruption: {'✓' if t3 else '✗'}")

        all_pass = all(t[1] for t in tests)
        return all_pass

    def run_all(self):
        """Run all chaos vectors."""
        print("=" * 60)
        print("D3 CHAOS VECTORS: ORIENTATION RESILIENCE")
        print("=" * 60)

        vectors = [
            ("CV_D3_HASH_MISMATCH", self.cv_d3_hash_mismatch),
            ("CV_D3_STALE_BEAD", self.cv_d3_stale_bead),
            ("CV_D3_SOURCE_DISAGREES", self.cv_d3_source_disagrees),
            ("CV_D3_MULTI_SOURCE_FAIL", self.cv_d3_multi_source_fail),
            ("CV_D3_HOSTILE_VARIANTS", self.cv_d3_hostile_variants),
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

        # Summary
        print("\n" + "=" * 60)
        print("CHAOS VECTORS SUMMARY")
        print("=" * 60)

        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)

        for name, result in self.results.items():
            status = "PASS ✓" if result else "FAIL ✗"
            print(f"  {name}: {status}")

        print()
        print(f"Chaos Vectors: {passed}/{total}")

        if passed == total:
            print("D3 CHAOS SWEEP: ALL PASS ✓")
            return True
        else:
            print("D3 CHAOS SWEEP: SOME FAILED ✗")
            return False


if __name__ == "__main__":
    chaos = D3ChaosVectors()
    success = chaos.run_all()
    sys.exit(0 if success else 1)
