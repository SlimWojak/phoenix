"""
Quality Telemetry — Health and quality reporting

VERSION: 0.2
CONTRACT: GOVERNANCE_INTERFACE_CONTRACT.md
"""

from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

from .types import QualityTelemetry, HealthState, LifecycleState


# =============================================================================
# TELEMETRY EMITTER
# =============================================================================

class TelemetryEmitter:
    """
    Emits quality telemetry for a module.
    
    Tracks:
    - data_health: HEALTHY, DEGRADED, CRITICAL
    - lifecycle_state: RUNNING, STOPPING, STOPPED
    - quality_score: 0.0-1.0
    - anomaly/gap counts
    - staleness
    """
    
    # Thresholds
    HEALTHY_THRESHOLD = 0.95
    DEGRADED_THRESHOLD = 0.70
    STALE_THRESHOLD_SECONDS = 60.0
    
    def __init__(self, module_id: str):
        self.module_id = module_id
        self._data_health = HealthState.HEALTHY
        self._lifecycle_state = LifecycleState.RUNNING
        self._quality_score = 1.0
        self._last_update = datetime.now(timezone.utc)
        self._anomaly_count = 0
        self._gap_count = 0
        self._staleness_seconds = 0.0
    
    def update(
        self,
        quality_score: Optional[float] = None,
        anomaly_count: Optional[int] = None,
        gap_count: Optional[int] = None,
        staleness_seconds: Optional[float] = None,
        lifecycle_state: Optional[LifecycleState] = None
    ) -> QualityTelemetry:
        """
        Update telemetry values and emit.
        
        Returns:
            Current QualityTelemetry snapshot
        """
        now = datetime.now(timezone.utc)
        
        if quality_score is not None:
            self._quality_score = max(0.0, min(1.0, quality_score))
        
        if anomaly_count is not None:
            self._anomaly_count = anomaly_count
        
        if gap_count is not None:
            self._gap_count = gap_count
        
        if staleness_seconds is not None:
            self._staleness_seconds = staleness_seconds
        
        if lifecycle_state is not None:
            self._lifecycle_state = lifecycle_state
        
        # Auto-compute data_health from quality_score and staleness
        self._data_health = self._compute_health()
        self._last_update = now
        
        return self.get_telemetry()
    
    def _compute_health(self) -> HealthState:
        """Compute health state from metrics."""
        # Staleness check
        if self._staleness_seconds > self.STALE_THRESHOLD_SECONDS:
            return HealthState.CRITICAL
        
        # Quality score check
        if self._quality_score >= self.HEALTHY_THRESHOLD:
            return HealthState.HEALTHY
        elif self._quality_score >= self.DEGRADED_THRESHOLD:
            return HealthState.DEGRADED
        else:
            return HealthState.CRITICAL
    
    def get_telemetry(self) -> QualityTelemetry:
        """Get current telemetry snapshot."""
        return QualityTelemetry(
            data_health=self._data_health,
            lifecycle_state=self._lifecycle_state,
            quality_score=self._quality_score,
            last_update=self._last_update,
            anomaly_count=self._anomaly_count,
            gap_count=self._gap_count,
            staleness_seconds=self._staleness_seconds
        )
    
    def increment_anomaly(self) -> None:
        """Increment anomaly count."""
        self._anomaly_count += 1
        self._last_update = datetime.now(timezone.utc)
    
    def increment_gap(self) -> None:
        """Increment gap count."""
        self._gap_count += 1
        self._last_update = datetime.now(timezone.utc)
    
    def reset_counters(self) -> None:
        """Reset anomaly and gap counters."""
        self._anomaly_count = 0
        self._gap_count = 0
        self._last_update = datetime.now(timezone.utc)
    
    @property
    def is_healthy(self) -> bool:
        return self._data_health == HealthState.HEALTHY
    
    @property
    def is_critical(self) -> bool:
        return self._data_health == HealthState.CRITICAL


# =============================================================================
# TELEMETRY AGGREGATOR
# =============================================================================

@dataclass
class AggregatedTelemetry:
    """Aggregated telemetry across modules."""
    module_count: int
    healthy_count: int
    degraded_count: int
    critical_count: int
    min_quality_score: float
    avg_quality_score: float
    total_anomalies: int
    total_gaps: int


class TelemetryAggregator:
    """
    Aggregates telemetry across multiple modules.
    """
    
    def __init__(self):
        self._emitters: dict[str, TelemetryEmitter] = {}
    
    def register(self, emitter: TelemetryEmitter) -> None:
        """Register a telemetry emitter."""
        self._emitters[emitter.module_id] = emitter
    
    def deregister(self, module_id: str) -> None:
        """Deregister a telemetry emitter."""
        self._emitters.pop(module_id, None)
    
    def aggregate(self) -> AggregatedTelemetry:
        """Aggregate telemetry from all registered emitters."""
        if not self._emitters:
            return AggregatedTelemetry(
                module_count=0,
                healthy_count=0,
                degraded_count=0,
                critical_count=0,
                min_quality_score=0.0,
                avg_quality_score=0.0,
                total_anomalies=0,
                total_gaps=0
            )
        
        healthy = 0
        degraded = 0
        critical = 0
        scores = []
        anomalies = 0
        gaps = 0
        
        for emitter in self._emitters.values():
            telemetry = emitter.get_telemetry()
            
            if telemetry.data_health == HealthState.HEALTHY:
                healthy += 1
            elif telemetry.data_health == HealthState.DEGRADED:
                degraded += 1
            else:
                critical += 1
            
            scores.append(telemetry.quality_score)
            anomalies += telemetry.anomaly_count
            gaps += telemetry.gap_count
        
        return AggregatedTelemetry(
            module_count=len(self._emitters),
            healthy_count=healthy,
            degraded_count=degraded,
            critical_count=critical,
            min_quality_score=min(scores),
            avg_quality_score=sum(scores) / len(scores),
            total_anomalies=anomalies,
            total_gaps=gaps
        )
