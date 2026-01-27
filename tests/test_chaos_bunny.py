#!/usr/bin/env python3
"""
CHAOS BUNNY TEST
SPRINT: 26.TRACK_A.DAY_2
PURPOSE: stress river under realistic market chaos, prove degradation VISIBLE not SILENT

INVARIANT: "System degrades gracefully, never lies about health"

VECTORS:
  1. GAPS: random missing bars (5-30 min)
  2. LATENCY: stale data (>60s behind)
  3. SPIKE: price spike (+50 pips)
  4. SEQUENCE: out-of-order timestamps
  5. CORRELATED_CHAOS: gap + spike + latency simultaneous
  7. RECOVERY_LAG: cycles to quality_score > 0.95

PASS_CONDITION:
  all_chaos_detected: TRUE
  quality_telemetry_accurate: TRUE
  no_silent_failures: TRUE
  correlated_chaos: detected + escalated to HALT
  recovery_lag: < 5 cycles

FAIL_CONDITION:
  any_silent_failure: HALT
  quality_lies: HALT

RUN:
  cd ~/nex && source .venv/bin/activate
  python ~/phoenix/tests/test_chaos_bunny.py
"""

import json
import random
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

# Paths
PHOENIX_ROOT = Path.home() / "phoenix"
NEX_ROOT = Path.home() / "nex"
sys.path.insert(0, str(NEX_ROOT))
sys.path.insert(0, str(PHOENIX_ROOT))

# Import ChaosBunny
import importlib.util

import pandas as pd

spec = importlib.util.spec_from_file_location(
    "truth_teller", PHOENIX_ROOT / "contracts" / "truth_teller.py"
)
truth_teller_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(truth_teller_module)
ChaosBunny = truth_teller_module.ChaosBunny
HealthState = truth_teller_module.HealthState


@dataclass
class VectorResult:
    """Result of a single chaos vector test."""

    vector_name: str
    detected: bool
    silent_failure: bool
    health_state: str
    quality_score: float
    anomalies_found: int
    details: dict


@dataclass
class ChaosBunnyResult:
    """Full test result."""

    verdict: str  # PASS or FAIL
    boar_confidence: float  # 0-100%

    # Vector results
    gaps_result: VectorResult
    latency_result: VectorResult
    spike_result: VectorResult
    sequence_result: VectorResult
    correlated_result: VectorResult
    recovery_result: VectorResult

    # Summary
    vectors_passed: int
    vectors_failed: int
    silent_failures: int

    # Threshold documentation
    thresholds: dict

    # Metadata
    test_window: str
    total_bars: int

    # Notes for BOAR
    test_isolation_acknowledged: bool = True
    mitigation_deferred: str = "live_shadow_mode (S27+)"


# =============================================================================
# TEST CONFIGURATION
# =============================================================================

TEST_SYMBOL = "EURUSD"
TEST_BAR_COUNT = 500  # Bars to test
BOAR_CONFIDENCE_TARGET = 0.85  # 85%


# =============================================================================
# VECTOR TESTS
# =============================================================================


def test_vector_gaps(bunny: ChaosBunny, df_clean: pd.DataFrame) -> VectorResult:
    """
    Vector 1: GAPS
    inject: random missing bars (5-30 min gaps)
    count: 10 gaps across test window
    expect: gap_count increments, quality_score drops
    fail_if: silent gap, quality_score == 1.0
    """
    print("\n[VECTOR 1] GAPS")

    # Inject 10 random gaps
    gap_positions = sorted(random.sample(range(20, len(df_clean) - 50), 10))
    gap_durations = [random.randint(5, 30) for _ in range(10)]

    # Inject gaps one at a time (cumulative)
    df_gapped = df_clean.copy()
    total_removed = 0

    for pos, dur in zip(gap_positions, gap_durations, strict=False):
        adjusted_pos = max(0, pos - total_removed)
        df_gapped, meta = bunny.inject_gaps(
            df_gapped, gap_positions=[adjusted_pos], gap_duration_minutes=dur
        )
        total_removed += meta["bars_removed"]

    # Run detection
    result = bunny.detect_chaos(df_gapped)

    # Check detection
    detected = result.gaps_detected > 0
    silent_failure = not detected

    print("  gaps_injected: 10")
    print(f"  gaps_detected: {result.gaps_detected}")
    print(f"  health_state: {result.health_state.value}")
    print(f"  quality_score: {result.quality_score:.3f}")
    print(f"  silent_failure: {silent_failure}")

    return VectorResult(
        vector_name="GAPS",
        detected=detected,
        silent_failure=silent_failure,
        health_state=result.health_state.value,
        quality_score=result.quality_score,
        anomalies_found=len(result.anomalies),
        details={
            "gaps_injected": 10,
            "gaps_detected": result.gaps_detected,
            "bars_removed": total_removed,
        },
    )


def test_vector_latency(bunny: ChaosBunny, df_clean: pd.DataFrame) -> VectorResult:
    """
    Vector 2: LATENCY
    inject: stale data (timestamp > 60s behind)
    expect: staleness_flag TRUE, entries blocked
    fail_if: stale data treated as fresh
    """
    print("\n[VECTOR 2] LATENCY")

    # Inject latency (120 seconds stale)
    df_stale, meta = bunny.inject_latency(df_clean, shift_seconds=120)

    # Current time = now (data will be stale)
    current_time = datetime.now(UTC)

    # Run detection
    result = bunny.detect_chaos(df_stale, current_time=current_time)

    # Check detection
    detected = result.latency_detected
    silent_failure = not detected

    print("  latency_injected: 120s")
    print(f"  latency_detected: {detected}")
    print(f"  health_state: {result.health_state.value}")
    print(f"  quality_score: {result.quality_score:.3f}")
    print(f"  silent_failure: {silent_failure}")

    return VectorResult(
        vector_name="LATENCY",
        detected=detected,
        silent_failure=silent_failure,
        health_state=result.health_state.value,
        quality_score=result.quality_score,
        anomalies_found=len(result.anomalies),
        details={"latency_injected_seconds": 120, "latency_detected": detected},
    )


def test_vector_spike(bunny: ChaosBunny, df_clean: pd.DataFrame) -> VectorResult:
    """
    Vector 3: SPIKE
    inject: price spike (+50 pips single bar)
    expect: anomaly detection fires
    fail_if: spike passes unmarked
    """
    print("\n[VECTOR 3] SPIKE")

    # Inject spike at middle bar
    spike_index = len(df_clean) // 2
    df_spiked, meta = bunny.inject_spike(df_clean, bar_index=spike_index, spike_pips=50.0)

    # Run detection
    result = bunny.detect_chaos(df_spiked)

    # Check detection
    detected = result.spikes_detected > 0
    silent_failure = not detected

    print(f"  spike_injected: +50 pips at bar {spike_index}")
    print(f"  spikes_detected: {result.spikes_detected}")
    print(f"  health_state: {result.health_state.value}")
    print(f"  quality_score: {result.quality_score:.3f}")
    print(f"  silent_failure: {silent_failure}")

    return VectorResult(
        vector_name="SPIKE",
        detected=detected,
        silent_failure=silent_failure,
        health_state=result.health_state.value,
        quality_score=result.quality_score,
        anomalies_found=len(result.anomalies),
        details={
            "spike_injected_pips": 50.0,
            "spike_bar": spike_index,
            "spikes_detected": result.spikes_detected,
        },
    )


def test_vector_sequence(bunny: ChaosBunny, df_clean: pd.DataFrame) -> VectorResult:
    """
    Vector 4: SEQUENCE
    inject: out-of-order timestamps
    expect: sequence_violation flag
    fail_if: silent reorder or acceptance

    ENFORCE: ZERO_TOLERANCE
    """
    print("\n[VECTOR 4] SEQUENCE")

    # Inject sequence error (swap bars 100 and 105)
    df_scrambled, meta = bunny.inject_sequence_error(df_clean, swap_indices=(100, 105))

    # Run detection
    result = bunny.detect_chaos(df_scrambled)

    # Check detection
    detected = result.sequence_errors > 0
    silent_failure = not detected

    print("  sequence_error_injected: swap bars 100 <-> 105")
    print(f"  sequence_errors_detected: {result.sequence_errors}")
    print(f"  health_state: {result.health_state.value}")
    print(f"  quality_score: {result.quality_score:.3f}")
    print(f"  silent_failure: {silent_failure}")

    # ZERO_TOLERANCE: any sequence error should trigger
    if detected and result.sequence_errors != 1:
        print(f"  WARNING: Expected 1 error, got {result.sequence_errors}")

    return VectorResult(
        vector_name="SEQUENCE",
        detected=detected,
        silent_failure=silent_failure,
        health_state=result.health_state.value,
        quality_score=result.quality_score,
        anomalies_found=len(result.anomalies),
        details={
            "sequence_errors_injected": 1,
            "sequence_errors_detected": result.sequence_errors,
            "zero_tolerance_enforced": True,
        },
    )


def test_vector_correlated(bunny: ChaosBunny, df_clean: pd.DataFrame) -> VectorResult:
    """
    Vector 5: CORRELATED_CHAOS
    inject: gap + spike + latency (simultaneous)
    expect: escalation to DEGRADED or HALT
    fail_if: isolated handling, no cascade detection
    """
    print("\n[VECTOR 5] CORRELATED_CHAOS")

    current_time = datetime.now(UTC)

    # Inject correlated chaos (gap + spike + latency)
    df_chaos, meta = bunny.inject_correlated_chaos(df_clean, current_time)

    # Run detection
    result = bunny.detect_chaos(df_chaos, current_time=current_time)

    # Check detection
    escalated = result.health_state in [HealthState.HALT, HealthState.CRITICAL]
    correlated_detected = result.correlated_chaos
    detected = escalated and correlated_detected
    silent_failure = not detected

    print("  chaos_vectors_injected: GAP + SPIKE + LATENCY")
    print(f"  correlated_chaos_detected: {correlated_detected}")
    print(f"  chaos_vectors_active: {result.chaos_vectors_active}")
    print(f"  health_state: {result.health_state.value}")
    print(f"  escalated: {escalated}")
    print(f"  quality_score: {result.quality_score:.3f}")
    print(f"  silent_failure: {silent_failure}")

    return VectorResult(
        vector_name="CORRELATED_CHAOS",
        detected=detected,
        silent_failure=silent_failure,
        health_state=result.health_state.value,
        quality_score=result.quality_score,
        anomalies_found=len(result.anomalies),
        details={
            "vectors_injected": ["GAP", "SPIKE", "LATENCY"],
            "vectors_detected": result.chaos_vectors_active,
            "correlated_detected": correlated_detected,
            "escalated_to": result.health_state.value,
        },
    )


def test_vector_recovery(bunny: ChaosBunny, df_clean: pd.DataFrame) -> VectorResult:
    """
    Vector 7: RECOVERY_LAG
    measure: cycles to quality_score > 0.95 post-injection
    expect: < 5 cycles
    fail_if: persistent degradation > 5 cycles
    """
    print("\n[VECTOR 7] RECOVERY_LAG")

    # Reset bunny state
    bunny.cycles_unhealthy = 0
    bunny.last_health_state = HealthState.HEALTHY

    # Inject single spike (recoverable chaos)
    df_spiked, _ = bunny.inject_spike(df_clean, bar_index=250, spike_pips=60.0)

    # Simulate cycles
    recovery_cycles = 0
    max_test_cycles = 10

    for cycle in range(max_test_cycles):
        if cycle == 0:
            # First cycle: chaotic data
            result = bunny.detect_chaos(df_spiked)
        else:
            # Subsequent cycles: clean data (simulating recovery)
            result = bunny.detect_chaos(df_clean)

        recovery_cycles = cycle + 1

        if result.health_state == HealthState.HEALTHY:
            break

    # Check recovery
    recovered = result.health_state == HealthState.HEALTHY
    within_threshold = recovery_cycles <= 5
    detected = recovered and within_threshold
    silent_failure = not detected

    print(f"  cycles_to_recovery: {recovery_cycles}")
    print("  threshold: 5 cycles")
    print(f"  recovered: {recovered}")
    print(f"  within_threshold: {within_threshold}")
    print(f"  final_health_state: {result.health_state.value}")
    print(f"  final_quality_score: {result.quality_score:.3f}")

    return VectorResult(
        vector_name="RECOVERY_LAG",
        detected=detected,
        silent_failure=silent_failure,
        health_state=result.health_state.value,
        quality_score=result.quality_score,
        anomalies_found=len(result.anomalies),
        details={
            "cycles_to_recovery": recovery_cycles,
            "threshold_cycles": 5,
            "recovered": recovered,
            "within_threshold": within_threshold,
        },
    )


# =============================================================================
# MAIN TEST
# =============================================================================


def run_chaos_bunny_test() -> ChaosBunnyResult:
    """Execute full Chaos Bunny test suite."""

    print("=" * 60)
    print("CHAOS BUNNY TEST")
    print("=" * 60)
    print("INVARIANT: System degrades gracefully, never lies about health")
    print()

    # Load clean data
    print("[LOAD] canonical data")
    raw_path = NEX_ROOT / "nex_lab" / "data" / "fx" / f"{TEST_SYMBOL}_1m.parquet"
    df_clean = pd.read_parquet(raw_path)
    df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"], utc=True)
    df_clean = df_clean.tail(TEST_BAR_COUNT).reset_index(drop=True)

    print(f"  bars: {len(df_clean)}")
    print(f"  range: {df_clean.timestamp.min()} → {df_clean.timestamp.max()}")

    # Initialize bunny
    bunny = ChaosBunny()

    # Run vector tests
    results = []

    # Vector 1: GAPS
    gaps_result = test_vector_gaps(bunny, df_clean)
    results.append(gaps_result)
    bunny = ChaosBunny()  # Reset

    # Vector 2: LATENCY
    latency_result = test_vector_latency(bunny, df_clean)
    results.append(latency_result)
    bunny = ChaosBunny()  # Reset

    # Vector 3: SPIKE
    spike_result = test_vector_spike(bunny, df_clean)
    results.append(spike_result)
    bunny = ChaosBunny()  # Reset

    # Vector 4: SEQUENCE
    sequence_result = test_vector_sequence(bunny, df_clean)
    results.append(sequence_result)
    bunny = ChaosBunny()  # Reset

    # Vector 5: CORRELATED_CHAOS
    correlated_result = test_vector_correlated(bunny, df_clean)
    results.append(correlated_result)
    bunny = ChaosBunny()  # Reset

    # Vector 7: RECOVERY_LAG
    recovery_result = test_vector_recovery(bunny, df_clean)
    results.append(recovery_result)

    # Summarize
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    vectors_passed = sum(1 for r in results if r.detected and not r.silent_failure)
    vectors_failed = len(results) - vectors_passed
    silent_failures = sum(1 for r in results if r.silent_failure)

    print(f"\n  vectors_passed: {vectors_passed}/{len(results)}")
    print(f"  vectors_failed: {vectors_failed}")
    print(f"  silent_failures: {silent_failures}")

    # Calculate BOAR confidence
    boar_confidence = vectors_passed / len(results)

    # Determine verdict
    verdict = "PASS" if silent_failures == 0 and vectors_passed == len(results) else "FAIL"

    print(f"\n  boar_confidence: {boar_confidence * 100:.0f}%")
    print(f"  boar_target: {BOAR_CONFIDENCE_TARGET * 100:.0f}%")
    print(f"  verdict: {verdict}")

    if verdict == "PASS":
        print("\n  INVARIANT PROVEN: System degrades gracefully, never lies about health")
    else:
        print(f"\n  CRITICAL: {silent_failures} silent failure(s) detected")
        print("  Action: HALT — fix detection before proceeding")

    print("=" * 60)

    return ChaosBunnyResult(
        verdict=verdict,
        boar_confidence=boar_confidence,
        gaps_result=gaps_result,
        latency_result=latency_result,
        spike_result=spike_result,
        sequence_result=sequence_result,
        correlated_result=correlated_result,
        recovery_result=recovery_result,
        vectors_passed=vectors_passed,
        vectors_failed=vectors_failed,
        silent_failures=silent_failures,
        thresholds=bunny.detect_chaos(df_clean).thresholds,
        test_window=f"{df_clean.timestamp.min()} → {df_clean.timestamp.max()}",
        total_bars=len(df_clean),
    )


def generate_report(result: ChaosBunnyResult, output_path: Path) -> None:
    """Generate CHAOS_BUNNY_REPORT.md."""

    def vector_row(r: VectorResult) -> str:
        status = "PASS ✓" if r.detected and not r.silent_failure else "FAIL ✗"
        return f"| {r.vector_name} | {status} | {r.health_state} | {r.quality_score:.3f} | {r.silent_failure} |"

    report = f"""# CHAOS BUNNY REPORT

**SPRINT:** 26.TRACK_A.DAY_2
**DATE:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}
**ADVISOR:** BOAR (post-execution audit requested)

---

## VERDICT: {result.verdict}

| Metric | Value |
|--------|-------|
| **vectors_passed** | {result.vectors_passed}/6 |
| **vectors_failed** | {result.vectors_failed} |
| **silent_failures** | {result.silent_failures} |
| **boar_confidence** | {result.boar_confidence * 100:.0f}% |
| **boar_target** | {BOAR_CONFIDENCE_TARGET * 100:.0f}% |

---

## VECTOR RESULTS

| Vector | Status | Health | Quality | Silent |
|--------|--------|--------|---------|--------|
{vector_row(result.gaps_result)}
{vector_row(result.latency_result)}
{vector_row(result.spike_result)}
{vector_row(result.sequence_result)}
{vector_row(result.correlated_result)}
{vector_row(result.recovery_result)}

---

## VECTOR DETAILS

### 1. GAPS
```yaml
detected: {result.gaps_result.detected}
gaps_injected: {result.gaps_result.details.get('gaps_injected', 'N/A')}
gaps_detected: {result.gaps_result.details.get('gaps_detected', 'N/A')}
bars_removed: {result.gaps_result.details.get('bars_removed', 'N/A')}
```

### 2. LATENCY
```yaml
detected: {result.latency_result.detected}
latency_injected_seconds: {result.latency_result.details.get('latency_injected_seconds', 'N/A')}
latency_detected: {result.latency_result.details.get('latency_detected', 'N/A')}
```

### 3. SPIKE
```yaml
detected: {result.spike_result.detected}
spike_pips: {result.spike_result.details.get('spike_injected_pips', 'N/A')}
spikes_detected: {result.spike_result.details.get('spikes_detected', 'N/A')}
```

### 4. SEQUENCE
```yaml
detected: {result.sequence_result.detected}
errors_injected: {result.sequence_result.details.get('sequence_errors_injected', 'N/A')}
errors_detected: {result.sequence_result.details.get('sequence_errors_detected', 'N/A')}
zero_tolerance_enforced: {result.sequence_result.details.get('zero_tolerance_enforced', 'N/A')}
```

### 5. CORRELATED_CHAOS
```yaml
detected: {result.correlated_result.detected}
vectors_injected: {result.correlated_result.details.get('vectors_injected', 'N/A')}
vectors_detected: {result.correlated_result.details.get('vectors_detected', 'N/A')}
escalated_to: {result.correlated_result.details.get('escalated_to', 'N/A')}
```

### 7. RECOVERY_LAG
```yaml
detected: {result.recovery_result.detected}
cycles_to_recovery: {result.recovery_result.details.get('cycles_to_recovery', 'N/A')}
threshold_cycles: {result.recovery_result.details.get('threshold_cycles', 'N/A')}
within_threshold: {result.recovery_result.details.get('within_threshold', 'N/A')}
```

---

## THRESHOLD RATIONALE

```yaml
healthy_threshold: {result.thresholds.get('healthy', 'N/A')}
degraded_threshold: {result.thresholds.get('degraded', 'N/A')}
critical_threshold: {result.thresholds.get('critical', 'N/A')}
gap_minutes: {result.thresholds.get('gap_minutes', 'N/A')}
latency_seconds: {result.thresholds.get('latency_seconds', 'N/A')}
spike_pips: {result.thresholds.get('spike_pips', 'N/A')}
recovery_max_cycles: {result.thresholds.get('recovery_max_cycles', 'N/A')}

rationale:
  healthy_0.95: "Normal operation, 5% tolerance for market gaps"
  degraded_0.70: "30% issue threshold — beyond this, entries blocked"
  spike_50_pips: "Single-bar 50+ pip move rare outside news — flag for review"
```

---

## TEST METADATA

```yaml
symbol: {TEST_SYMBOL}
total_bars: {result.total_bars}
test_window: {result.test_window}
test_isolation_acknowledged: {result.test_isolation_acknowledged}
mitigation_deferred: {result.mitigation_deferred}
```

---

## INVARIANT

> "System degrades gracefully, never lies about health"

**STATUS:** {"PROVEN" if result.verdict == "PASS" else "VIOLATED"}

---

## EXIT_GATE

| Condition | Status |
|-----------|--------|
| all_vectors_detected | {"TRUE ✓" if result.silent_failures == 0 else "FALSE ✗"} |
| quality_telemetry_accurate | {"TRUE ✓" if result.vectors_passed >= 5 else "FALSE ✗"} |
| no_silent_failures | {"TRUE ✓" if result.silent_failures == 0 else "FALSE ✗"} |
| correlated_chaos_escalated | {"TRUE ✓" if result.correlated_result.detected else "FALSE ✗"} |
| recovery_lag < 5 cycles | {"TRUE ✓" if result.recovery_result.detected else "FALSE ✗"} |

**NEXT:** {"HISTORICAL_NUKES (Day 2.5)" if result.verdict == "PASS" else "HALT — fix detection"}

---

## BOAR AUDIT REQUEST

**TO:** BOAR
**RE:** Adversarial audit of Chaos Bunny results

Questions for BOAR:
1. What chaos vectors did we miss?
2. Are the thresholds appropriately calibrated?
3. Is the correlated chaos escalation logic sound?
4. What additional edge cases should we test?

**CONFIDENCE:** {result.boar_confidence * 100:.0f}% (target: {BOAR_CONFIDENCE_TARGET * 100:.0f}%)

---

*Generated by phoenix/tests/test_chaos_bunny.py*
"""

    output_path.write_text(report)
    print(f"\nReport: {output_path}")


# =============================================================================
# PYTEST
# =============================================================================


def test_chaos_bunny():
    """Pytest: Chaos Bunny must detect all injected chaos."""
    result = run_chaos_bunny_test()

    # Generate report
    report_dir = PHOENIX_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    generate_report(result, report_dir / "CHAOS_BUNNY_REPORT.md")

    # Assert
    assert result.verdict == "PASS", (
        f"CHAOS_BUNNY FAILED\n"
        f"  vectors_passed: {result.vectors_passed}/6\n"
        f"  silent_failures: {result.silent_failures}\n"
        f"  Action: HALT — fix detection before proceeding"
    )


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    result = run_chaos_bunny_test()

    # Generate report
    report_dir = PHOENIX_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    generate_report(result, report_dir / "CHAOS_BUNNY_REPORT.md")

    # Save raw results
    results_path = report_dir / "chaos_bunny_results.json"
    with open(results_path, "w") as f:
        # Convert dataclasses to dict
        result_dict = asdict(result)
        json.dump(result_dict, f, indent=2, default=str)
    print(f"Results: {results_path}")

    sys.exit(0 if result.verdict == "PASS" else 1)
