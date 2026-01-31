"""
Alert Taxonomy — S41 Track C
============================

Unified alert classification for glanceable Telegram notifications.

TAXONOMY:
  CRITICAL: Requires immediate action (halt, T2 blocked, supervisor dead)
  WARNING:  Degraded state, attention needed (circuit open, reconnecting)
  INFO:     State change, no action required (heartbeat ok, trade executed)

INVARIANTS:
  INV-ALERT-TAXONOMY-1: All alerts have explicit severity
  INV-ALERT-TAXONOMY-2: Deduplication ≤5 per 60s window per category
  INV-ALERT-TAXONOMY-3: Telegram format matches severity (emoji + layout)
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

# =============================================================================
# SEVERITY ENUM
# =============================================================================


class AlertSeverity(str, Enum):
    """
    Alert severity levels.

    Determines urgency, formatting, and deduplication window.
    """

    CRITICAL = "CRITICAL"  # Immediate action required
    WARNING = "WARNING"  # Attention needed
    INFO = "INFO"  # Informational


# =============================================================================
# ALERT CATEGORIES
# =============================================================================


class AlertCategory(str, Enum):
    """Alert categories for classification and deduplication."""

    # System Health
    HALT = "HALT"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    HEALTH_FSM = "HEALTH_FSM"

    # IBKR
    IBKR_CONNECTION = "IBKR_CONNECTION"
    IBKR_DEGRADATION = "IBKR_DEGRADATION"
    SUPERVISOR = "SUPERVISOR"

    # Trading
    TRADE = "TRADE"
    POSITION = "POSITION"

    # Constitutional
    CONSTITUTIONAL_VIOLATION = "CONSTITUTIONAL_VIOLATION"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"

    # General
    SYSTEM = "SYSTEM"
    TEST = "TEST"


# =============================================================================
# ALERT DATACLASS
# =============================================================================


@dataclass
class Alert:
    """
    Unified alert with explicit taxonomy.

    All alerts must have severity and category.
    No ambiguous alerts allowed.
    """

    severity: AlertSeverity
    category: AlertCategory
    title: str
    message: str
    component: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)

    # Deduplication key (auto-generated if not provided)
    dedup_key: str = ""

    def __post_init__(self):
        if not self.dedup_key:
            self.dedup_key = f"{self.category.value}:{self.component}:{self.title}"


# =============================================================================
# SEVERITY MAPPING (for health FSM integration)
# =============================================================================


# Map health states to alert severity
HEALTH_STATE_SEVERITY = {
    "HEALTHY": AlertSeverity.INFO,
    "DEGRADED": AlertSeverity.WARNING,
    "CRITICAL": AlertSeverity.CRITICAL,
    "HALTED": AlertSeverity.CRITICAL,
}

# Map circuit breaker states to alert severity
CIRCUIT_STATE_SEVERITY = {
    "CLOSED": AlertSeverity.INFO,
    "OPEN": AlertSeverity.WARNING,
    "HALF_OPEN": AlertSeverity.INFO,
}


# =============================================================================
# ALERT DEDUPLICATION
# =============================================================================


@dataclass
class DeduplicationWindow:
    """Tracks alerts for deduplication."""

    alerts: list[float] = field(default_factory=list)
    last_sent: float = 0.0

    def should_send(self, window_seconds: float, max_count: int) -> bool:
        """Check if alert should be sent (not deduplicated)."""
        now = time.time()

        # Clean old alerts outside window
        cutoff = now - window_seconds
        self.alerts = [t for t in self.alerts if t > cutoff]

        # Check count in window
        if len(self.alerts) >= max_count:
            return False

        return True

    def record(self) -> None:
        """Record alert sent."""
        now = time.time()
        self.alerts.append(now)
        self.last_sent = now


class AlertDeduplicator:
    """
    Deduplicates alerts within time windows.

    INV-ALERT-TAXONOMY-2: ≤5 per 60s window per category
    """

    # Window settings by severity
    WINDOW_SECONDS = {
        AlertSeverity.CRITICAL: 30.0,  # Criticals: 30s window
        AlertSeverity.WARNING: 60.0,  # Warnings: 60s window
        AlertSeverity.INFO: 300.0,  # Info: 5 min window
    }

    MAX_IN_WINDOW = {
        AlertSeverity.CRITICAL: 10,  # Allow more criticals
        AlertSeverity.WARNING: 5,  # 5 per window
        AlertSeverity.INFO: 3,  # Fewer info alerts
    }

    def __init__(self):
        self._windows: dict[str, DeduplicationWindow] = defaultdict(DeduplicationWindow)
        self._total_sent = 0
        self._total_deduplicated = 0

    def should_send(self, alert: Alert) -> bool:
        """
        Check if alert should be sent.

        Returns True if not deduplicated, False if suppressed.
        """
        window = self._windows[alert.dedup_key]
        window_seconds = self.WINDOW_SECONDS.get(alert.severity, 60.0)
        max_count = self.MAX_IN_WINDOW.get(alert.severity, 5)

        return window.should_send(window_seconds, max_count)

    def record_sent(self, alert: Alert) -> None:
        """Record that alert was sent."""
        window = self._windows[alert.dedup_key]
        window.record()
        self._total_sent += 1

    def record_deduplicated(self, alert: Alert) -> None:
        """Record that alert was deduplicated (not sent)."""
        self._total_deduplicated += 1

    @property
    def stats(self) -> dict:
        """Get deduplication stats."""
        return {
            "total_sent": self._total_sent,
            "total_deduplicated": self._total_deduplicated,
            "active_windows": len(self._windows),
        }


# =============================================================================
# TELEGRAM FORMATTER
# =============================================================================


class TelegramAlertFormatter:
    """
    Formats alerts for Telegram with severity-appropriate styling.

    INV-ALERT-TAXONOMY-3: Format matches severity
    S41 Phase 2E: One-liner format (≤60 chars) with emoji prefix
    """

    # Emoji by severity (S41 Phase 2E: 🔴🟡🟢)
    SEVERITY_EMOJI = {
        AlertSeverity.CRITICAL: "🔴",
        AlertSeverity.WARNING: "🟡",
        AlertSeverity.INFO: "🟢",
    }

    # Legacy emoji (for full format)
    SEVERITY_EMOJI_FULL = {
        AlertSeverity.CRITICAL: "🚨",
        AlertSeverity.WARNING: "⚠️",
        AlertSeverity.INFO: "ℹ️",
    }

    # Header format by severity
    SEVERITY_HEADER = {
        AlertSeverity.CRITICAL: "🚨 <b>CRITICAL ALERT</b> 🚨",
        AlertSeverity.WARNING: "⚠️ <b>WARNING</b>",
        AlertSeverity.INFO: "ℹ️ <b>INFO</b>",
    }

    # Category emoji
    CATEGORY_EMOJI = {
        AlertCategory.HALT: "🛑",
        AlertCategory.CIRCUIT_BREAKER: "⚡",
        AlertCategory.HEALTH_FSM: "💚",
        AlertCategory.IBKR_CONNECTION: "🔌",
        AlertCategory.IBKR_DEGRADATION: "📉",
        AlertCategory.SUPERVISOR: "👁️",
        AlertCategory.TRADE: "💰",
        AlertCategory.POSITION: "📊",
        AlertCategory.CONSTITUTIONAL_VIOLATION: "⚖️",
        AlertCategory.PROVENANCE_MISSING: "🔗",
        AlertCategory.SYSTEM: "🖥️",
        AlertCategory.TEST: "🧪",
    }

    def format_oneliner(self, alert: Alert) -> str:
        """
        Format alert as one-liner (≤60 chars).

        S41 Phase 2E: Glanceable format with severity emoji.
        Format: {emoji} {component} — {title}

        Args:
            alert: Alert to format

        Returns:
            One-liner string ≤60 chars
        """
        emoji = self.SEVERITY_EMOJI.get(alert.severity, "⚪")
        component = alert.component.upper() if alert.component else "SYSTEM"
        title = alert.title

        # Base format
        base = f"{emoji} {component} — {title}"

        # Truncate if needed
        if len(base) > 60:
            # Truncate title to fit
            max_title = 60 - len(f"{emoji} {component} — ...") - 3
            if max_title > 5:
                title = title[:max_title] + "..."
                base = f"{emoji} {component} — {title}"
            else:
                base = base[:57] + "..."

        return base

    def format(self, alert: Alert, oneliner: bool = False) -> str:
        """
        Format alert for Telegram.

        Args:
            alert: Alert to format
            oneliner: If True, use compact one-liner format

        Returns:
            HTML-formatted string.
        """
        if oneliner:
            return self.format_oneliner(alert)

        header = self.SEVERITY_HEADER.get(alert.severity, "📢 <b>ALERT</b>")
        category_emoji = self.CATEGORY_EMOJI.get(alert.category, "📌")
        timestamp = alert.timestamp.strftime("%H:%M:%S UTC")

        # Build message
        lines = [
            header,
            "",
            f"{category_emoji} <b>{alert.title}</b>",
        ]

        if alert.component:
            lines.append(f"<b>Component:</b> <code>{alert.component}</code>")

        lines.append("")
        lines.append(alert.message)

        # Add metadata if present
        if alert.metadata:
            lines.append("")
            lines.append("<b>Details:</b>")
            for key, value in alert.metadata.items():
                lines.append(f"• {key}: <code>{value}</code>")

        # Footer
        lines.append("")
        lines.append(f"<i>{timestamp}</i>")

        return "\n".join(lines)

    def format_batch(self, alerts: list[Alert]) -> str:
        """
        Format batch of alerts (same severity assumed).

        Used for aggregated notifications.
        """
        if not alerts:
            return ""

        # Use severity from first alert
        severity = alerts[0].severity
        header = self.SEVERITY_HEADER.get(severity, "📢 <b>ALERTS</b>")
        timestamp = datetime.now(UTC).strftime("%H:%M:%S UTC")

        lines = [
            f"{header} ({len(alerts)} alerts)",
            "",
        ]

        for alert in alerts[:10]:  # Max 10 in batch
            category_emoji = self.CATEGORY_EMOJI.get(alert.category, "📌")
            lines.append(f"{category_emoji} {alert.title}")
            if alert.component:
                lines.append(f"   └─ {alert.component}: {alert.message[:50]}")
            lines.append("")

        if len(alerts) > 10:
            lines.append(f"<i>...and {len(alerts) - 10} more</i>")

        lines.append(f"<i>{timestamp}</i>")

        return "\n".join(lines)


# =============================================================================
# ALERT ROUTER
# =============================================================================


class AlertRouter:
    """
    Routes alerts through deduplication and formatting to handlers.

    Usage:
        router = AlertRouter()
        router.add_handler(my_telegram_handler)

        alert = Alert(
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.HALT,
            title="System Halted",
            message="Emergency halt triggered",
            component="governance",
        )
        router.route(alert)
    """

    def __init__(self):
        self._deduplicator = AlertDeduplicator()
        self._formatter = TelegramAlertFormatter()
        self._handlers: list[Callable[[str, AlertSeverity], None]] = []
        self._alerts_routed = 0
        self._alerts_suppressed = 0

    def add_handler(self, handler: Callable[[str, AlertSeverity], None]) -> None:
        """Add alert handler (receives formatted message + severity)."""
        self._handlers.append(handler)

    def route(self, alert: Alert) -> bool:
        """
        Route alert through pipeline.

        Returns True if alert was sent, False if deduplicated.
        """
        # Check deduplication
        if not self._deduplicator.should_send(alert):
            self._deduplicator.record_deduplicated(alert)
            self._alerts_suppressed += 1
            return False

        # Format
        formatted = self._formatter.format(alert)

        # Send to handlers
        for handler in self._handlers:
            try:
                handler(formatted, alert.severity)
            except Exception:
                pass  # Don't crash on handler failure

        # Record
        self._deduplicator.record_sent(alert)
        self._alerts_routed += 1

        return True

    @property
    def stats(self) -> dict:
        """Get routing stats."""
        return {
            "alerts_routed": self._alerts_routed,
            "alerts_suppressed": self._alerts_suppressed,
            **self._deduplicator.stats,
        }


# =============================================================================
# FACTORY FUNCTIONS (for integration)
# =============================================================================


def create_halt_alert(component: str, reason: str) -> Alert:
    """Create halt alert."""
    return Alert(
        severity=AlertSeverity.CRITICAL,
        category=AlertCategory.HALT,
        title="SYSTEM HALTED",
        message=reason,
        component=component,
    )


def create_circuit_open_alert(circuit_name: str, failure_count: int) -> Alert:
    """Create circuit breaker open alert."""
    return Alert(
        severity=AlertSeverity.WARNING,
        category=AlertCategory.CIRCUIT_BREAKER,
        title="Circuit Breaker OPEN",
        message=f"Circuit opened after {failure_count} failures",
        component=circuit_name,
        metadata={"failure_count": failure_count},
    )


def create_health_transition_alert(
    component: str,
    old_state: str,
    new_state: str,
) -> Alert:
    """Create health state transition alert."""
    severity = HEALTH_STATE_SEVERITY.get(new_state, AlertSeverity.INFO)
    return Alert(
        severity=severity,
        category=AlertCategory.HEALTH_FSM,
        title=f"Health: {new_state}",
        message=f"Transitioned from {old_state} to {new_state}",
        component=component,
        metadata={"old_state": old_state, "new_state": new_state},
    )


def create_ibkr_connection_alert(status: str, reason: str = "") -> Alert:
    """Create IBKR connection alert."""
    severity = AlertSeverity.CRITICAL if status == "DISCONNECTED" else AlertSeverity.INFO
    return Alert(
        severity=severity,
        category=AlertCategory.IBKR_CONNECTION,
        title=f"IBKR {status}",
        message=reason or f"Connection status: {status}",
        component="ibkr",
    )


def create_supervisor_alert(status: str, reason: str = "") -> Alert:
    """Create supervisor alert."""
    severity = AlertSeverity.CRITICAL if status == "DEAD" else AlertSeverity.INFO
    return Alert(
        severity=severity,
        category=AlertCategory.SUPERVISOR,
        title=f"Supervisor {status}",
        message=reason or f"Supervisor status: {status}",
        component="supervisor",
    )


def create_constitutional_violation_alert(
    violation_type: str,
    context: str,
    details: str,
) -> Alert:
    """Create constitutional violation alert."""
    return Alert(
        severity=AlertSeverity.CRITICAL,
        category=AlertCategory.CONSTITUTIONAL_VIOLATION,
        title=f"Constitutional Violation: {violation_type}",
        message=details,
        component=context,
        metadata={"violation_type": violation_type},
    )


# =============================================================================
# S43 ALERT BUNDLER
# =============================================================================


# Types that BYPASS bundling — always emit immediately
UNBUNDLABLE_SEVERITIES = {AlertSeverity.CRITICAL}
UNBUNDLABLE_CATEGORIES = {AlertCategory.HALT, AlertCategory.SUPERVISOR}


class AlertBundler:
    """
    S43: Bundle alerts to prevent storms during multi-failure scenarios.

    CRITICAL/HALT alerts BYPASS bundling and emit immediately.
    Other alerts are bundled within a configurable time window.
    >5 alerts in window → single MULTI_DEGRADED alert.

    INV-ALERT-TAXONOMY-2 enhanced: configurable window, bypass for critical.
    """

    def __init__(self, window_seconds: int = 1800):  # 30min default
        """
        Initialize bundler.

        Args:
            window_seconds: Bundling window in seconds (default 1800 = 30min).
                           Configurable via config.notification.bundle_window_seconds
        """
        self.window_seconds = window_seconds
        self._pending: dict[str, list[Alert]] = defaultdict(list)
        self._window_start: dict[str, float] = {}
        self._multi_degraded_emitted: set[str] = set()
        self._stats = {
            "total_received": 0,
            "total_bypassed": 0,
            "total_bundled": 0,
            "multi_degraded_emitted": 0,
        }

    def _should_bypass(self, alert: Alert) -> bool:
        """Check if alert should bypass bundling."""
        return alert.severity in UNBUNDLABLE_SEVERITIES or alert.category in UNBUNDLABLE_CATEGORIES

    def _get_bundle_key(self, alert: Alert) -> str:
        """Get bundle key for alert grouping."""
        return f"{alert.category.value}:{alert.component}"

    def _check_window_expired(self, bundle_key: str) -> bool:
        """Check if bundle window has expired."""
        if bundle_key not in self._window_start:
            return True
        return time.time() - self._window_start[bundle_key] > self.window_seconds

    def submit(self, alert: Alert) -> Alert | None:
        """
        Submit alert for bundling.

        Returns:
            - The alert if it should be emitted immediately (bypass or new)
            - A MULTI_DEGRADED alert if bundle threshold reached
            - None if alert is bundled (no emit yet)
        """
        self._stats["total_received"] += 1

        # CRITICAL/HALT bypass bundling — emit immediately
        if self._should_bypass(alert):
            self._stats["total_bypassed"] += 1
            return alert

        bundle_key = self._get_bundle_key(alert)

        # Check if window expired — reset bundle
        if self._check_window_expired(bundle_key):
            self._pending[bundle_key] = []
            self._window_start[bundle_key] = time.time()
            self._multi_degraded_emitted.discard(bundle_key)

        # Add to pending bundle
        self._pending[bundle_key].append(alert)
        self._stats["total_bundled"] += 1

        # Check threshold (>5 alerts → MULTI_DEGRADED)
        if len(self._pending[bundle_key]) > 5:
            # Only emit MULTI_DEGRADED once per window
            if bundle_key not in self._multi_degraded_emitted:
                self._multi_degraded_emitted.add(bundle_key)
                self._stats["multi_degraded_emitted"] += 1
                return self._create_multi_degraded(bundle_key)

        # First alert in bundle — emit normally
        if len(self._pending[bundle_key]) == 1:
            return alert

        # Otherwise, bundled — no emit
        return None

    def _create_multi_degraded(self, bundle_key: str) -> Alert:
        """Create MULTI_DEGRADED summary alert."""
        alerts = self._pending.get(bundle_key, [])
        count = len(alerts)
        components = set(a.component for a in alerts if a.component)
        categories = set(a.category.value for a in alerts)

        return Alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.SYSTEM,
            title="MULTI_DEGRADED",
            message=f"{count} alerts in {self.window_seconds//60}min window",
            component=",".join(components) or "multiple",
            metadata={
                "alert_count": count,
                "categories": list(categories),
                "bundle_key": bundle_key,
            },
        )

    def flush(self) -> list[Alert]:
        """Flush all pending bundles (for shutdown or manual emit)."""
        result = []
        for alerts in self._pending.values():
            if alerts:
                # Return summary for bundles with multiple alerts
                if len(alerts) > 1:
                    result.append(self._create_multi_degraded(self._get_bundle_key(alerts[0])))
                else:
                    result.append(alerts[0])
        self._pending.clear()
        self._window_start.clear()
        self._multi_degraded_emitted.clear()
        return result

    @property
    def stats(self) -> dict:
        """Get bundler statistics."""
        return {
            **self._stats,
            "pending_bundles": len(self._pending),
            "window_seconds": self.window_seconds,
        }
