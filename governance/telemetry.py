"""
Quality Telemetry — Health and quality reporting

VERSION: 0.3 (S28.B expansion)
CONTRACT: GOVERNANCE_INTERFACE_CONTRACT.md

EXPANSION (S28.B):
- cascade timing histogram
- signal generation rate (stub for CSO)
- bounds violation counter (from Track A fix)
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from .types import HealthState, LifecycleState, QualityTelemetry

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
        self._last_update = datetime.now(UTC)
        self._anomaly_count = 0
        self._gap_count = 0
        self._staleness_seconds = 0.0

    def update(
        self,
        quality_score: float | None = None,
        anomaly_count: int | None = None,
        gap_count: int | None = None,
        staleness_seconds: float | None = None,
        lifecycle_state: LifecycleState | None = None,
    ) -> QualityTelemetry:
        """
        Update telemetry values and emit.

        Returns:
            Current QualityTelemetry snapshot
        """
        now = datetime.now(UTC)

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
            staleness_seconds=self._staleness_seconds,
        )

    def increment_anomaly(self) -> None:
        """Increment anomaly count."""
        self._anomaly_count += 1
        self._last_update = datetime.now(UTC)

    def increment_gap(self) -> None:
        """Increment gap count."""
        self._gap_count += 1
        self._last_update = datetime.now(UTC)

    def reset_counters(self) -> None:
        """Reset anomaly and gap counters."""
        self._anomaly_count = 0
        self._gap_count = 0
        self._last_update = datetime.now(UTC)

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
                total_gaps=0,
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
            total_gaps=gaps,
        )


# =============================================================================
# EXPANDED TELEMETRY (S28.B)
# =============================================================================


@dataclass
class CascadeTimingTelemetry:
    """Cascade timing histogram for halt propagation."""

    samples: list[float] = field(default_factory=list)
    p50_ms: float = 0.0
    p99_ms: float = 0.0
    max_ms: float = 0.0
    sample_count: int = 0
    slo_violations: int = 0  # > 500ms (INV-HALT-2)

    def record(self, timing_ms: float, slo_threshold_ms: float = 500.0) -> None:
        """Record cascade timing sample."""
        self.samples.append(timing_ms)
        self.sample_count += 1

        if timing_ms > slo_threshold_ms:
            self.slo_violations += 1

        # Keep last 1000 samples
        if len(self.samples) > 1000:
            self.samples = self.samples[-1000:]

        # Update percentiles
        if self.samples:
            sorted_s = sorted(self.samples)
            self.p50_ms = sorted_s[int(len(sorted_s) * 0.50)]
            self.p99_ms = sorted_s[int(len(sorted_s) * 0.99)]
            self.max_ms = max(self.samples)


@dataclass
class SignalGenerationTelemetry:
    """Signal generation rate tracking (stub for CSO)."""

    total_signals: int = 0
    rate_per_minute: float = 0.0
    last_signal_time: datetime | None = None
    window_signals: int = 0
    window_start: datetime | None = None

    def record_signal(self) -> None:
        """Record a signal generation event."""
        now = datetime.now(UTC)
        self.total_signals += 1
        self.last_signal_time = now

        # Rolling 1-minute window for rate calculation
        if self.window_start is None:
            self.window_start = now
            self.window_signals = 1
        elif (now - self.window_start).total_seconds() > 60:
            self.rate_per_minute = self.window_signals
            self.window_start = now
            self.window_signals = 1
        else:
            self.window_signals += 1


@dataclass
class BoundsViolationTelemetry:
    """Bounds violation tracking (from Track A fix)."""

    total_violations: int = 0
    violations_by_type: dict[str, int] = field(default_factory=dict)
    last_violation_time: datetime | None = None
    last_violation_type: str | None = None

    def record_violation(self, violation_type: str) -> None:
        """Record a bounds violation."""
        self.total_violations += 1
        self.violations_by_type[violation_type] = self.violations_by_type.get(violation_type, 0) + 1
        self.last_violation_time = datetime.now(UTC)
        self.last_violation_type = violation_type


class ExtendedTelemetryEmitter(TelemetryEmitter):
    """
    Extended telemetry emitter with S28.B metrics.

    Adds:
    - cascade_timing: Halt propagation timing histogram
    - signal_generation: CSO signal rate (stub)
    - bounds_violations: Data bounds violations
    """

    def __init__(self, module_id: str):
        super().__init__(module_id)
        self.cascade_timing = CascadeTimingTelemetry()
        self.signal_generation = SignalGenerationTelemetry()
        self.bounds_violations = BoundsViolationTelemetry()

    def record_cascade_timing(self, timing_ms: float) -> None:
        """Record cascade timing sample."""
        self.cascade_timing.record(timing_ms)
        self._last_update = datetime.now(UTC)

    def record_signal(self) -> None:
        """Record signal generation event."""
        self.signal_generation.record_signal()
        self._last_update = datetime.now(UTC)

    def record_bounds_violation(self, violation_type: str) -> None:
        """Record bounds violation."""
        self.bounds_violations.record_violation(violation_type)
        self.increment_anomaly()

    def get_extended_telemetry(self) -> dict:
        """Get extended telemetry including S28.B metrics."""
        base = self.get_telemetry()
        return {
            "base": {
                "data_health": base.data_health.value,
                "lifecycle_state": base.lifecycle_state.value,
                "quality_score": base.quality_score,
                "anomaly_count": base.anomaly_count,
                "gap_count": base.gap_count,
            },
            "cascade_timing": {
                "p50_ms": self.cascade_timing.p50_ms,
                "p99_ms": self.cascade_timing.p99_ms,
                "max_ms": self.cascade_timing.max_ms,
                "sample_count": self.cascade_timing.sample_count,
                "slo_violations": self.cascade_timing.slo_violations,
            },
            "signal_generation": {
                "total_signals": self.signal_generation.total_signals,
                "rate_per_minute": self.signal_generation.rate_per_minute,
            },
            "bounds_violations": {
                "total": self.bounds_violations.total_violations,
                "by_type": self.bounds_violations.violations_by_type,
            },
        }
