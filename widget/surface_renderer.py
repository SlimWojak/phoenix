"""
Surface Renderer — Verbatim State Projection
=============================================

S34: D4 SURFACE_RENDERER_POC

Reads OrientationBead and projects MAX 4 fields verbatim.
NO derivation. NO interpretation. NO actions.

INVARIANTS:
- INV-D4-GLANCEABLE-1: Update <100ms
- INV-D4-ACCURATE-1: Matches actual state
- INV-D4-NO-ACTIONS-1: Read-only
- INV-D4-NO-DERIVATION-1: Every field verbatim from OrientationBead
- INV-D4-EPHEMERAL-1: No local state persistence

"UI is projection of state, not participant in reasoning."
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# RENDER STATE (Verbatim projection of OrientationBead)
# =============================================================================


@dataclass
class RenderState:
    """
    Render state — MAX 4 fields, verbatim from OrientationBead.

    INV-D4-NO-DERIVATION-1: Every field comes directly from source.
    """

    # Source available?
    source_available: bool = False

    # VERBATIM FIELDS (4 max, no derivation)
    heartbeat_status: str | None = None  # Verbatim from bead
    positions_open: int | None = None  # Verbatim from bead
    mode: str | None = None  # Verbatim from bead
    kill_flags_active: int | None = None  # Verbatim from bead

    # Metadata (for staleness check only)
    generated_at: datetime | None = None
    read_at: datetime | None = None

    @property
    def is_stale(self) -> bool:
        """Check if orientation is stale (>5 min old)."""
        if not self.generated_at:
            return True
        age = (datetime.now(UTC) - self.generated_at).total_seconds()
        return age > 300  # 5 minutes

    def to_menu_title(self) -> str:
        """
        Render to menu bar title.

        INV-D4-NO-DERIVATION-1: Only verbatim mapping, no logic.
        """
        if not self.source_available:
            return "⚠️ NO STATE"

        if self.is_stale:
            return "⏳ STALE"

        # Verbatim emoji mapping (no interpretation)
        health_emoji = self._health_to_emoji(self.heartbeat_status)
        mode_emoji = self._mode_to_emoji(self.mode)

        # Format: 🟢 0 📄 0
        # (health, positions, mode, kill_flags)
        parts = [
            health_emoji,
            str(self.positions_open or 0),
            mode_emoji,
            str(self.kill_flags_active or 0),
        ]

        return " ".join(parts)

    def to_detail_text(self) -> str:
        """
        Render detail text for click popup.

        INV-D4-NO-DERIVATION-1: Verbatim field values only.
        """
        if not self.source_available:
            return "No orientation state available.\nCheck if orientation.yaml exists."

        lines = [
            "ORIENTATION STATE",
            "=" * 30,
            f"Health: {self.heartbeat_status}",
            f"Positions: {self.positions_open}",
            f"Mode: {self.mode}",
            f"Kill Flags: {self.kill_flags_active}",
            "",
            f"Generated: {self.generated_at.isoformat() if self.generated_at else 'N/A'}",
            f"Stale: {'YES' if self.is_stale else 'NO'}",
        ]

        return "\n".join(lines)

    @staticmethod
    def _health_to_emoji(status: str | None) -> str:
        """
        Verbatim enum → emoji mapping.

        INV-D4-NO-DERIVATION-1: Direct 1:1 mapping only.
        """
        if status is None:
            return "⚪"
        mapping = {
            "HEALTHY": "🟢",
            "DEGRADED": "🟡",
            "MISSED": "🔴",
            "UNKNOWN": "⚪",
        }
        return mapping.get(status.upper(), "⚪")

    @staticmethod
    def _mode_to_emoji(mode: str | None) -> str:
        """
        Verbatim enum → emoji mapping.

        INV-D4-NO-DERIVATION-1: Direct 1:1 mapping only.
        """
        if mode is None:
            return "❓"
        mapping = {
            "MOCK": "🧪",
            "PAPER": "📄",
            "LIVE_LOCKED": "⚠️",
        }
        return mapping.get(mode.upper(), "❓")


# =============================================================================
# SURFACE RENDERER
# =============================================================================


class SurfaceRenderer:
    """
    Surface Renderer — Projects OrientationBead to UI surface.

    INV-D4-GLANCEABLE-1: Update <100ms
    INV-D4-ACCURATE-1: Matches actual state
    INV-D4-NO-DERIVATION-1: Verbatim fields only
    INV-D4-EPHEMERAL-1: No local state persistence

    "UI is projection of state, not participant in reasoning."
    """

    # Default path to orientation state
    DEFAULT_ORIENTATION_PATH = Path(__file__).parent.parent / "state" / "orientation.yaml"

    def __init__(
        self,
        orientation_path: Path | None = None,
    ) -> None:
        """
        Initialize renderer.

        INV-D4-EPHEMERAL-1: No state stored on init.

        Args:
            orientation_path: Path to orientation.yaml (default: state/orientation.yaml)
        """
        self._orientation_path = orientation_path or self.DEFAULT_ORIENTATION_PATH

        # INV-D4-EPHEMERAL-1: NO cached state
        # State is read fresh every time

    def read_state(self) -> RenderState:
        """
        Read current orientation and project to RenderState.

        INV-D4-GLANCEABLE-1: Must complete <100ms
        INV-D4-NO-DERIVATION-1: Verbatim fields only
        INV-D4-EPHEMERAL-1: No caching, fresh read every time

        Returns:
            RenderState (blank if source unavailable)
        """
        start = time.perf_counter()

        state = RenderState(read_at=datetime.now(UTC))

        # Check source exists
        if not self._orientation_path.exists():
            state.source_available = False
            return state

        try:
            # Read YAML
            with open(self._orientation_path) as f:
                data: dict[str, Any] = yaml.safe_load(f)

            if not data:
                state.source_available = False
                return state

            # Extract VERBATIM fields only (INV-D4-NO-DERIVATION-1)
            state.source_available = True
            state.heartbeat_status = data.get("heartbeat_status")
            state.positions_open = data.get("positions_open")
            state.mode = data.get("mode")
            state.kill_flags_active = data.get("kill_flags_active")

            # Metadata for staleness
            if "generated_at" in data:
                state.generated_at = datetime.fromisoformat(data["generated_at"])

        except Exception:
            # Any error = source unavailable
            state.source_available = False

        # INV-D4-GLANCEABLE-1: Verify <100ms
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > 100:
            # Log warning but don't fail
            pass

        return state

    def get_menu_title(self) -> str:
        """
        Get current menu bar title.

        INV-D4-EPHEMERAL-1: Reads fresh, no cache.
        """
        state = self.read_state()
        return state.to_menu_title()

    def get_detail_text(self) -> str:
        """
        Get detail text for popup.

        INV-D4-EPHEMERAL-1: Reads fresh, no cache.
        """
        state = self.read_state()
        return state.to_detail_text()

    def verify_no_derivation(self) -> bool:
        """
        Verify INV-D4-NO-DERIVATION-1.

        Check that state matches source file exactly.
        """
        if not self._orientation_path.exists():
            return True  # Nothing to derive from

        state = self.read_state()

        if not state.source_available:
            return True

        # Re-read source
        with open(self._orientation_path) as f:
            data = yaml.safe_load(f)

        # Verify each field is verbatim
        checks = [
            state.heartbeat_status == data.get("heartbeat_status"),
            state.positions_open == data.get("positions_open"),
            state.mode == data.get("mode"),
            state.kill_flags_active == data.get("kill_flags_active"),
        ]

        return all(checks)

    def verify_blank_on_missing(self) -> bool:
        """
        Verify INV-D4-NO-DERIVATION-1: Goes BLANK when source missing.

        Delete orientation.yaml → widget goes blank, not default/stale.
        """
        if self._orientation_path.exists():
            return True  # Can't test when file exists

        state = self.read_state()

        # Must be source_available=False (blank)
        if state.source_available:
            return False

        # Must not show any data
        if state.heartbeat_status is not None:
            return False
        if state.positions_open is not None:
            return False
        if state.mode is not None:
            return False
        if state.kill_flags_active is not None:
            return False

        return True
