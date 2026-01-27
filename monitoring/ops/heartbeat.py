"""
Heartbeat Daemon — 30s health monitoring with jitter
=====================================================

S33: FIRST_BLOOD

Performs health checks every 30s ±5s with semantic validation.

INVARIANTS:
- INV-OPS-HEARTBEAT-30S-1: Heartbeat every 30s ±5s jitter
- INV-OPS-HEARTBEAT-SEMANTIC-1: Includes semantic health checks
"""

from __future__ import annotations

import logging
import random
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Callable

from .heartbeat_bead import (
    BeadEmitter,
    HealthChecks,
    HealthStatus,
    HeartbeatBeadData,
    HeartbeatBeadEmitter,
)
from .semantic_health import (
    SemanticHealthChecker,
    SemanticHealthConfig,
    SemanticHealthResult,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Alert callback type
AlertCallback = Callable[[str, str, dict[str, Any]], None]


@dataclass
class HeartbeatConfig:
    """
    Heartbeat configuration.

    INVARIANT: INV-OPS-HEARTBEAT-30S-1
    Base interval 30s with ±5s jitter.
    """

    # Timing (INV-OPS-HEARTBEAT-30S-1)
    interval_sec: float = 30.0
    jitter_sec: float = 5.0  # ±5s

    # Miss detection
    miss_threshold: int = 3  # 3 consecutive misses = 90s max blind

    # Semantic health config
    semantic_config: SemanticHealthConfig = field(
        default_factory=SemanticHealthConfig
    )

    def get_next_interval(self) -> float:
        """Get next interval with jitter."""
        jitter = random.uniform(-self.jitter_sec, self.jitter_sec)
        return max(1.0, self.interval_sec + jitter)


@dataclass
class HeartbeatState:
    """Tracks heartbeat state."""

    running: bool = False
    last_beat: datetime | None = None
    consecutive_misses: int = 0
    total_beats: int = 0
    total_misses: int = 0
    total_degraded: int = 0


class Heartbeat:
    """
    Heartbeat daemon for 24/7 health monitoring.

    INVARIANT: INV-OPS-HEARTBEAT-30S-1
    Heartbeat every 30s ±5s jitter.

    INVARIANT: INV-OPS-HEARTBEAT-SEMANTIC-1
    Heartbeat includes semantic health checks.
    """

    def __init__(
        self,
        config: HeartbeatConfig | None = None,
        bead_emitter: BeadEmitter | None = None,
        alert_callback: AlertCallback | None = None,
        ibkr_health_provider: Any = None,
        recon_health_provider: Any = None,
        position_health_provider: Any = None,
    ) -> None:
        """
        Initialize heartbeat daemon.

        Args:
            config: Heartbeat configuration
            bead_emitter: Callback for bead emission
            alert_callback: Callback for alerts
            ibkr_health_provider: IBKR state provider for semantic checks
            recon_health_provider: Reconciliation state provider
            position_health_provider: Position state provider
        """
        self._config = config or HeartbeatConfig()
        self._state = HeartbeatState()

        # Bead emitter
        self._bead_emitter = HeartbeatBeadEmitter(bead_emitter)

        # Alert callback
        self._alert_callback = alert_callback

        # Semantic health checker
        self._semantic_checker = SemanticHealthChecker(
            config=self._config.semantic_config,
            ibkr_provider=ibkr_health_provider,
            recon_provider=recon_health_provider,
            position_provider=position_health_provider,
        )

        # Threading
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def set_bead_emitter(self, emitter: BeadEmitter) -> None:
        """Set bead emission callback."""
        self._bead_emitter.set_emitter(emitter)

    def set_alert_callback(self, callback: AlertCallback) -> None:
        """Set alert callback."""
        self._alert_callback = callback

    def set_ibkr_provider(self, provider: Any) -> None:
        """Set IBKR health provider."""
        self._semantic_checker = SemanticHealthChecker(
            config=self._config.semantic_config,
            ibkr_provider=provider,
            recon_provider=None,
            position_provider=None,
        )

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def start(self) -> None:
        """Start heartbeat daemon in background thread."""
        if self._state.running:
            logger.warning("Heartbeat already running")
            return

        self._stop_event.clear()
        self._state.running = True

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        logger.info(
            f"Heartbeat started: interval={self._config.interval_sec}s "
            f"±{self._config.jitter_sec}s"
        )

    def stop(self) -> None:
        """Stop heartbeat daemon."""
        if not self._state.running:
            return

        self._stop_event.set()
        self._state.running = False

        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

        logger.info("Heartbeat stopped")

    def is_running(self) -> bool:
        """Check if heartbeat is running."""
        return self._state.running

    # =========================================================================
    # MAIN LOOP
    # =========================================================================

    def _run_loop(self) -> None:
        """Main heartbeat loop."""
        while not self._stop_event.is_set():
            try:
                self._beat()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                self._record_miss(f"Heartbeat error: {e}")

            # Wait for next interval with jitter
            interval = self._config.get_next_interval()
            self._stop_event.wait(interval)

    def _beat(self) -> None:
        """Perform single heartbeat."""
        self._state.total_beats += 1
        self._state.last_beat = datetime.now(UTC)

        # Check process health (always true if we're here)
        process_alive = True

        # Check IBKR connection
        ibkr_connected = self._check_ibkr_connected()

        # Run semantic health checks
        semantic_result = self._semantic_checker.check_all()
        semantic_healthy = semantic_result.healthy

        # Create health checks result
        checks = HealthChecks(
            process_alive=process_alive,
            ibkr_connected=ibkr_connected,
            semantic_healthy=semantic_healthy,
        )

        # Determine status and emit bead
        status = checks.get_status()

        if status == HealthStatus.HEALTHY:
            self._record_healthy(checks)
        elif status == HealthStatus.DEGRADED:
            self._record_degraded(checks, semantic_result)
        else:
            self._record_miss("Health check failed")

        logger.debug(
            f"Heartbeat: status={status.value}, "
            f"ibkr={ibkr_connected}, semantic={semantic_healthy}"
        )

    def _check_ibkr_connected(self) -> bool:
        """Check if IBKR is connected."""
        # In real implementation, would check actual connector
        # For now, assume connected unless semantic check says otherwise
        return True

    def _record_healthy(self, checks: HealthChecks) -> None:
        """Record healthy heartbeat."""
        self._state.consecutive_misses = 0
        self._bead_emitter.emit_healthy(checks)

    def _record_degraded(
        self, checks: HealthChecks, semantic: SemanticHealthResult
    ) -> None:
        """Record degraded heartbeat."""
        self._state.total_degraded += 1

        details = semantic.to_dict()
        self._bead_emitter.emit_degraded(checks, details)

        # Alert on degradation
        warnings = semantic.get_warnings()
        criticals = semantic.get_criticals()

        if criticals:
            self._fire_alert(
                "CRITICAL",
                f"Semantic health critical: {len(criticals)} issues",
                details,
            )
        elif warnings:
            self._fire_alert(
                "WARNING",
                f"Semantic health degraded: {len(warnings)} issues",
                details,
            )

    def _record_miss(self, reason: str) -> None:
        """Record missed heartbeat."""
        self._state.consecutive_misses += 1
        self._state.total_misses += 1

        self._bead_emitter.emit_missed(
            details={"reason": reason, "consecutive": self._state.consecutive_misses}
        )

        # Alert on consecutive misses
        if self._state.consecutive_misses >= self._config.miss_threshold:
            self._fire_alert(
                "CRITICAL",
                f"Heartbeat missed {self._state.consecutive_misses} times",
                {
                    "consecutive_misses": self._state.consecutive_misses,
                    "reason": reason,
                },
            )

    def _fire_alert(self, level: str, message: str, details: dict[str, Any]) -> None:
        """Fire alert through callback."""
        if self._alert_callback:
            self._alert_callback(level, message, details)
        else:
            logger.warning(f"ALERT [{level}]: {message}")

    # =========================================================================
    # MANUAL TRIGGER
    # =========================================================================

    def beat_now(self) -> HeartbeatBeadData:
        """
        Trigger immediate heartbeat (for testing).

        Returns:
            Emitted bead data
        """
        self._beat()
        return HeartbeatBeadData(
            status=HealthStatus.HEALTHY,  # Placeholder
        )

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_state(self) -> dict[str, Any]:
        """Get heartbeat state."""
        return {
            "running": self._state.running,
            "last_beat": (
                self._state.last_beat.isoformat() if self._state.last_beat else None
            ),
            "consecutive_misses": self._state.consecutive_misses,
            "total_beats": self._state.total_beats,
            "total_misses": self._state.total_misses,
            "total_degraded": self._state.total_degraded,
            "config": {
                "interval_sec": self._config.interval_sec,
                "jitter_sec": self._config.jitter_sec,
                "miss_threshold": self._config.miss_threshold,
            },
        }
