#!/usr/bin/env python3
"""
Menu Bar Widget — macOS rumps Implementation
============================================

S34: D4 SURFACE_RENDERER_POC

Read-only menu bar showing OrientationBead state.
NO actions. NO controls. Projection only.

INVARIANTS:
- INV-D4-GLANCEABLE-1: Update <100ms
- INV-D4-ACCURATE-1: Matches actual state
- INV-D4-NO-ACTIONS-1: Read-only, no actions
- INV-D4-NO-DERIVATION-1: Every field verbatim from OrientationBead
- INV-D4-EPHEMERAL-1: No local state persistence

"UI is projection of state, not participant in reasoning."

USAGE:
    python -m phoenix.widget.menu_bar
    # Or: python phoenix/widget/menu_bar.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add phoenix root to path for standalone execution
PHOENIX_ROOT = Path(__file__).resolve().parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

try:
    import rumps
except ImportError:
    print("ERROR: rumps not installed. Run: pip install rumps")
    sys.exit(1)

from widget.surface_renderer import SurfaceRenderer  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# PHOENIX MENU BAR APP
# =============================================================================


class PhoenixMenuBar(rumps.App):
    """
    Phoenix Menu Bar — Read-only state projection.

    INV-D4-NO-ACTIONS-1: No actions, no controls.
    INV-D4-EPHEMERAL-1: No local state, fresh read every refresh.
    """

    # Refresh interval (seconds)
    REFRESH_INTERVAL = 5

    def __init__(self) -> None:
        """
        Initialize menu bar.

        INV-D4-EPHEMERAL-1: No state stored on init.
        """
        # Initial title (will be updated on first tick)
        super().__init__("⏳", quit_button=None)

        # Renderer (stateless projection)
        self._renderer = SurfaceRenderer()

        # Menu items (read-only display)
        self._detail_item = rumps.MenuItem("Loading...", callback=None)
        self._separator = rumps.separator
        self._quit_item = rumps.MenuItem("Quit Phoenix Widget", callback=self._quit)

        # Build menu (INV-D4-NO-ACTIONS-1: No action items except quit)
        self.menu = [
            self._detail_item,
            self._separator,
            self._quit_item,
        ]

        # Start refresh timer
        self._timer = rumps.Timer(self._refresh, self.REFRESH_INTERVAL)
        self._timer.start()

        # Initial refresh
        self._refresh(None)

    def _refresh(self, _sender: rumps.Timer | None) -> None:
        """
        Refresh display from OrientationBead.

        INV-D4-EPHEMERAL-1: Fresh read, no cache.
        INV-D4-NO-DERIVATION-1: Verbatim fields only.
        """
        try:
            # Update title (INV-D4-GLANCEABLE-1: <100ms)
            self.title = self._renderer.get_menu_title()

            # Update detail text
            detail = self._renderer.get_detail_text()
            self._detail_item.title = detail.split("\n")[0]  # First line as menu item

        except Exception as e:
            logger.error(f"Refresh error: {e}")
            self.title = "❌ ERROR"

    @rumps.clicked("Show Details")
    def _show_details(self, _sender: rumps.MenuItem) -> None:
        """
        Show detail popup.

        INV-D4-NO-ACTIONS-1: Read-only display only.
        """
        detail = self._renderer.get_detail_text()
        rumps.alert(
            title="Phoenix Orientation",
            message=detail,
            ok="Close",
        )

    def _quit(self, _sender: rumps.MenuItem) -> None:
        """Quit the app."""
        rumps.quit_application()


# =============================================================================
# STANDALONE MENU BAR (No actions variant)
# =============================================================================


class PhoenixMenuBarSimple(rumps.App):
    """
    Simplified menu bar — absolutely minimal.

    For testing/verification. No menu, just title + quit.

    INV-D4-NO-ACTIONS-1: Zero actions.
    """

    REFRESH_INTERVAL = 5

    def __init__(self) -> None:
        """Initialize minimal menu bar."""
        super().__init__("⏳", quit_button="Quit")

        self._renderer = SurfaceRenderer()

        # Timer
        self._timer = rumps.Timer(self._refresh, self.REFRESH_INTERVAL)
        self._timer.start()

        self._refresh(None)

    def _refresh(self, _sender: rumps.Timer | None) -> None:
        """Refresh title."""
        try:
            self.title = self._renderer.get_menu_title()
        except Exception:
            self.title = "❌"


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """Run the Phoenix menu bar widget."""
    logger.info("Starting Phoenix Menu Bar Widget...")
    logger.info("INV-D4-NO-ACTIONS-1: Read-only mode")
    logger.info("INV-D4-EPHEMERAL-1: No local state")

    app = PhoenixMenuBarSimple()
    app.run()


if __name__ == "__main__":
    main()
