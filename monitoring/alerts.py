"""
Alert Pipeline — Thresholds, debounce, delivery, auto-halt

VERSION: 2.0
SPRINT: S28.D

THRESHOLDS:
- halt > 10ms → WARN
- halt > 50ms → CRITICAL
- quality < 0.8 → WARN
- worker death → CRITICAL
- no heartbeat > 30s → WARN

DEBOUNCE:
- Same alert class: suppress for 60s
- Prevents alert fatigue

AUTO-HALT ESCALATION (S28.D):
- >3 CRITICAL alerts in 300s → auto halt
- Emits AUTO_HALT_TRIGGERED bead

BEAD EMISSION (S28.D):
- All CRITICAL alerts emit VIOLATION beads
- Enables audit trail and boardroom visibility
"""

import logging
import time
import hashlib
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


# =============================================================================
# ALERT TYPES
# =============================================================================

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARN = "warn"
    CRITICAL = "critical"


class AlertClass(Enum):
    """Alert classification for debounce grouping."""
    HALT_LATENCY = "halt_latency"
    QUALITY_DEGRADED = "quality_degraded"
    WORKER_DEATH = "worker_death"
    HEARTBEAT_STALE = "heartbeat_stale"
    BOUNDS_VIOLATION = "bounds_violation"
    CHAOS_FAILURE = "chaos_failure"


@dataclass
class Alert:
    """Alert event."""
    alert_class: AlertClass
    level: AlertLevel
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "class": self.alert_class.value,
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


# =============================================================================
# ALERT THRESHOLDS
# =============================================================================

@dataclass
class AlertThreshold:
    """Threshold configuration for an alert class."""
    warn_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison: str = "gt"  # gt (greater than) or lt (less than)


DEFAULT_THRESHOLDS = {
    AlertClass.HALT_LATENCY: AlertThreshold(
        warn_threshold=10.0,      # > 10ms
        critical_threshold=50.0,  # > 50ms
        comparison="gt"
    ),
    AlertClass.QUALITY_DEGRADED: AlertThreshold(
        warn_threshold=0.8,       # < 0.8
        critical_threshold=0.5,   # < 0.5
        comparison="lt"
    ),
    AlertClass.HEARTBEAT_STALE: AlertThreshold(
        warn_threshold=30.0,      # > 30s
        critical_threshold=60.0,  # > 60s
        comparison="gt"
    ),
}


# =============================================================================
# ALERT MANAGER
# =============================================================================

class AlertManager:
    """
    Manages alert lifecycle with debounce and auto-halt escalation.
    
    DEBOUNCE LOGIC:
    - Track last alert time per (alert_class, source_id)
    - Suppress duplicates within debounce_seconds
    - Always allow CRITICAL to override WARN
    
    AUTO-HALT ESCALATION (S28.D):
    - Track CRITICAL alerts in sliding window
    - >3 CRITICAL in 300s → trigger auto halt
    - Emit AUTO_HALT_TRIGGERED bead
    
    BEAD EMISSION (S28.D):
    - All CRITICAL alerts emit VIOLATION beads
    - Beads logged to telemetry and optionally boardroom
    """
    
    DEFAULT_DEBOUNCE_SECONDS = 60.0
    AUTO_HALT_WINDOW_SECONDS = 300.0
    AUTO_HALT_THRESHOLD = 3
    
    def __init__(
        self,
        debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
        thresholds: Optional[Dict[AlertClass, AlertThreshold]] = None,
        halt_callback: Optional[Callable[[str], None]] = None,
        bead_callback: Optional[Callable[[Dict], None]] = None
    ):
        self.debounce_seconds = debounce_seconds
        self.thresholds = thresholds or DEFAULT_THRESHOLDS
        
        # Debounce tracking: (alert_class, source_id) -> last_alert_time
        self._last_alert_time: Dict[tuple, float] = {}
        self._last_alert_level: Dict[tuple, AlertLevel] = {}
        
        # Alert history
        self._alerts: List[Alert] = []
        self._suppressed_count: int = 0
        
        # Callbacks
        self._callbacks: List[Callable[[Alert], None]] = []
        
        # S28.D: Auto-halt escalation
        self._halt_callback = halt_callback
        self._critical_timestamps: deque = deque()  # Track CRITICAL times
        self._auto_halt_triggered = False
        
        # S28.D: Bead emission
        self._bead_callback = bead_callback
        self._beads_emitted: List[Dict] = []
    
    def register_callback(self, callback: Callable[[Alert], None]) -> None:
        """Register callback to receive alerts."""
        self._callbacks.append(callback)
    
    def check_threshold(
        self,
        alert_class: AlertClass,
        value: float,
        source_id: str = "default",
        metadata: Optional[Dict] = None
    ) -> Optional[Alert]:
        """
        Check value against thresholds and emit alert if exceeded.
        
        Returns:
            Alert if emitted, None if suppressed or within threshold
        """
        threshold = self.thresholds.get(alert_class)
        if not threshold:
            return None
        
        level = None
        
        if threshold.comparison == "gt":
            if threshold.critical_threshold and value > threshold.critical_threshold:
                level = AlertLevel.CRITICAL
            elif threshold.warn_threshold and value > threshold.warn_threshold:
                level = AlertLevel.WARN
        else:  # lt
            if threshold.critical_threshold and value < threshold.critical_threshold:
                level = AlertLevel.CRITICAL
            elif threshold.warn_threshold and value < threshold.warn_threshold:
                level = AlertLevel.WARN
        
        if level is None:
            return None
        
        message = f"{alert_class.value}: {value} ({'>' if threshold.comparison == 'gt' else '<'} threshold)"
        return self.emit(alert_class, level, message, source_id, metadata or {"value": value})
    
    def emit(
        self,
        alert_class: AlertClass,
        level: AlertLevel,
        message: str,
        source_id: str = "default",
        metadata: Optional[Dict] = None
    ) -> Optional[Alert]:
        """
        Emit an alert with debounce logic.
        
        Returns:
            Alert if emitted, None if suppressed by debounce
        """
        key = (alert_class, source_id)
        now = time.time()
        
        # Check debounce
        last_time = self._last_alert_time.get(key, 0)
        last_level = self._last_alert_level.get(key)
        
        time_since_last = now - last_time
        
        # Debounce logic:
        # - Suppress if same class within debounce window
        # - EXCEPT: allow CRITICAL to override WARN
        should_suppress = (
            time_since_last < self.debounce_seconds
            and not (level == AlertLevel.CRITICAL and last_level == AlertLevel.WARN)
        )
        
        if should_suppress:
            self._suppressed_count += 1
            logger.debug(f"Alert suppressed (debounce): {alert_class.value} from {source_id}")
            return None
        
        # Create and emit alert
        alert = Alert(
            alert_class=alert_class,
            level=level,
            message=message,
            metadata=metadata or {}
        )
        
        self._last_alert_time[key] = now
        self._last_alert_level[key] = level
        self._alerts.append(alert)
        
        # Log
        log_level = logging.WARNING if level == AlertLevel.WARN else logging.ERROR
        logger.log(log_level, f"ALERT [{level.value}] {message}")
        
        # S28.D: Emit bead for CRITICAL alerts
        if level == AlertLevel.CRITICAL:
            self._emit_violation_bead(alert)
            self._check_auto_halt_escalation()
        
        # Callbacks
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        return alert
    
    def _emit_violation_bead(self, alert: Alert) -> Dict:
        """
        Emit VIOLATION bead for CRITICAL alert.
        
        S28.D: All CRITICAL alerts → bead emission.
        """
        now = datetime.now(timezone.utc)
        
        bead = {
            "bead_id": f"BEAD-VIOL-{now.strftime('%Y%m%d%H%M%S')}-{len(self._beads_emitted):04d}",
            "bead_type": "VIOLATION",
            "timestamp": now.isoformat(),
            "source_module": "monitoring.alerts",
            "alert_class": alert.alert_class.value,
            "alert_level": alert.level.value,
            "message": alert.message,
            "metadata": alert.metadata,
            "state_hash": self._compute_alert_hash(alert),
        }
        
        self._beads_emitted.append(bead)
        logger.info(f"BEAD emitted: {bead['bead_id']} ({alert.alert_class.value})")
        
        # Invoke bead callback if registered
        if self._bead_callback:
            try:
                self._bead_callback(bead)
            except Exception as e:
                logger.error(f"Bead callback error: {e}")
        
        return bead
    
    def _compute_alert_hash(self, alert: Alert) -> str:
        """Compute deterministic hash of alert."""
        hashable = {
            "class": alert.alert_class.value,
            "level": alert.level.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
        }
        canonical = json.dumps(hashable, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]
    
    def _check_auto_halt_escalation(self) -> None:
        """
        Check if auto-halt should be triggered.
        
        S28.D: >3 CRITICAL alerts in 300s → auto halt.
        """
        if self._auto_halt_triggered:
            return  # Already halted
        
        now = time.time()
        cutoff = now - self.AUTO_HALT_WINDOW_SECONDS
        
        # Add current CRITICAL timestamp
        self._critical_timestamps.append(now)
        
        # Remove old timestamps outside window
        while self._critical_timestamps and self._critical_timestamps[0] < cutoff:
            self._critical_timestamps.popleft()
        
        # Check threshold
        if len(self._critical_timestamps) > self.AUTO_HALT_THRESHOLD:
            self._trigger_auto_halt()
    
    def _trigger_auto_halt(self) -> None:
        """
        Trigger automatic halt due to repeated CRITICAL alerts.
        
        S28.D: Invoke halt callback and emit AUTO_HALT_TRIGGERED bead.
        """
        self._auto_halt_triggered = True
        halt_reason = f"AUTO_HALT: >{self.AUTO_HALT_THRESHOLD} CRITICAL alerts in {self.AUTO_HALT_WINDOW_SECONDS}s"
        
        logger.critical(halt_reason)
        
        # Emit AUTO_HALT bead
        now = datetime.now(timezone.utc)
        bead = {
            "bead_id": f"BEAD-HALT-{now.strftime('%Y%m%d%H%M%S')}-AUTO",
            "bead_type": "AUTO_HALT_TRIGGERED",
            "timestamp": now.isoformat(),
            "source_module": "monitoring.alerts",
            "reason": halt_reason,
            "critical_count": len(self._critical_timestamps),
            "window_seconds": self.AUTO_HALT_WINDOW_SECONDS,
        }
        self._beads_emitted.append(bead)
        
        if self._bead_callback:
            try:
                self._bead_callback(bead)
            except Exception as e:
                logger.error(f"Bead callback error: {e}")
        
        # Invoke halt callback
        if self._halt_callback:
            try:
                self._halt_callback(halt_reason)
            except Exception as e:
                logger.error(f"Halt callback error: {e}")
    
    def reset_auto_halt(self) -> None:
        """Reset auto-halt state (for testing or recovery)."""
        self._auto_halt_triggered = False
        self._critical_timestamps.clear()
    
    def emit_halt_violation(self, latency_ms: float, source_id: str = "halt") -> Optional[Alert]:
        """Emit halt latency violation alert."""
        return self.check_threshold(
            AlertClass.HALT_LATENCY,
            latency_ms,
            source_id,
            {"latency_ms": latency_ms}
        )
    
    def emit_quality_degraded(self, quality: float, source_id: str = "river") -> Optional[Alert]:
        """Emit quality degradation alert."""
        return self.check_threshold(
            AlertClass.QUALITY_DEGRADED,
            quality,
            source_id,
            {"quality_score": quality}
        )
    
    def emit_worker_death(self, worker_id: str, reason: str = "unknown") -> Optional[Alert]:
        """Emit worker death alert (always CRITICAL, no debounce on different workers)."""
        return self.emit(
            AlertClass.WORKER_DEATH,
            AlertLevel.CRITICAL,
            f"Worker {worker_id} died: {reason}",
            source_id=worker_id,
            metadata={"worker_id": worker_id, "reason": reason}
        )
    
    def emit_heartbeat_stale(self, worker_id: str, seconds_stale: float) -> Optional[Alert]:
        """Emit heartbeat staleness alert."""
        return self.check_threshold(
            AlertClass.HEARTBEAT_STALE,
            seconds_stale,
            source_id=worker_id,
            metadata={"worker_id": worker_id, "seconds_stale": seconds_stale}
        )
    
    def emit_bounds_violation(self, violation_type: str, value: float, threshold: float) -> Optional[Alert]:
        """Emit bounds violation alert (from Track A)."""
        return self.emit(
            AlertClass.BOUNDS_VIOLATION,
            AlertLevel.CRITICAL,
            f"Bounds violation: {violation_type} = {value} (threshold: {threshold})",
            source_id="bounds_check",
            metadata={"type": violation_type, "value": value, "threshold": threshold}
        )
    
    def get_recent_alerts(self, limit: int = 50) -> List[Alert]:
        """Get recent alerts."""
        return self._alerts[-limit:]
    
    def get_stats(self) -> Dict:
        """Get alert statistics."""
        recent = self._alerts[-100:] if self._alerts else []
        
        by_level = defaultdict(int)
        by_class = defaultdict(int)
        
        for alert in recent:
            by_level[alert.level.value] += 1
            by_class[alert.alert_class.value] += 1
        
        return {
            "total_alerts": len(self._alerts),
            "suppressed_count": self._suppressed_count,
            "recent_100": {
                "by_level": dict(by_level),
                "by_class": dict(by_class),
            },
            "debounce_seconds": self.debounce_seconds,
            # S28.D additions
            "beads_emitted": len(self._beads_emitted),
            "critical_in_window": len(self._critical_timestamps),
            "auto_halt_triggered": self._auto_halt_triggered,
        }
    
    def get_beads(self) -> List[Dict]:
        """Get all emitted beads."""
        return self._beads_emitted.copy()
    
    def is_auto_halted(self) -> bool:
        """Check if auto-halt has been triggered."""
        return self._auto_halt_triggered
    
    def clear_history(self) -> None:
        """Clear alert history (for testing)."""
        self._alerts.clear()
        self._suppressed_count = 0
        self._last_alert_time.clear()
        self._last_alert_level.clear()


# =============================================================================
# SINGLETON FOR GLOBAL ACCESS
# =============================================================================

_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
