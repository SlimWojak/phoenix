#!/usr/bin/env python3
"""
D3 NEGATIVE TEST — THE KILL TEST
=================================

S34: D3 ORIENTATION_BEAD_CHECKSUM

**THIS IS THE KILL TEST FOR D3**

If ANY of these 5 corruption variants pass without triggering STATE_CONFLICT,
D3 has FAILED and orientation is still "vibes", not system-owned.

CORRUPTION VARIANTS:
1. Hash wrong
2. Fields invalid (enum out of range)
3. Stale timestamp (>1 hour old)
4. Mode mismatch (bead says LIVE, system says PAPER)
5. Position count mismatch

CTO EMPHASIS: THIS IS THE KILL TEST
GPT WARNING: "If it fails, abort and log"
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add phoenix root to path
PHOENIX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class D3NegativeTest:
    """
    THE KILL TEST: 5 corruption variants must ALL trigger STATE_CONFLICT.

    If ANY variant passes undetected, D3 has failed.
    """

    def __init__(self):
        self.results = {}
        self.critical_failures = []

    def test_variant_1_hash_wrong(self) -> bool:
        """
        KILL TEST VARIANT 1: Wrong hash.

        Corrupt the bead_hash to not match content.
        MUST trigger: STATE_CONFLICT_HASH
        """
        print("\n[KILL_TEST_V1] Hash corruption...")

        from orientation.generator import OrientationBead
        from orientation.validator import ConflictCode, OrientationValidator

        # Create valid bead
        bead = OrientationBead()
        original_hash = bead.bead_hash

        # CORRUPT: Set wrong hash
        bead.bead_hash = "deadbeef" * 8  # 64 char hex, but wrong

        print(f"  Original hash: {original_hash[:16]}...")
        print(f"  Corrupted hash: {bead.bead_hash[:16]}...")

        # Validate
        validator = OrientationValidator()
        result = validator.validate(bead)

        # MUST detect STATE_CONFLICT_HASH
        detected = ConflictCode.STATE_CONFLICT_HASH in result.conflict_codes

        if detected:
            print("  STATE_CONFLICT_HASH detected: ✓")
        else:
            print("  STATE_CONFLICT_HASH NOT detected: ✗ CRITICAL FAILURE")
            self.critical_failures.append("V1_HASH")

        return detected

    def test_variant_2_invalid_enum(self) -> bool:
        """
        KILL TEST VARIANT 2: Invalid enum value.

        Inject an invalid enum value that doesn't exist in the schema.
        MUST trigger: STATE_CONFLICT_INVALID_ENUM
        """
        print("\n[KILL_TEST_V2] Enum corruption...")

        from orientation.validator import ConflictCode, OrientationValidator

        # Create bead dict with invalid enum
        bead_dict = {
            "bead_id": "test-123",
            "generated_at": datetime.now(UTC).isoformat(),
            "execution_phase": "INVALID_PHASE_XYZ",  # CORRUPT: Invalid enum
            "mode": "PAPER",
            "active_invariants_count": 71,
            "kill_flags_active": 0,
            "unresolved_drift_count": 0,
            "positions_open": 0,
            "heartbeat_status": "HEALTHY",
            "last_human_action_bead_id": None,
            "last_alert_id": None,
            "bead_hash": "0" * 64,
        }

        print("  Corrupted execution_phase: 'INVALID_PHASE_XYZ'")

        # Validate from dict (should fail to parse)
        validator = OrientationValidator()
        result = validator.validate_from_dict(bead_dict)

        # Should fail either with INVALID_ENUM or VALIDATION error
        detected = (
            ConflictCode.STATE_CONFLICT_INVALID_ENUM in result.conflict_codes
            or ConflictCode.STATE_CONFLICT_VALIDATION in result.conflict_codes
            or not result.valid
        )

        if detected:
            print(f"  Corruption detected: ✓ ({result.conflict_codes})")
        else:
            print("  Corruption NOT detected: ✗ CRITICAL FAILURE")
            self.critical_failures.append("V2_ENUM")

        return detected

    def test_variant_3_stale_timestamp(self) -> bool:
        """
        KILL TEST VARIANT 3: Stale timestamp.

        Set timestamp to >1 hour ago.
        MUST trigger: STATE_CONFLICT_STALE
        """
        print("\n[KILL_TEST_V3] Stale timestamp corruption...")

        from orientation.generator import OrientationBead
        from orientation.validator import ConflictCode, OrientationValidator

        # Create bead with stale timestamp
        old_time = datetime.now(UTC) - timedelta(hours=2)
        bead = OrientationBead(generated_at=old_time)
        # Recompute hash to make it internally consistent (but stale)
        bead.bead_hash = bead.compute_hash()

        print(f"  Timestamp: {old_time.isoformat()}")
        print("  Age: ~2 hours (threshold: 1 hour)")

        # Validate
        validator = OrientationValidator()
        result = validator.validate(bead)

        # MUST detect STATE_CONFLICT_STALE
        detected = ConflictCode.STATE_CONFLICT_STALE in result.conflict_codes

        if detected:
            print("  STATE_CONFLICT_STALE detected: ✓")
        else:
            print("  STATE_CONFLICT_STALE NOT detected: ✗ CRITICAL FAILURE")
            self.critical_failures.append("V3_STALE")

        return detected

    def test_variant_4_mode_mismatch(self) -> bool:
        """
        KILL TEST VARIANT 4: Mode mismatch.

        Bead says LIVE_LOCKED, but system (env) says PAPER.
        MUST trigger: STATE_CONFLICT_MODE
        """
        print("\n[KILL_TEST_V4] Mode mismatch corruption...")

        from orientation.generator import ModeEnum, OrientationBead
        from orientation.validator import ConflictCode, OrientationValidator

        # Set system to PAPER
        os.environ["IBKR_MODE"] = "PAPER"

        # Create bead claiming LIVE_LOCKED
        bead = OrientationBead(mode=ModeEnum.LIVE_LOCKED)
        # Recompute hash to make internally consistent (but mismatched)
        bead.bead_hash = bead.compute_hash()

        print("  System mode (env): PAPER")
        print("  Bead claims: LIVE_LOCKED")

        # Validate
        validator = OrientationValidator()
        result = validator.validate(bead)

        # MUST detect STATE_CONFLICT_MODE
        detected = ConflictCode.STATE_CONFLICT_MODE in result.conflict_codes

        if detected:
            print("  STATE_CONFLICT_MODE detected: ✓")
        else:
            print("  STATE_CONFLICT_MODE NOT detected: ✗ CRITICAL FAILURE")
            self.critical_failures.append("V4_MODE")

        return detected

    def test_variant_5_position_mismatch(self) -> bool:
        """
        KILL TEST VARIANT 5: Position count mismatch.

        Bead says 5 positions, tracker says 0.
        MUST trigger: STATE_CONFLICT_POSITIONS
        """
        print("\n[KILL_TEST_V5] Position count mismatch...")

        from orientation.generator import OrientationBead
        from orientation.validator import ConflictCode, OrientationValidator

        # Mock position tracker that returns 0
        class MockPositionTracker:
            def get_open_positions_count(self) -> int:
                return 0

        # Create bead claiming 5 positions
        bead = OrientationBead(positions_open=5)
        # Recompute hash to make internally consistent (but mismatched)
        bead.bead_hash = bead.compute_hash()

        print("  Tracker reports: 0 positions")
        print("  Bead claims: 5 positions")

        # Validate with mock provider
        validator = OrientationValidator(position_provider=MockPositionTracker())
        result = validator.validate(bead)

        # MUST detect STATE_CONFLICT_POSITIONS
        detected = ConflictCode.STATE_CONFLICT_POSITIONS in result.conflict_codes

        if detected:
            print("  STATE_CONFLICT_POSITIONS detected: ✓")
        else:
            print("  STATE_CONFLICT_POSITIONS NOT detected: ✗ CRITICAL FAILURE")
            self.critical_failures.append("V5_POSITIONS")

        return detected

    def run_kill_test(self):
        """
        Run THE KILL TEST.

        ALL 5 variants MUST pass (detect corruption).
        ANY failure = D3 has failed.
        """
        print("=" * 60)
        print("D3 NEGATIVE TEST — THE KILL TEST")
        print("=" * 60)
        print()
        print("CTO EMPHASIS: THIS IS THE KILL TEST")
        print("GPT WARNING: If it fails, abort and log")
        print()
        print("5 CORRUPTION VARIANTS MUST ALL TRIGGER STATE_CONFLICT:")
        print("  V1: Hash wrong")
        print("  V2: Invalid enum")
        print("  V3: Stale timestamp (>1 hour)")
        print("  V4: Mode mismatch")
        print("  V5: Position count mismatch")

        variants = [
            ("V1_HASH_WRONG", self.test_variant_1_hash_wrong),
            ("V2_INVALID_ENUM", self.test_variant_2_invalid_enum),
            ("V3_STALE_TIMESTAMP", self.test_variant_3_stale_timestamp),
            ("V4_MODE_MISMATCH", self.test_variant_4_mode_mismatch),
            ("V5_POSITION_MISMATCH", self.test_variant_5_position_mismatch),
        ]

        for name, test_fn in variants:
            try:
                result = test_fn()
                self.results[name] = result
            except Exception as e:
                print(f"\n[{name}] ERROR: {e}")
                import traceback

                traceback.print_exc()
                self.results[name] = False
                self.critical_failures.append(name)

        # Summary
        print("\n" + "=" * 60)
        print("KILL TEST RESULTS")
        print("=" * 60)

        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)

        for name, result in self.results.items():
            status = "DETECTED ✓" if result else "UNDETECTED ✗"
            print(f"  {name}: {status}")

        print()
        print(f"Corruption Detection Rate: {passed}/{total}")

        if passed == total:
            print()
            print("=" * 60)
            print("THE KILL TEST: PASS ✓")
            print("=" * 60)
            print()
            print("All 5 corruption variants detected.")
            print("Orientation is machine-verifiable, not vibes.")
            print()
            print("D3 EXIT GATE: GREEN")
            return True
        else:
            print()
            print("=" * 60)
            print("THE KILL TEST: FAIL ✗")
            print("=" * 60)
            print()
            print("CRITICAL FAILURES:")
            for failure in self.critical_failures:
                print(f"  - {failure}")
            print()
            print("Orientation is still vibes.")
            print("D3 has FAILED.")
            print()
            print("GPT DIRECTIVE: Abort and log")
            return False


if __name__ == "__main__":
    test = D3NegativeTest()
    success = test.run_kill_test()
    sys.exit(0 if success else 1)
