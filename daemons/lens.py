"""
Response Lens — Inject responses into Claude's view
=====================================================

S34: D1 FILE_SEAM_COMPLETION

Watches /phoenix/responses/ for new response files.
Makes them available to Claude via file flag or MCP fallback.

INVARIANT:
- INV-D1-LENS-1: Response injection adds ≤50 tokens to context

DESIGN:
- File flag approach: Set /phoenix/state/new_response.flag
- Claude polls flag, reads response
- MCP fallback: Single tool read_phoenix_response() (~30 tokens)
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# LENS CONFIG
# =============================================================================


@dataclass
class LensConfig:
    """Configuration for response lens."""

    # Directories
    responses_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "responses")
    state_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "state")

    # Flag file for Claude to poll
    flag_file: str = "new_response.flag"

    # Polling
    poll_interval_ms: int = 500

    # Patterns
    response_pattern: str = "*.md"

    # Delivery tracking
    max_pending: int = 10


# =============================================================================
# RESPONSE TRACKING
# =============================================================================


@dataclass
class PendingResponse:
    """Tracks a pending response for delivery."""

    path: Path
    detected_at: datetime
    delivered: bool = False
    delivered_at: datetime | None = None


@dataclass
class LensStats:
    """Statistics for lens operation."""

    responses_detected: int = 0
    responses_delivered: int = 0
    flags_set: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "responses_detected": self.responses_detected,
            "responses_delivered": self.responses_delivered,
            "flags_set": self.flags_set,
            "uptime_seconds": (datetime.now(UTC) - self.start_time).total_seconds(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }


# =============================================================================
# RESPONSE LENS
# =============================================================================


class ResponseLens:
    """
    Watches for responses and makes them visible to Claude.

    Approach:
    1. Detect new .md files in /responses/
    2. Set flag file with response metadata
    3. Claude polls flag, reads response
    4. Mark as delivered

    MCP fallback: read_phoenix_response() tool (~30 tokens)
    """

    def __init__(
        self,
        config: LensConfig | None = None,
        on_response_detected: Callable[[Path], None] | None = None,
    ) -> None:
        """
        Initialize lens.

        Args:
            config: Lens configuration
            on_response_detected: Callback when new response found
        """
        self._config = config or LensConfig()
        self._on_response_detected = on_response_detected

        # State
        self._running = False
        self._thread: threading.Thread | None = None
        self._stats = LensStats()

        # Track known files (to detect new ones)
        self._known_files: set[str] = set()
        self._pending: list[PendingResponse] = []
        self._lock = threading.Lock()

        # Ensure directories exist
        self._config.responses_dir.mkdir(parents=True, exist_ok=True)
        self._config.state_dir.mkdir(parents=True, exist_ok=True)

        # Initialize known files
        self._scan_existing()

    @property
    def running(self) -> bool:
        """Check if lens is running."""
        return self._running

    @property
    def stats(self) -> LensStats:
        """Get lens statistics."""
        return self._stats

    @property
    def flag_path(self) -> Path:
        """Path to response flag file."""
        return self._config.state_dir / self._config.flag_file

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def start(self) -> None:
        """Start the lens daemon."""
        if self._running:
            logger.warning("Lens already running")
            return

        self._running = True
        self._stats = LensStats()

        # Clear any stale flag
        self._clear_flag()

        # Start polling thread
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

        logger.info(
            f"Response lens started: watching {self._config.responses_dir} "
            f"(poll: {self._config.poll_interval_ms}ms)"
        )

    def stop(self) -> None:
        """Stop the lens daemon."""
        self._running = False

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.info(f"Response lens stopped. Stats: {self._stats.to_dict()}")

    def _scan_existing(self) -> None:
        """Scan for existing response files on init."""
        for path in self._config.responses_dir.glob(self._config.response_pattern):
            self._known_files.add(path.name)

    # =========================================================================
    # POLLING
    # =========================================================================

    def _poll_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                self._poll_once()
            except Exception as e:
                logger.error(f"Lens poll error: {e}")

            time.sleep(self._config.poll_interval_ms / 1000)

    def _poll_once(self) -> None:
        """Single poll iteration — detect new responses."""
        current_files = set()

        for path in self._config.responses_dir.glob(self._config.response_pattern):
            current_files.add(path.name)

            # Check if new
            if path.name not in self._known_files:
                self._on_new_response(path)

        # Update known files
        self._known_files = current_files

    def _on_new_response(self, path: Path) -> None:
        """
        Handle newly detected response file.

        Args:
            path: Path to new response
        """
        logger.info(f"New response detected: {path.name}")
        self._stats.responses_detected += 1
        self._stats.last_activity = datetime.now(UTC)

        # Track as pending
        pending = PendingResponse(
            path=path,
            detected_at=datetime.now(UTC),
        )

        with self._lock:
            self._pending.append(pending)

            # Trim old pending
            if len(self._pending) > self._config.max_pending:
                self._pending = self._pending[-self._config.max_pending :]

        # Set flag for Claude
        self._set_flag(path)

        # Callback
        if self._on_response_detected:
            try:
                self._on_response_detected(path)
            except Exception as e:
                logger.error(f"Response callback error: {e}")

    # =========================================================================
    # FLAG FILE (Claude polling)
    # =========================================================================

    def _set_flag(self, response_path: Path) -> None:
        """
        Set response flag for Claude.

        Flag contains minimal metadata (~30 tokens):
        - file: Filename to read
        - type: Response type
        - ts: Detection time (short format)

        INV-D1-LENS-1: ≤50 tokens
        """
        # Read response type from frontmatter
        response_type = self._extract_type(response_path)

        # Compact format to stay under 50 tokens
        flag_data = {
            "file": response_path.name,
            "type": response_type,
            "ts": datetime.now(UTC).strftime("%H:%M:%S"),
        }

        # Write flag file (no indent = more compact)
        self.flag_path.write_text(json.dumps(flag_data))
        self._stats.flags_set += 1

        logger.debug(f"Flag set: {response_path.name}")

    def _clear_flag(self) -> None:
        """Clear the response flag."""
        if self.flag_path.exists():
            self.flag_path.unlink()

    def _extract_type(self, path: Path) -> str:
        """Extract response type from frontmatter."""
        try:
            content = path.read_text()
            if content.startswith("---"):
                for line in content.split("\n")[1:20]:  # Check first 20 lines
                    if line.startswith("type: "):
                        return line.replace("type: ", "").strip()
                    if line == "---":
                        break
        except Exception:  # noqa: S110 - intentional silent fail for type extraction
            pass
        return "unknown"

    # =========================================================================
    # PUBLIC API (for MCP tool fallback)
    # =========================================================================

    def get_pending_responses(self) -> list[dict[str, Any]]:
        """
        Get list of pending (unacknowledged) responses.

        For MCP tool: read_phoenix_responses()
        """
        with self._lock:
            return [
                {
                    "file": p.path.name,
                    "type": self._extract_type(p.path),
                    "detected_at": p.detected_at.isoformat(),
                    "delivered": p.delivered,
                }
                for p in self._pending
                if not p.delivered
            ]

    def get_latest_response(self) -> dict[str, Any] | None:
        """
        Get the most recent pending response.

        For MCP tool: read_phoenix_response()

        INV-D1-LENS-1: Returns ≤50 tokens metadata
        """
        with self._lock:
            undelivered = [p for p in self._pending if not p.delivered]
            if not undelivered:
                return None

            latest = undelivered[-1]
            # Compact format: ~40 tokens
            return {
                "file": latest.path.name,
                "type": self._extract_type(latest.path),
                "ts": latest.detected_at.strftime("%H:%M:%S"),
            }

    def read_response(self, filename: str) -> str | None:
        """
        Read response content by filename.

        For MCP tool: read_phoenix_response(filename)
        """
        path = self._config.responses_dir / filename
        if not path.exists():
            return None

        content = path.read_text()

        # Mark as delivered
        self._mark_delivered(filename)

        return content

    def _mark_delivered(self, filename: str) -> None:
        """Mark a response as delivered."""
        with self._lock:
            for p in self._pending:
                if p.path.name == filename and not p.delivered:
                    p.delivered = True
                    p.delivered_at = datetime.now(UTC)
                    self._stats.responses_delivered += 1
                    break

    def acknowledge_all(self) -> int:
        """
        Acknowledge all pending responses.

        Called after Claude reads them.

        Returns:
            Number of responses acknowledged
        """
        count = 0
        with self._lock:
            for p in self._pending:
                if not p.delivered:
                    p.delivered = True
                    p.delivered_at = datetime.now(UTC)
                    count += 1
                    self._stats.responses_delivered += 1

        if count:
            self._clear_flag()
            logger.info(f"Acknowledged {count} responses")

        return count

    def check_flag(self) -> dict[str, Any] | None:
        """
        Check if response flag is set.

        For Claude polling: Check this file for new responses.
        """
        if not self.flag_path.exists():
            return None

        try:
            return json.loads(self.flag_path.read_text())
        except Exception:
            return None


# =============================================================================
# MCP TOOL HELPERS
# =============================================================================


def create_mcp_read_response_tool(lens: ResponseLens) -> dict[str, Any]:
    """
    Create MCP tool definition for reading Phoenix responses.

    Token cost: ~30 tokens for tool definition
    """
    return {
        "name": "read_phoenix_response",
        "description": "Read the latest Phoenix response",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Optional filename. If omitted, reads latest.",
                }
            },
        },
    }


def handle_mcp_read_response(
    lens: ResponseLens,
    filename: str | None = None,
) -> dict[str, Any]:
    """
    Handle MCP tool call for reading response.

    Args:
        lens: ResponseLens instance
        filename: Optional specific file

    Returns:
        Tool response with content or error
    """
    if filename:
        content = lens.read_response(filename)
        if content:
            return {"success": True, "content": content}
        return {"success": False, "error": f"Response not found: {filename}"}

    # Get latest
    latest = lens.get_latest_response()
    if latest:
        content = lens.read_response(latest["file"])
        return {"success": True, "metadata": latest, "content": content}

    return {"success": False, "error": "No pending responses"}
