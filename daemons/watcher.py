"""
Intent Watcher — File-based intent detection daemon
====================================================

S34: D1 FILE_SEAM_COMPLETION

Watches /phoenix/intents/incoming/ for new intent files.
Routes to workers via IntentRouter.
Moves processed intents to /processed/, unknown to /unprocessed/.

INVARIANTS:
- INV-D1-WATCHER-1: Every intent processed exactly once
- INV-D1-WATCHER-IMMUTABLE-1: Watcher may not modify intent payloads
- INV-D1-HALT-PRIORITY-1: HALT bypasses queue, processes immediately

DESIGN:
- Poll-based (500ms default) with optional watchdog upgrade
- Hash-based duplicate detection
- Graceful degradation on errors
"""

from __future__ import annotations

import hashlib
import logging
import shutil
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .routing import Intent, IntentRouter, IntentType, RouteResult, parse_intent

logger = logging.getLogger(__name__)


# =============================================================================
# WATCHER CONFIG
# =============================================================================


@dataclass
class WatcherConfig:
    """Configuration for intent watcher."""

    # Directories
    incoming_dir: Path = field(
        default_factory=lambda: Path(__file__).parent.parent / "intents" / "incoming"
    )
    processed_dir: Path = field(
        default_factory=lambda: Path(__file__).parent.parent / "intents" / "processed"
    )
    unprocessed_dir: Path = field(
        default_factory=lambda: Path(__file__).parent.parent / "intents" / "unprocessed"
    )

    # Polling
    poll_interval_ms: int = 500
    use_watchdog: bool = False  # Fallback to poll if False

    # Resilience
    max_retries: int = 3
    retry_delay_ms: int = 1000

    # File patterns
    intent_pattern: str = "*.yaml"


# =============================================================================
# WATCHER STATE
# =============================================================================


@dataclass
class WatcherStats:
    """Statistics for watcher operation."""

    intents_processed: int = 0
    intents_failed: int = 0
    intents_quarantined: int = 0
    halt_intents: int = 0
    duplicates_skipped: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intents_processed": self.intents_processed,
            "intents_failed": self.intents_failed,
            "intents_quarantined": self.intents_quarantined,
            "halt_intents": self.halt_intents,
            "duplicates_skipped": self.duplicates_skipped,
            "uptime_seconds": (datetime.now(UTC) - self.start_time).total_seconds(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }


# =============================================================================
# INTENT WATCHER
# =============================================================================


class IntentWatcher:
    """
    Watches for new intent files and routes to workers.

    INVARIANT: INV-D1-WATCHER-1
    Every intent is processed exactly once.
    Uses hash-based tracking to prevent duplicates.

    INVARIANT: INV-D1-WATCHER-IMMUTABLE-1
    Intent payloads are NEVER modified.
    Hash verified before/after routing.
    """

    def __init__(
        self,
        router: IntentRouter,
        config: WatcherConfig | None = None,
        on_intent_processed: Callable[[Intent, RouteResult], None] | None = None,
    ) -> None:
        """
        Initialize watcher.

        Args:
            router: Intent router for dispatching
            config: Watcher configuration
            on_intent_processed: Callback after processing
        """
        self._router = router
        self._config = config or WatcherConfig()
        self._on_intent_processed = on_intent_processed

        # State
        self._running = False
        self._thread: threading.Thread | None = None
        self._stats = WatcherStats()

        # Duplicate detection (hash → timestamp)
        self._processed_hashes: dict[str, datetime] = {}
        self._hash_lock = threading.Lock()

        # Ensure directories exist
        self._config.incoming_dir.mkdir(parents=True, exist_ok=True)
        self._config.processed_dir.mkdir(parents=True, exist_ok=True)
        self._config.unprocessed_dir.mkdir(parents=True, exist_ok=True)

    @property
    def running(self) -> bool:
        """Check if watcher is running."""
        return self._running

    @property
    def stats(self) -> WatcherStats:
        """Get watcher statistics."""
        return self._stats

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def start(self) -> None:
        """Start the watcher daemon."""
        if self._running:
            logger.warning("Watcher already running")
            return

        self._running = True
        self._stats = WatcherStats()

        # Recover orphans from previous run
        self._recover_orphans()

        # Start polling thread
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

        logger.info(
            f"Intent watcher started: watching {self._config.incoming_dir} "
            f"(poll: {self._config.poll_interval_ms}ms)"
        )

    def stop(self) -> None:
        """Stop the watcher daemon."""
        self._running = False

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.info(f"Intent watcher stopped. Stats: {self._stats.to_dict()}")

    def _recover_orphans(self) -> None:
        """
        Recover orphan intents from unprocessed directory.

        Called on startup to handle intents from previous crash.
        """
        orphans = list(self._config.unprocessed_dir.glob(self._config.intent_pattern))

        if orphans:
            logger.info(f"Recovering {len(orphans)} orphan intents")

            for orphan_path in orphans:
                # Move back to incoming for reprocessing
                target = self._config.incoming_dir / orphan_path.name
                if not target.exists():
                    shutil.move(str(orphan_path), str(target))
                    logger.info(f"Recovered orphan: {orphan_path.name}")

    # =========================================================================
    # POLLING
    # =========================================================================

    def _poll_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                self._poll_once()
            except Exception as e:
                logger.error(f"Poll error: {e}")

            time.sleep(self._config.poll_interval_ms / 1000)

    def _poll_once(self) -> None:
        """Single poll iteration."""
        intent_files = list(self._config.incoming_dir.glob(self._config.intent_pattern))

        for intent_path in intent_files:
            if not self._running:
                break

            self._process_intent_file(intent_path)

    # =========================================================================
    # INTENT PROCESSING
    # =========================================================================

    def _process_intent_file(self, path: Path) -> None:
        """
        Process a single intent file.

        INV-D1-WATCHER-1: Exactly once processing.
        INV-D1-WATCHER-IMMUTABLE-1: No modification.
        """
        # Read raw content for hash
        try:
            raw_content = path.read_text()
        except Exception as e:
            logger.error(f"Failed to read intent {path}: {e}")
            return

        # Check for duplicate (INV-D1-WATCHER-1)
        content_hash = hashlib.sha256(raw_content.encode()).hexdigest()

        with self._hash_lock:
            if content_hash in self._processed_hashes:
                logger.debug(f"Duplicate intent skipped: {path.name}")
                self._stats.duplicates_skipped += 1
                # Remove duplicate file
                try:
                    path.unlink()
                except Exception:  # noqa: S110 - intentional silent fail for duplicate cleanup
                    pass
                return

        # Parse intent
        intent = parse_intent(path)

        if intent is None:
            # Malformed YAML — quarantine
            self._quarantine(path, "parse_error")
            self._stats.intents_quarantined += 1
            return

        # Verify hash matches (paranoia check)
        if intent.content_hash != content_hash:
            logger.error("Hash mismatch during parsing — possible corruption")
            self._quarantine(path, "hash_mismatch")
            self._stats.intents_quarantined += 1
            return

        # Check for unknown type
        if intent.intent_type == IntentType.UNKNOWN:
            self._quarantine(path, "unknown_type")
            self._stats.intents_quarantined += 1
            logger.warning(f"Unknown intent type quarantined: {path.name}")
            return

        # Check for HALT priority (INV-D1-HALT-PRIORITY-1)
        if self._router.is_priority(intent.intent_type):
            logger.warning("HALT intent detected — processing immediately")
            self._stats.halt_intents += 1

        # Route intent
        result = self._router.route(intent)

        # Verify immutability (INV-D1-WATCHER-IMMUTABLE-1)
        current_content = path.read_text()
        if not intent.verify_immutable(current_content):
            logger.error(
                "INV-D1-WATCHER-IMMUTABLE-1 VIOLATED: " "Intent modified during processing!"
            )
            # Still mark as processed to prevent loops
            self._stats.intents_failed += 1
        elif result.success:
            self._stats.intents_processed += 1
        else:
            self._stats.intents_failed += 1
            logger.error(f"Intent routing failed: {result.error}")

        # Record hash (INV-D1-WATCHER-1)
        with self._hash_lock:
            self._processed_hashes[content_hash] = datetime.now(UTC)

        # Move to processed
        self._move_processed(path)

        # Update stats
        self._stats.last_activity = datetime.now(UTC)

        # Callback
        if self._on_intent_processed:
            try:
                self._on_intent_processed(intent, result)
            except Exception as e:
                logger.error(f"Intent callback error: {e}")

        logger.info(
            f"Intent processed: {intent.intent_type.value} "
            f"({result.processing_time_ms:.1f}ms) "
            f"session={intent.session_id}"
        )

    def _quarantine(self, path: Path, reason: str) -> None:
        """
        Move malformed/unknown intent to quarantine.

        Args:
            path: Intent file path
            reason: Quarantine reason
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        target_name = f"{timestamp}_{reason}_{path.name}"
        target = self._config.unprocessed_dir / target_name

        try:
            shutil.move(str(path), str(target))
            logger.info(f"Intent quarantined: {path.name} -> {target_name}")
        except Exception as e:
            logger.error(f"Failed to quarantine {path}: {e}")

    def _move_processed(self, path: Path) -> None:
        """
        Move processed intent to processed directory.

        Args:
            path: Intent file path
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        target_name = f"{timestamp}_{path.name}"
        target = self._config.processed_dir / target_name

        try:
            shutil.move(str(path), str(target))
        except Exception as e:
            logger.error(f"Failed to move processed {path}: {e}")

    # =========================================================================
    # MAINTENANCE
    # =========================================================================

    def cleanup_old_hashes(self, max_age_hours: int = 24) -> int:
        """
        Clean up old hash entries to prevent memory growth.

        Args:
            max_age_hours: Remove hashes older than this

        Returns:
            Number of entries removed
        """
        from datetime import timedelta

        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
        removed = 0

        with self._hash_lock:
            old_hashes = [h for h, ts in self._processed_hashes.items() if ts < cutoff]
            for h in old_hashes:
                del self._processed_hashes[h]
                removed += 1

        if removed:
            logger.info(f"Cleaned up {removed} old hash entries")

        return removed

    def process_single(self, path: Path) -> RouteResult | None:
        """
        Process a single intent file (for testing).

        Does not move files or update stats.

        Args:
            path: Path to intent file

        Returns:
            RouteResult or None if parse failed
        """
        intent = parse_intent(path)
        if intent is None:
            return None

        return self._router.route(intent)
