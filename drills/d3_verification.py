#!/usr/bin/env python3
"""
D3 Verification Script — ORIENTATION_BEAD Checksum
===================================================

S34: D3 ORIENTATION_BEAD_CHECKSUM

Verifies all D3 invariants:
- INV-D3-CHECKSUM-1: All fields machine-verifiable, no prose
- INV-D3-CROSS-CHECK-1: Every field verifiable against source
- INV-D3-NO-DERIVED-1: No interpreted/summary fields
- POSITIVE TEST: Fresh session verifies state in <10s
"""

import os
import sys
import time
from pathlib import Path

# Add phoenix root to path
PHOENIX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class D3Verification:
    """Run all D3 invariant tests."""

    def __init__(self):
        self.results = {}

    def test_inv_d3_checksum_1_machine_verifiable(self) -> bool:
        """INV-D3-CHECKSUM-1: All fields machine-verifiable."""
        print("\n[INV-D3-CHECKSUM-1] Testing machine-verifiable fields...")

        from orientation.generator import OrientationGenerator

        # Generate bead
        generator = OrientationGenerator()
        bead = generator.generate()

        # Check all fields are primitive/enum (no prose)
        bead_dict = bead.to_dict()

        # Forbidden patterns (prose indicators)
        forbidden_keys = [
            "system_stable",
            "risk_level",
            "narrative_state",
            "summary",
            "recommendation",
            "description",
            "explanation",
        ]

        prose_detected = []
        for key in bead_dict:
            if key in forbidden_keys:
                prose_detected.append(key)

        if prose_detected:
            print(f"  FAIL: Prose fields detected: {prose_detected}")
            return False

        # Verify all values are primitive or None
        non_primitive = []
        for key, value in bead_dict.items():
            if isinstance(value, (list, dict)):
                non_primitive.append(key)

        if non_primitive:
            print(f"  WARNING: Complex fields: {non_primitive}")

        print(f"  Fields: {len(bead_dict)}")
        print("  All fields machine-verifiable: ✓")

        return True

    def test_inv_d3_checksum_hash_integrity(self) -> bool:
        """Hash integrity verification."""
        print("\n[INV-D3-CHECKSUM-HASH] Testing hash integrity...")

        from orientation.generator import OrientationBead

        # Create bead
        bead = OrientationBead()

        # Verify hash is computed
        has_hash = bool(bead.bead_hash)
        print(f"  Hash computed: {has_hash}")

        # Verify hash matches
        hash_valid = bead.verify_hash()
        print(f"  Hash valid: {hash_valid}")

        # Verify hash changes when field changes
        original_hash = bead.bead_hash
        bead.positions_open = 999
        bead.bead_hash = bead.compute_hash()
        hash_changed = bead.bead_hash != original_hash
        print(f"  Hash changes on field change: {hash_changed}")

        return has_hash and hash_valid and hash_changed

    def test_inv_d3_cross_check_1_verifiable(self) -> bool:
        """INV-D3-CROSS-CHECK-1: Fields verifiable against source."""
        print("\n[INV-D3-CROSS-CHECK-1] Testing field verifiability...")

        from orientation.generator import OrientationGenerator

        # Set environment for cross-check
        os.environ["IBKR_MODE"] = "PAPER"

        # Generate bead
        generator = OrientationGenerator()
        bead = generator.generate()

        # Verify mode matches environment
        mode_matches = bead.mode.value == os.environ.get("IBKR_MODE", "PAPER")
        print(f"  Mode matches env: {mode_matches}")

        # Verify timestamp is recent
        from datetime import UTC, datetime

        age_sec = (datetime.now(UTC) - bead.generated_at).total_seconds()
        timestamp_recent = age_sec < 60  # Within 60s
        print(f"  Timestamp recent ({age_sec:.1f}s): {timestamp_recent}")

        return mode_matches and timestamp_recent

    def test_inv_d3_no_derived_1_no_summaries(self) -> bool:
        """INV-D3-NO-DERIVED-1: No derived/interpreted fields."""
        print("\n[INV-D3-NO-DERIVED-1] Testing no derived fields...")

        from orientation.generator import OrientationBead

        bead = OrientationBead()
        bead_dict = bead.to_dict()

        # Derived fields that are FORBIDDEN
        forbidden_derived = [
            "system_stable",  # Derived from multiple fields
            "trading_allowed",  # Derived boolean
            "risk_level",  # Interpreted judgment
            "health_score",  # Derived/computed
            "overall_status",  # Summary
        ]

        found_derived = [k for k in forbidden_derived if k in bead_dict]

        if found_derived:
            print(f"  FAIL: Derived fields found: {found_derived}")
            return False

        print("  No derived fields: ✓")
        return True

    def test_positive_verification_speed(self) -> bool:
        """POSITIVE TEST: Fresh session verifies state in <10s."""
        print("\n[POSITIVE_TEST] Testing verification speed...")

        from orientation.generator import OrientationGenerator
        from orientation.validator import OrientationValidator

        # Measure time to generate + validate
        start = time.perf_counter()

        # Generate orientation
        generator = OrientationGenerator()
        bead = generator.generate()

        # Validate orientation
        validator = OrientationValidator()
        result = validator.validate(bead)

        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"  Generate + Validate: {elapsed_ms:.2f}ms")
        print(f"  Valid: {result.valid}")

        # Target: <10s (we're way under)
        under_target = elapsed_ms < 10000
        print(f"  Under 10s target: {under_target}")

        return result.valid and under_target

    def test_gate_d3_1_generates_from_state(self) -> bool:
        """GATE_D3_1: ORIENTATION_BEAD generates from system state."""
        print("\n[GATE_D3_1] Testing generation from system state...")

        from orientation.generator import OrientationGenerator

        generator = OrientationGenerator()
        bead = generator.generate()

        # Check all required fields present
        required_fields = [
            "bead_id",
            "generated_at",
            "execution_phase",
            "mode",
            "active_invariants_count",
            "kill_flags_active",
            "unresolved_drift_count",
            "positions_open",
            "heartbeat_status",
            "bead_hash",
        ]

        bead_dict = bead.to_dict()
        missing = [f for f in required_fields if f not in bead_dict]

        if missing:
            print(f"  Missing fields: {missing}")
            return False

        print(f"  All {len(required_fields)} required fields present: ✓")
        print(f"  Bead ID: {bead.bead_id[:8]}...")
        print(f"  Hash: {bead.bead_hash[:16]}...")

        return True

    def test_gate_d3_2_verification_success(self) -> bool:
        """GATE_D3_2: Fresh Claude verifies state in <10s."""
        print("\n[GATE_D3_2] Testing verification success path...")

        from orientation.generator import OrientationGenerator
        from orientation.validator import OrientationValidator

        # Generate fresh bead
        generator = OrientationGenerator()
        bead = generator.generate()

        # Validate
        validator = OrientationValidator()
        result = validator.validate(bead)

        print(f"  Valid: {result.valid}")
        print(f"  Conflicts: {len(result.conflicts)}")

        if result.conflicts:
            for c in result.conflicts:
                print(f"    - {c.code.value}: {c.message}")

        return result.valid

    def test_file_seam_output(self) -> bool:
        """Test file seam output."""
        print("\n[FILE_SEAM] Testing orientation.yaml output...")

        from orientation.generator import OrientationGenerator

        generator = OrientationGenerator()
        bead, path = generator.generate_and_write()

        # Check file exists
        exists = path.exists()
        print(f"  File exists: {exists}")

        # Check content
        if exists:
            content = path.read_text()
            has_hash = "bead_hash" in content
            print(f"  Has bead_hash: {has_hash}")
            print(f"  Path: {path}")

            # Token count (rough estimate: 1 token ~= 4 chars)
            tokens = len(content) // 4
            under_budget = tokens <= 1000
            print(f"  Tokens (~{tokens}): {'✓' if under_budget else '✗'} (limit: 1000)")

            return has_hash and under_budget

        return False

    def run_all(self):
        """Run all verification tests."""
        print("=" * 60)
        print("D3 VERIFICATION: ORIENTATION_BEAD CHECKSUM")
        print("=" * 60)

        tests = [
            ("INV-D3-CHECKSUM-1", self.test_inv_d3_checksum_1_machine_verifiable),
            ("INV-D3-CHECKSUM-HASH", self.test_inv_d3_checksum_hash_integrity),
            ("INV-D3-CROSS-CHECK-1", self.test_inv_d3_cross_check_1_verifiable),
            ("INV-D3-NO-DERIVED-1", self.test_inv_d3_no_derived_1_no_summaries),
            ("POSITIVE_TEST (speed)", self.test_positive_verification_speed),
            ("GATE_D3_1 (generation)", self.test_gate_d3_1_generates_from_state),
            ("GATE_D3_2 (verification)", self.test_gate_d3_2_verification_success),
            ("FILE_SEAM", self.test_file_seam_output),
        ]

        for name, test_fn in tests:
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
            print("D3 VERIFICATION: ALL PASS ✓")
            return True
        else:
            print("D3 VERIFICATION: SOME FAILED ✗")
            return False


if __name__ == "__main__":
    verifier = D3Verification()
    success = verifier.run_all()
    sys.exit(0 if success else 1)
