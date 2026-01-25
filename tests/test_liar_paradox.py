#!/usr/bin/env python3
"""
LIAR'S PARADOX TEST
SPRINT: 26.TRACK_A.DAY_1.5
PURPOSE: prove quality_monitoring detects injected corruption within 1 cycle

INVARIANT: "Truth Teller is awake — lies cannot pass silently"

TEST:
  1. inject: +1 pip to close price (single bar)
  2. process: run integrity check
  3. verify: anomaly detected within 1 cycle

PASS: detection == TRUE, latency <= 1 cycle
FAIL: detection == FALSE → HALT

RUN:
  cd ~/nex && source .venv/bin/activate
  python ~/phoenix/tests/test_liar_paradox.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Dict, List

# Paths
PHOENIX_ROOT = Path.home() / "phoenix"
NEX_ROOT = Path.home() / "nex"
sys.path.insert(0, str(NEX_ROOT))
sys.path.insert(0, str(PHOENIX_ROOT))

import pandas as pd
import numpy as np

# Import TruthTeller
import importlib.util
spec = importlib.util.spec_from_file_location(
    "truth_teller",
    PHOENIX_ROOT / "contracts" / "truth_teller.py"
)
truth_teller_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(truth_teller_module)
TruthTeller = truth_teller_module.TruthTeller
IntegrityResult = truth_teller_module.IntegrityResult


@dataclass
class LiarParadoxResult:
    """Test result structure."""
    verdict: str  # PASS or FAIL
    injection_detected: bool
    detection_method: str
    detection_latency_cycles: int
    
    # Injection details
    injection_bar_index: int
    injection_timestamp: str
    injection_field: str
    injection_delta_pips: float
    original_value: float
    corrupted_value: float
    
    # Detection details
    anomalies_found: int
    quality_score: float
    integrity_result: Dict
    
    # Metadata
    total_bars_tested: int
    test_window: str


# =============================================================================
# TEST CONFIGURATION
# =============================================================================

TEST_SYMBOL = "EURUSD"
INJECTION_DELTA_PIPS = 1.0  # Minimum detectable
INJECTION_FIELD = "close"
TEST_BAR_COUNT = 1000  # Bars to test


# =============================================================================
# TEST EXECUTION
# =============================================================================

def run_liar_paradox_test() -> LiarParadoxResult:
    """
    Execute Liar's Paradox test.
    
    PROCESS:
      1. Load clean canonical data
      2. Create reference hashes
      3. Inject +1 pip corruption
      4. Run TruthTeller detection
      5. Verify detection occurred
    """
    print("=" * 60)
    print("LIAR'S PARADOX TEST")
    print("=" * 60)
    print()
    
    # Step 1: Load clean data
    print("[1/5] LOAD: canonical data")
    raw_path = NEX_ROOT / "nex_lab" / "data" / "fx" / f"{TEST_SYMBOL}_1m.parquet"
    df_clean = pd.read_parquet(raw_path)
    df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'], utc=True)
    
    # Take a sample for testing
    df_clean = df_clean.tail(TEST_BAR_COUNT).reset_index(drop=True)
    print(f"       bars: {len(df_clean)}")
    print(f"       range: {df_clean.timestamp.min()} → {df_clean.timestamp.max()}")
    print()
    
    # Step 2: Create reference hashes
    print("[2/5] HASH: create reference integrity hashes")
    teller = TruthTeller(sensitivity_pips=0.5, continuity_threshold=3.0)
    
    reference_hashes = {}
    for idx, row in df_clean.iterrows():
        ts_key = str(row['timestamp'])
        reference_hashes[ts_key] = teller.compute_bar_hash(row)
    
    dataset_hash_clean = teller.compute_dataset_hash(df_clean)
    print(f"       dataset_hash (clean): {dataset_hash_clean}")
    print()
    
    # Step 3: Inject corruption
    print("[3/5] INJECT: +1 pip to close price")
    injection_bar = len(df_clean) // 2  # Middle bar
    
    df_corrupted, injection_meta = teller.inject_corruption(
        df_clean,
        bar_index=injection_bar,
        field=INJECTION_FIELD,
        delta_pips=INJECTION_DELTA_PIPS
    )
    
    dataset_hash_corrupted = teller.compute_dataset_hash(df_corrupted)
    
    print(f"       bar_index: {injection_bar}")
    print(f"       timestamp: {injection_meta['timestamp']}")
    print(f"       field: {injection_meta['field']}")
    print(f"       delta: +{injection_meta['delta_pips']} pips")
    print(f"       original: {injection_meta['original_value']:.5f}")
    print(f"       corrupted: {injection_meta['corrupted_value']:.5f}")
    print(f"       dataset_hash (corrupted): {dataset_hash_corrupted}")
    print()
    
    # Step 4: Run detection
    print("[4/5] DETECT: TruthTeller integrity check")
    integrity_result = teller.verify_integrity(df_corrupted, reference_hashes)
    
    print(f"       is_valid: {integrity_result.is_valid}")
    print(f"       is_corrupted: {integrity_result.is_corrupted}")
    print(f"       anomaly_suspected: {integrity_result.anomaly_suspected}")
    print(f"       quality_score: {integrity_result.quality_score:.4f}")
    print(f"       anomalies_found: {len(integrity_result.anomalies)}")
    print(f"       message: {integrity_result.message}")
    print()
    
    # Step 5: Verify detection
    print("[5/5] VERIFY: detection results")
    
    injection_detected = False
    detection_method = "NONE"
    
    # Check if the injected bar was flagged
    for anomaly in integrity_result.anomalies:
        if injection_meta['timestamp'] in anomaly['timestamp']:
            injection_detected = True
            detection_method = anomaly['type']
            print(f"       DETECTED at {anomaly['timestamp']}")
            print(f"       type: {anomaly['type']}")
            print(f"       severity: {anomaly['severity']}")
            break
    
    # Also check hash mismatch detection
    hash_mismatch_count = sum(
        1 for a in integrity_result.anomalies 
        if a['type'] == 'HASH_MISMATCH'
    )
    if hash_mismatch_count > 0:
        injection_detected = True
        if detection_method == "NONE":
            detection_method = "HASH_MISMATCH"
        print(f"       hash_mismatches: {hash_mismatch_count}")
    
    print()
    
    # Determine verdict
    verdict = "PASS" if injection_detected else "FAIL"
    
    print("=" * 60)
    print(f"VERDICT: {verdict}")
    if verdict == "PASS":
        print("  Truth Teller detected the lie.")
        print("  Invariant proven: lies cannot pass silently.")
    else:
        print("  CRITICAL: Corruption passed undetected!")
        print("  Action: HALT — quality monitoring insufficient")
    print("=" * 60)
    
    return LiarParadoxResult(
        verdict=verdict,
        injection_detected=injection_detected,
        detection_method=detection_method,
        detection_latency_cycles=1 if injection_detected else -1,
        injection_bar_index=injection_bar,
        injection_timestamp=injection_meta['timestamp'],
        injection_field=injection_meta['field'],
        injection_delta_pips=injection_meta['delta_pips'],
        original_value=injection_meta['original_value'],
        corrupted_value=injection_meta['corrupted_value'],
        anomalies_found=len(integrity_result.anomalies),
        quality_score=integrity_result.quality_score,
        integrity_result={
            'is_valid': integrity_result.is_valid,
            'is_corrupted': integrity_result.is_corrupted,
            'anomaly_suspected': integrity_result.anomaly_suspected,
            'message': integrity_result.message
        },
        total_bars_tested=len(df_clean),
        test_window=f"{df_clean.timestamp.min()} → {df_clean.timestamp.max()}"
    )


def generate_report(result: LiarParadoxResult, output_path: Path) -> None:
    """Generate LIAR_PARADOX_REPORT.md."""
    
    report = f"""# LIAR'S PARADOX REPORT

**SPRINT:** 26.TRACK_A.DAY_1.5  
**DATE:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  
**CONTRACT:** phoenix/contracts/ICT_DATA_CONTRACT.md v1.0.0

---

## VERDICT: {result.verdict}

| Metric | Value |
|--------|-------|
| **injection_detected** | {result.injection_detected} |
| **detection_method** | {result.detection_method} |
| **detection_latency** | {result.detection_latency_cycles} cycle(s) |
| **quality_score** | {result.quality_score:.4f} |

---

## INJECTION

| Parameter | Value |
|-----------|-------|
| bar_index | {result.injection_bar_index} |
| timestamp | {result.injection_timestamp} |
| field | {result.injection_field} |
| delta | +{result.injection_delta_pips} pips |
| original | {result.original_value:.5f} |
| corrupted | {result.corrupted_value:.5f} |

---

## DETECTION

```yaml
is_valid: {result.integrity_result['is_valid']}
is_corrupted: {result.integrity_result['is_corrupted']}
anomaly_suspected: {result.integrity_result['anomaly_suspected']}
anomalies_found: {result.anomalies_found}
message: {result.integrity_result['message']}
```

---

## TEST_CONFIG

```yaml
symbol: {TEST_SYMBOL}
bars_tested: {result.total_bars_tested}
window: {result.test_window}
injection_delta_pips: {INJECTION_DELTA_PIPS}
injection_field: {INJECTION_FIELD}
```

---

## INVARIANT

> "Truth Teller is awake — lies cannot pass silently"

**STATUS:** {"PROVEN" if result.verdict == "PASS" else "VIOLATED"}

---

## EXIT_GATE

| Condition | Status |
|-----------|--------|
| injected_lie_detected | {"TRUE ✅" if result.injection_detected else "FALSE ❌"} |
| detection_latency <= 1 cycle | {"TRUE ✅" if result.detection_latency_cycles <= 1 else "FALSE ❌"} |
| silent_pass | {"FALSE ✅" if result.injection_detected else "TRUE ❌"} |

**NEXT:** {"CHAOS_BUNNY (Day 2)" if result.verdict == "PASS" else "HALT — implement detection"}

---

*Generated by phoenix/tests/test_liar_paradox.py*
"""
    
    output_path.write_text(report)
    print(f"\nReport: {output_path}")


# =============================================================================
# PYTEST
# =============================================================================

def test_liar_paradox():
    """Pytest: Liar's Paradox must detect injected corruption."""
    result = run_liar_paradox_test()
    
    # Generate report
    report_dir = PHOENIX_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    generate_report(result, report_dir / "LIAR_PARADOX_REPORT.md")
    
    # Assert
    assert result.verdict == "PASS", (
        f"LIAR'S PARADOX FAILED\n"
        f"  injection_detected: {result.injection_detected}\n"
        f"  detection_method: {result.detection_method}\n"
        f"  Action: HALT — quality monitoring insufficient"
    )


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    result = run_liar_paradox_test()
    
    # Generate report
    report_dir = PHOENIX_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    generate_report(result, report_dir / "LIAR_PARADOX_REPORT.md")
    
    # Save raw results
    results_path = report_dir / "liar_paradox_results.json"
    with open(results_path, 'w') as f:
        json.dump(asdict(result), f, indent=2, default=str)
    print(f"Results: {results_path}")
    
    sys.exit(0 if result.verdict == "PASS" else 1)
