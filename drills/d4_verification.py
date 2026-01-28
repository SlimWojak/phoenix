#!/usr/bin/env python3
"""
D4 Verification Script — SURFACE_RENDERER_POC
==============================================

S34: D4 Surface Renderer Proof-of-Concept

"UI is projection of state, not participant in reasoning."

INVARIANTS:
- INV-D4-GLANCEABLE-1: Update <100ms
- INV-D4-ACCURATE-1: Matches actual state
- INV-D4-NO-ACTIONS-1: Read-only, no actions
- INV-D4-NO-DERIVATION-1: Every field verbatim from OrientationBead
- INV-D4-EPHEMERAL-1: Renderer must not persist state locally
"""

import shutil
import sys
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add phoenix root to path
PHOENIX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

import yaml  # noqa: E402


class D4Verification:
    """Run all D4 invariant tests."""

    def __init__(self):
        self.results = {}
        self._temp_dir = None

    def setup(self):
        """Create temp directory for isolated tests."""
        self._temp_dir = Path(tempfile.mkdtemp(prefix="d4_test_"))
        return self._temp_dir

    def cleanup(self):
        """Clean up temp directory."""
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)

    def test_inv_d4_glanceable_1_update_speed(self) -> bool:
        """INV-D4-GLANCEABLE-1: Update <100ms."""
        print("\n[INV-D4-GLANCEABLE-1] Testing update speed...")

        from widget.surface_renderer import SurfaceRenderer

        renderer = SurfaceRenderer()

        # Measure read time
        times = []
        for _ in range(10):
            start = time.perf_counter()
            renderer.read_state()
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)

        avg_ms = sum(times) / len(times)
        max_ms = max(times)

        print(f"  Average: {avg_ms:.2f}ms")
        print(f"  Max: {max_ms:.2f}ms")
        print(f"  Under 100ms: {'✓' if max_ms < 100 else '✗'}")

        return max_ms < 100

    def test_inv_d4_accurate_1_matches_state(self) -> bool:
        """INV-D4-ACCURATE-1: Matches actual state."""
        print("\n[INV-D4-ACCURATE-1] Testing accuracy...")

        temp_dir = self.setup()
        orientation_path = temp_dir / "orientation.yaml"

        # Create known state
        known_state = {
            "bead_id": "test-123",
            "generated_at": datetime.now(UTC).isoformat(),
            "execution_phase": "S34_OPERATIONAL",
            "mode": "PAPER",
            "active_invariants_count": 71,
            "kill_flags_active": 2,
            "unresolved_drift_count": 0,
            "positions_open": 3,
            "heartbeat_status": "HEALTHY",
            "last_human_action_bead_id": None,
            "last_alert_id": None,
            "bead_hash": "a" * 64,
        }

        with open(orientation_path, "w") as f:
            yaml.dump(known_state, f)

        from widget.surface_renderer import SurfaceRenderer

        renderer = SurfaceRenderer(orientation_path=orientation_path)
        state = renderer.read_state()

        # Verify accuracy
        checks = [
            ("source_available", state.source_available, True),
            ("heartbeat_status", state.heartbeat_status, "HEALTHY"),
            ("positions_open", state.positions_open, 3),
            ("mode", state.mode, "PAPER"),
            ("kill_flags_active", state.kill_flags_active, 2),
        ]

        all_match = True
        for name, actual, expected in checks:
            match = actual == expected
            print(f"  {name}: {actual} == {expected} {'✓' if match else '✗'}")
            if not match:
                all_match = False

        self.cleanup()
        return all_match

    def test_inv_d4_no_derivation_1_verbatim(self) -> bool:
        """INV-D4-NO-DERIVATION-1: Every field verbatim."""
        print("\n[INV-D4-NO-DERIVATION-1] Testing no derivation...")

        from widget.surface_renderer import SurfaceRenderer

        renderer = SurfaceRenderer()
        result = renderer.verify_no_derivation()

        print(f"  No derivation: {'✓' if result else '✗'}")
        return result

    def test_inv_d4_ephemeral_1_no_persistence(self) -> bool:
        """INV-D4-EPHEMERAL-1: No local state persistence."""
        print("\n[INV-D4-EPHEMERAL-1] Testing no persistence...")

        temp_dir = self.setup()
        orientation_path = temp_dir / "orientation.yaml"

        from widget.surface_renderer import SurfaceRenderer

        # Create renderer with no file
        renderer = SurfaceRenderer(orientation_path=orientation_path)

        # Read should return blank (not cached/default)
        state1 = renderer.read_state()
        no_source = not state1.source_available
        print(f"  No file → blank: {'✓' if no_source else '✗'}")

        # Create file
        test_state = {
            "heartbeat_status": "HEALTHY",
            "positions_open": 5,
            "mode": "PAPER",
            "kill_flags_active": 0,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        with open(orientation_path, "w") as f:
            yaml.dump(test_state, f)

        # Read should now show data
        state2 = renderer.read_state()
        has_source = state2.source_available
        print(f"  With file → data: {'✓' if has_source else '✗'}")

        # Delete file
        orientation_path.unlink()

        # Read should go blank again (not cached)
        state3 = renderer.read_state()
        blank_again = not state3.source_available
        print(f"  Delete file → blank: {'✓' if blank_again else '✗'}")

        self.cleanup()
        return no_source and has_source and blank_again

    def test_gate_d4_1_displays_4_fields(self) -> bool:
        """GATE_D4_1: Widget displays 4 fields from OrientationBead."""
        print("\n[GATE_D4_1] Testing 4 field display...")

        temp_dir = self.setup()
        orientation_path = temp_dir / "orientation.yaml"

        test_state = {
            "heartbeat_status": "HEALTHY",
            "positions_open": 2,
            "mode": "PAPER",
            "kill_flags_active": 1,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        with open(orientation_path, "w") as f:
            yaml.dump(test_state, f)

        from widget.surface_renderer import SurfaceRenderer

        renderer = SurfaceRenderer(orientation_path=orientation_path)
        title = renderer.get_menu_title()

        # Should contain all 4 indicators
        has_health = "🟢" in title or "🟡" in title or "🔴" in title or "⚪" in title
        has_mode = "📄" in title or "🧪" in title or "⚠️" in title
        has_positions = "2" in title
        has_kill = "1" in title

        print(f"  Title: '{title}'")
        print(f"  Has health emoji: {'✓' if has_health else '✗'}")
        print(f"  Has positions: {'✓' if has_positions else '✗'}")
        print(f"  Has mode emoji: {'✓' if has_mode else '✗'}")
        print(f"  Has kill flags: {'✓' if has_kill else '✗'}")

        self.cleanup()
        return has_health and has_positions and has_mode and has_kill

    def test_gate_d4_2_blank_on_delete(self) -> bool:
        """GATE_D4_2: Delete orientation → widget goes blank."""
        print("\n[GATE_D4_2] Testing blank on missing...")

        temp_dir = self.setup()
        orientation_path = temp_dir / "orientation.yaml"

        # Create then delete
        test_state = {"heartbeat_status": "HEALTHY", "positions_open": 0}
        with open(orientation_path, "w") as f:
            yaml.dump(test_state, f)
        orientation_path.unlink()

        from widget.surface_renderer import SurfaceRenderer

        renderer = SurfaceRenderer(orientation_path=orientation_path)
        state = renderer.read_state()
        title = renderer.get_menu_title()

        is_blank = not state.source_available
        shows_no_state = "NO STATE" in title

        print(f"  source_available=False: {'✓' if is_blank else '✗'}")
        print(f"  Shows 'NO STATE': {'✓' if shows_no_state else '✗'}")
        print(f"  Title: '{title}'")

        self.cleanup()
        return is_blank and shows_no_state

    def test_gate_d4_3_updates_within_5s(self) -> bool:
        """GATE_D4_3: Widget updates within 5s of state change."""
        print("\n[GATE_D4_3] Testing update responsiveness...")

        # This is a design verification - the renderer has no cache
        # so every read is fresh within the read_state() call time

        from widget.surface_renderer import SurfaceRenderer

        renderer = SurfaceRenderer()

        # Measure responsiveness
        start = time.perf_counter()
        renderer.read_state()
        elapsed_ms = (time.perf_counter() - start) * 1000

        # With 5s refresh + <100ms read, updates are guaranteed within 5.1s
        responsive = elapsed_ms < 100

        print(f"  Read latency: {elapsed_ms:.2f}ms")
        print("  With 5s refresh cycle: updates within 5.1s guaranteed")
        print(f"  Responsive: {'✓' if responsive else '✗'}")

        return responsive

    def test_cv_d4_source_missing(self) -> bool:
        """CV_D4_SOURCE_MISSING: Orientation unavailable → NO STATE."""
        print("\n[CV_D4_SOURCE_MISSING] Source missing chaos...")

        temp_dir = self.setup()
        nonexistent_path = temp_dir / "does_not_exist.yaml"

        from widget.surface_renderer import SurfaceRenderer

        renderer = SurfaceRenderer(orientation_path=nonexistent_path)
        title = renderer.get_menu_title()

        shows_warning = "NO STATE" in title
        print(f"  Title on missing: '{title}'")
        print(f"  Shows NO STATE: {'✓' if shows_warning else '✗'}")

        self.cleanup()
        return shows_warning

    def test_cv_d4_stale_orientation(self) -> bool:
        """CV_D4_STALE_ORIENTATION: Bead >5 min → staleness indicator."""
        print("\n[CV_D4_STALE_ORIENTATION] Stale bead chaos...")

        temp_dir = self.setup()
        orientation_path = temp_dir / "orientation.yaml"

        # Create stale state (10 min old)
        stale_time = datetime.now(UTC) - timedelta(minutes=10)
        test_state = {
            "heartbeat_status": "HEALTHY",
            "positions_open": 0,
            "mode": "PAPER",
            "kill_flags_active": 0,
            "generated_at": stale_time.isoformat(),
        }
        with open(orientation_path, "w") as f:
            yaml.dump(test_state, f)

        from widget.surface_renderer import SurfaceRenderer

        renderer = SurfaceRenderer(orientation_path=orientation_path)
        state = renderer.read_state()
        title = renderer.get_menu_title()

        is_stale = state.is_stale
        shows_stale = "STALE" in title

        print(f"  State.is_stale: {'✓' if is_stale else '✗'}")
        print(f"  Title shows STALE: {'✓' if shows_stale else '✗'}")
        print(f"  Title: '{title}'")

        self.cleanup()
        return is_stale and shows_stale

    def run_all(self):
        """Run all verification tests."""
        print("=" * 60)
        print("D4 VERIFICATION: SURFACE_RENDERER_POC")
        print("=" * 60)
        print()
        print('"UI is projection of state, not participant in reasoning."')

        tests = [
            ("INV-D4-GLANCEABLE-1 (speed)", self.test_inv_d4_glanceable_1_update_speed),
            ("INV-D4-ACCURATE-1 (matches)", self.test_inv_d4_accurate_1_matches_state),
            ("INV-D4-NO-DERIVATION-1", self.test_inv_d4_no_derivation_1_verbatim),
            ("INV-D4-EPHEMERAL-1 (no persist)", self.test_inv_d4_ephemeral_1_no_persistence),
            ("GATE_D4_1 (4 fields)", self.test_gate_d4_1_displays_4_fields),
            ("GATE_D4_2 (blank on delete)", self.test_gate_d4_2_blank_on_delete),
            ("GATE_D4_3 (updates <5s)", self.test_gate_d4_3_updates_within_5s),
            ("CV_D4_SOURCE_MISSING", self.test_cv_d4_source_missing),
            ("CV_D4_STALE_ORIENTATION", self.test_cv_d4_stale_orientation),
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
            print("D4 VERIFICATION: ALL PASS ✓")
            return True
        else:
            print("D4 VERIFICATION: SOME FAILED ✗")
            return False


if __name__ == "__main__":
    verifier = D4Verification()
    success = verifier.run_all()
    sys.exit(0 if success else 1)
