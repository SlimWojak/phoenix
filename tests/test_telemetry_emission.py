#!/usr/bin/env python3
"""
TEST: TELEMETRY EMISSION
SPRINT: 26.TRACK_B
EXIT_GATE: QualityTelemetry emits correctly

PURPOSE:
  Prove telemetry system works correctly.
  All required fields present and accurate.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

PHOENIX_ROOT = Path.home() / "phoenix"
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import (
    TelemetryEmitter,
    TelemetryAggregator,
    QualityTelemetry,
    HealthState,
    LifecycleState,
)


# =============================================================================
# TESTS
# =============================================================================

def test_telemetry_emitter_initialization():
    """TelemetryEmitter initializes with healthy defaults."""
    emitter = TelemetryEmitter(module_id="test_module")
    telemetry = emitter.get_telemetry()
    
    print("\nInitial Telemetry:")
    print(f"  data_health: {telemetry.data_health.value}")
    print(f"  lifecycle_state: {telemetry.lifecycle_state.value}")
    print(f"  quality_score: {telemetry.quality_score}")
    
    assert telemetry.data_health == HealthState.HEALTHY
    assert telemetry.lifecycle_state == LifecycleState.RUNNING
    assert telemetry.quality_score == 1.0


def test_telemetry_update():
    """TelemetryEmitter.update() changes values correctly."""
    emitter = TelemetryEmitter(module_id="test_module")
    
    # Update with degraded values
    telemetry = emitter.update(
        quality_score=0.85,
        anomaly_count=5,
        gap_count=2
    )
    
    print("\nUpdated Telemetry:")
    print(f"  quality_score: {telemetry.quality_score}")
    print(f"  anomaly_count: {telemetry.anomaly_count}")
    print(f"  gap_count: {telemetry.gap_count}")
    print(f"  data_health: {telemetry.data_health.value}")
    
    assert telemetry.quality_score == 0.85
    assert telemetry.anomaly_count == 5
    assert telemetry.gap_count == 2
    # 0.85 is between 0.95 and 0.70 → DEGRADED
    assert telemetry.data_health == HealthState.DEGRADED


def test_health_state_thresholds():
    """Health state computed correctly from quality_score."""
    emitter = TelemetryEmitter(module_id="test_module")
    
    test_cases = [
        (1.0, HealthState.HEALTHY),
        (0.95, HealthState.HEALTHY),
        (0.94, HealthState.DEGRADED),
        (0.80, HealthState.DEGRADED),
        (0.70, HealthState.DEGRADED),
        (0.69, HealthState.CRITICAL),
        (0.50, HealthState.CRITICAL),
        (0.0, HealthState.CRITICAL),
    ]
    
    print("\nHealth State Thresholds:")
    for score, expected in test_cases:
        emitter.update(quality_score=score)
        actual = emitter.get_telemetry().data_health
        status = "✓" if actual == expected else "✗"
        print(f"  score={score:.2f} → {actual.value} {status}")
        assert actual == expected, f"score={score}: expected {expected}, got {actual}"


def test_staleness_triggers_critical():
    """Staleness > threshold triggers CRITICAL."""
    emitter = TelemetryEmitter(module_id="test_module")
    
    # Good quality but stale
    emitter.update(quality_score=1.0, staleness_seconds=100)
    telemetry = emitter.get_telemetry()
    
    print(f"\nStaleness Test:")
    print(f"  quality_score: {telemetry.quality_score}")
    print(f"  staleness_seconds: {telemetry.staleness_seconds}")
    print(f"  data_health: {telemetry.data_health.value}")
    
    # Should be CRITICAL due to staleness
    assert telemetry.data_health == HealthState.CRITICAL


def test_telemetry_to_dict():
    """QualityTelemetry.to_dict() returns serializable dict."""
    emitter = TelemetryEmitter(module_id="test_module")
    emitter.update(quality_score=0.90, anomaly_count=3)
    
    telemetry = emitter.get_telemetry()
    d = telemetry.to_dict()
    
    print("\nTelemetry Dict:")
    for k, v in d.items():
        print(f"  {k}: {v}")
    
    assert 'data_health' in d
    assert 'lifecycle_state' in d
    assert 'quality_score' in d
    assert 'last_update' in d
    assert 'anomaly_count' in d
    
    # Should be JSON-serializable strings
    assert isinstance(d['data_health'], str)
    assert isinstance(d['lifecycle_state'], str)


def test_telemetry_aggregator():
    """TelemetryAggregator aggregates multiple emitters."""
    aggregator = TelemetryAggregator()
    
    # Create emitters with different states
    emitter1 = TelemetryEmitter(module_id="mod1")
    emitter1.update(quality_score=1.0)
    
    emitter2 = TelemetryEmitter(module_id="mod2")
    emitter2.update(quality_score=0.85, anomaly_count=5)
    
    emitter3 = TelemetryEmitter(module_id="mod3")
    emitter3.update(quality_score=0.50, gap_count=10)
    
    # Register
    aggregator.register(emitter1)
    aggregator.register(emitter2)
    aggregator.register(emitter3)
    
    # Aggregate
    agg = aggregator.aggregate()
    
    print("\nAggregated Telemetry:")
    print(f"  module_count: {agg.module_count}")
    print(f"  healthy_count: {agg.healthy_count}")
    print(f"  degraded_count: {agg.degraded_count}")
    print(f"  critical_count: {agg.critical_count}")
    print(f"  min_quality_score: {agg.min_quality_score}")
    print(f"  avg_quality_score: {agg.avg_quality_score:.3f}")
    print(f"  total_anomalies: {agg.total_anomalies}")
    print(f"  total_gaps: {agg.total_gaps}")
    
    assert agg.module_count == 3
    assert agg.healthy_count == 1
    assert agg.degraded_count == 1
    assert agg.critical_count == 1
    assert agg.min_quality_score == 0.50
    assert agg.total_anomalies == 5
    assert agg.total_gaps == 10


def test_increment_counters():
    """increment_anomaly() and increment_gap() work."""
    emitter = TelemetryEmitter(module_id="test_module")
    
    assert emitter.get_telemetry().anomaly_count == 0
    
    emitter.increment_anomaly()
    emitter.increment_anomaly()
    emitter.increment_gap()
    
    telemetry = emitter.get_telemetry()
    assert telemetry.anomaly_count == 2
    assert telemetry.gap_count == 1
    
    print("\nIncrement Counters: VERIFIED")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TELEMETRY EMISSION TEST")
    print("=" * 60)
    
    try:
        test_telemetry_emitter_initialization()
        test_telemetry_update()
        test_health_state_thresholds()
        test_staleness_triggers_critical()
        test_telemetry_to_dict()
        test_telemetry_aggregator()
        test_increment_counters()
        
        print("\n" + "=" * 60)
        print("VERDICT: PASS")
        print("  - TelemetryEmitter initializes correctly")
        print("  - Health thresholds work")
        print("  - Aggregator aggregates")
        print("  - All required fields present")
        print("=" * 60)
        
        sys.exit(0)
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print("VERDICT: FAIL")
        print(f"  {e}")
        print("=" * 60)
        sys.exit(1)
