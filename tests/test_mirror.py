#!/usr/bin/env python3
"""
Mirror Test — IBKR ↔ Dukascopy Boolean Marker Equivalence

Sprint 26 Track A Day 1
Contract: phoenix/contracts/ICT_DATA_CONTRACT.md v1.0.0

INVARIANT: If the same price action flows through the same enrichment logic,
the same boolean markers must fire.

This test proves: XOR_SUM == 0 across boolean markers when IBKR and Dukascopy
data pass through identical enrichment pipeline.

Run with nex venv (IBKR Gateway must be running):
    cd ~/nex && source .venv/bin/activate
    python ~/phoenix/tests/test_mirror.py

Or via pytest:
    cd ~/nex && source .venv/bin/activate
    cd ~/phoenix && python -m pytest tests/test_mirror.py -v -s
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# Add paths for imports
PHOENIX_ROOT = Path.home() / "phoenix"
NEX_ROOT = Path.home() / "nex"
sys.path.insert(0, str(NEX_ROOT))
sys.path.insert(0, str(PHOENIX_ROOT))

import pandas as pd
import numpy as np

# Import mirror markers directly (avoid package import issues)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "mirror_markers", 
    PHOENIX_ROOT / "contracts" / "mirror_markers.py"
)
mirror_markers_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mirror_markers_module)
MIRROR_MARKER_COLUMNS = mirror_markers_module.MIRROR_MARKER_COLUMNS
EXCLUDED_FROM_MIRROR = mirror_markers_module.EXCLUDED_FROM_MIRROR


@dataclass
class MarkerResult:
    """Result for a single marker XOR comparison."""
    marker: str
    xor_sum: int
    total_bars: int
    divergence_rate: float
    divergent_timestamps: List[str]  # First 5 timestamps where XOR=1


@dataclass 
class MirrorTestResult:
    """Complete mirror test results."""
    test_window_start: str
    test_window_end: str
    symbol: str
    
    # Bar counts
    dukascopy_bars: int
    ibkr_bars: int
    aligned_bars: int
    excluded_bars: int
    
    # Marker results
    markers_tested: int
    markers_passed: int
    markers_failed: int
    total_xor_sum: int
    
    # Per-marker details
    marker_results: List[Dict]
    
    # Exclusions
    exclusions: Dict[str, int]
    
    # Verdict
    verdict: str  # PASS or FAIL
    failure_reasons: List[str]


# =============================================================================
# TEST CONFIGURATION
# =============================================================================

# Test window: 4 days where both vendors have data
# Dukascopy: Has data up to 2025-11-21
# IBKR: Can fetch historical for this period
TEST_WINDOW_START = datetime(2025, 11, 17, 0, 0, 0, tzinfo=timezone.utc)
TEST_WINDOW_END = datetime(2025, 11, 21, 0, 0, 0, tzinfo=timezone.utc)
TEST_SYMBOL = "EURUSD"

# Paths (NEX_ROOT defined at top)
RAW_PARQUET_PATH = NEX_ROOT / "nex_lab" / "data" / "fx" / f"{TEST_SYMBOL}_1m.parquet"


# =============================================================================
# DATA EXTRACTION
# =============================================================================

def extract_dukascopy_data(
    start: datetime,
    end: datetime,
    symbol: str = TEST_SYMBOL
) -> pd.DataFrame:
    """
    Extract Dukascopy data from raw parquet for the test window.
    
    Returns raw OHLCV DataFrame (6 columns).
    """
    df = pd.read_parquet(RAW_PARQUET_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # Filter to test window
    mask = (df['timestamp'] >= start) & (df['timestamp'] < end)
    df_window = df[mask].copy()
    
    return df_window.sort_values('timestamp').reset_index(drop=True)


def fetch_ibkr_data(
    start: datetime,
    end: datetime,
    symbol: str = TEST_SYMBOL
) -> Optional[pd.DataFrame]:
    """
    Fetch IBKR historical data for the test window.
    
    Returns raw OHLCV DataFrame (6 columns) or None if fetch fails.
    """
    try:
        from nex_lab.data.vendors.ibkr import fetch_ohlcv
        
        print(f"Fetching IBKR data for {symbol} from {start} to {end}...")
        df = fetch_ohlcv(symbol, "1m", start, end)
        
        if df is None or df.empty:
            print("  WARNING: IBKR returned no data")
            return None
            
        print(f"  Fetched {len(df):,} bars from IBKR")
        return df
        
    except Exception as e:
        print(f"  ERROR fetching IBKR data: {e}")
        return None


# =============================================================================
# ENRICHMENT
# =============================================================================

def run_enrichment(df: pd.DataFrame, symbol: str = TEST_SYMBOL) -> pd.DataFrame:
    """
    Run full NEX enrichment pipeline on raw OHLCV data.
    
    This is the SAME enrichment logic for both vendors — no vendor-specific branches.
    """
    from nex_lab.data.enrichment.incremental import _run_full_enrichment
    
    print(f"Running enrichment on {len(df):,} bars...")
    df_enriched = _run_full_enrichment(df.copy(), symbol)
    print(f"  Enriched to {len(df_enriched.columns)} columns")
    
    return df_enriched


# =============================================================================
# XOR COMPARISON
# =============================================================================

def align_by_timestamp(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    label_a: str = "A",
    label_b: str = "B"
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Align two DataFrames by timestamp for comparison.
    
    Returns:
        - Aligned DataFrame with columns from both sources
        - Dict of exclusion counts
    """
    # Ensure timestamp is the key
    df_a = df_a.copy()
    df_b = df_b.copy()
    
    if 'timestamp' not in df_a.columns:
        if isinstance(df_a.index, pd.DatetimeIndex):
            df_a = df_a.reset_index()
    if 'timestamp' not in df_b.columns:
        if isinstance(df_b.index, pd.DatetimeIndex):
            df_b = df_b.reset_index()
    
    # Merge on timestamp (inner join = only overlapping bars)
    merged = pd.merge(
        df_a, df_b,
        on='timestamp',
        how='inner',
        suffixes=(f'_{label_a}', f'_{label_b}')
    )
    
    exclusions = {
        f'{label_a}_total': len(df_a),
        f'{label_b}_total': len(df_b),
        'aligned': len(merged),
        'excluded_no_match': len(df_a) + len(df_b) - 2 * len(merged)
    }
    
    return merged, exclusions


def xor_compare_markers(
    df_aligned: pd.DataFrame,
    markers: List[str],
    label_a: str = "dukascopy",
    label_b: str = "ibkr"
) -> List[MarkerResult]:
    """
    XOR compare boolean markers between two aligned DataFrames.
    
    Returns list of MarkerResult for each marker.
    """
    results = []
    
    for marker in markers:
        col_a = f"{marker}_{label_a}"
        col_b = f"{marker}_{label_b}"
        
        # Check columns exist
        if col_a not in df_aligned.columns:
            print(f"  WARNING: {col_a} not found in aligned data")
            continue
        if col_b not in df_aligned.columns:
            print(f"  WARNING: {col_b} not found in aligned data")
            continue
        
        # Get values as boolean
        vals_a = df_aligned[col_a].fillna(False).astype(bool)
        vals_b = df_aligned[col_b].fillna(False).astype(bool)
        
        # XOR comparison
        xor_result = vals_a ^ vals_b
        xor_sum = xor_result.sum()
        total_bars = len(xor_result)
        divergence_rate = xor_sum / total_bars if total_bars > 0 else 0.0
        
        # Get timestamps of divergences (first 5)
        divergent_mask = xor_result
        divergent_ts = df_aligned.loc[divergent_mask, 'timestamp'].head(5).astype(str).tolist()
        
        results.append(MarkerResult(
            marker=marker,
            xor_sum=int(xor_sum),
            total_bars=total_bars,
            divergence_rate=float(divergence_rate),
            divergent_timestamps=divergent_ts
        ))
    
    return results


# =============================================================================
# MAIN TEST
# =============================================================================

def run_mirror_test(
    start: datetime = TEST_WINDOW_START,
    end: datetime = TEST_WINDOW_END,
    symbol: str = TEST_SYMBOL
) -> MirrorTestResult:
    """
    Execute full mirror test: IBKR ↔ Dukascopy boolean marker equivalence.
    
    Returns MirrorTestResult with all details.
    """
    print("=" * 70)
    print("MIRROR TEST: IBKR ↔ Dukascopy Boolean Marker Equivalence")
    print("=" * 70)
    print()
    print(f"Test window: {start} to {end}")
    print(f"Symbol: {symbol}")
    print()
    
    failure_reasons = []
    
    # Step 1: Extract Dukascopy data
    print("[1/5] Extracting Dukascopy data...")
    df_dukascopy_raw = extract_dukascopy_data(start, end, symbol)
    print(f"      Found {len(df_dukascopy_raw):,} bars")
    
    if len(df_dukascopy_raw) == 0:
        failure_reasons.append("No Dukascopy data for test window")
    
    # Step 2: Fetch IBKR data
    print()
    print("[2/5] Fetching IBKR historical data...")
    df_ibkr_raw = fetch_ibkr_data(start, end, symbol)
    
    if df_ibkr_raw is None or len(df_ibkr_raw) == 0:
        failure_reasons.append("Failed to fetch IBKR data for test window")
        # Create empty result
        return MirrorTestResult(
            test_window_start=str(start),
            test_window_end=str(end),
            symbol=symbol,
            dukascopy_bars=len(df_dukascopy_raw),
            ibkr_bars=0,
            aligned_bars=0,
            excluded_bars=0,
            markers_tested=0,
            markers_passed=0,
            markers_failed=0,
            total_xor_sum=0,
            marker_results=[],
            exclusions={},
            verdict="FAIL",
            failure_reasons=failure_reasons
        )
    
    print(f"      Found {len(df_ibkr_raw):,} bars")
    
    # Step 3: Run enrichment on both
    print()
    print("[3/5] Running enrichment pipeline...")
    print("      Dukascopy enrichment:")
    df_dukascopy_enriched = run_enrichment(df_dukascopy_raw, symbol)
    print("      IBKR enrichment:")
    df_ibkr_enriched = run_enrichment(df_ibkr_raw, symbol)
    
    # Step 4: Align by timestamp
    print()
    print("[4/5] Aligning data by timestamp...")
    df_aligned, exclusions = align_by_timestamp(
        df_dukascopy_enriched, df_ibkr_enriched,
        label_a="dukascopy", label_b="ibkr"
    )
    print(f"      Dukascopy: {exclusions['dukascopy_total']:,} bars")
    print(f"      IBKR: {exclusions['ibkr_total']:,} bars")
    print(f"      Aligned: {exclusions['aligned']:,} bars")
    print(f"      Excluded (no match): {exclusions['excluded_no_match']:,} bars")
    
    if exclusions['aligned'] == 0:
        failure_reasons.append("No aligned bars between vendors")
    
    # Step 5: XOR compare markers
    print()
    print("[5/5] XOR comparing boolean markers...")
    
    # Filter to markers that exist and aren't excluded
    markers_to_test = [
        m for m in MIRROR_MARKER_COLUMNS 
        if m not in EXCLUDED_FROM_MIRROR
    ]
    print(f"      Testing {len(markers_to_test)} markers (excluding volume-derived)")
    
    marker_results = xor_compare_markers(
        df_aligned, markers_to_test,
        label_a="dukascopy", label_b="ibkr"
    )
    
    # Summarize results
    total_xor = sum(r.xor_sum for r in marker_results)
    passed = sum(1 for r in marker_results if r.xor_sum == 0)
    failed = sum(1 for r in marker_results if r.xor_sum > 0)
    
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Markers tested: {len(marker_results)}")
    print(f"Markers PASS (XOR=0): {passed}")
    print(f"Markers FAIL (XOR>0): {failed}")
    print(f"Total XOR sum: {total_xor:,}")
    
    # Determine verdict
    if total_xor == 0 and len(failure_reasons) == 0:
        verdict = "PASS"
        print()
        print("✅ VERDICT: PASS — Boolean markers are equivalent across vendors")
    else:
        verdict = "FAIL"
        if total_xor > 0:
            failure_reasons.append(f"Total XOR sum = {total_xor} (expected 0)")
        print()
        print("❌ VERDICT: FAIL")
        for reason in failure_reasons:
            print(f"   • {reason}")
    
    # Show failed markers
    if failed > 0:
        print()
        print("Failed markers (showing divergence details):")
        failed_markers = [r for r in marker_results if r.xor_sum > 0]
        for r in sorted(failed_markers, key=lambda x: -x.xor_sum)[:10]:
            print(f"  {r.marker}: XOR={r.xor_sum}, rate={r.divergence_rate:.4%}")
            if r.divergent_timestamps:
                print(f"    First divergence at: {r.divergent_timestamps[0]}")
    
    print("=" * 70)
    
    return MirrorTestResult(
        test_window_start=str(start),
        test_window_end=str(end),
        symbol=symbol,
        dukascopy_bars=len(df_dukascopy_raw),
        ibkr_bars=len(df_ibkr_raw) if df_ibkr_raw is not None else 0,
        aligned_bars=exclusions['aligned'],
        excluded_bars=exclusions.get('excluded_no_match', 0),
        markers_tested=len(marker_results),
        markers_passed=passed,
        markers_failed=failed,
        total_xor_sum=total_xor,
        marker_results=[asdict(r) for r in marker_results],
        exclusions=exclusions,
        verdict=verdict,
        failure_reasons=failure_reasons
    )


def generate_report(result: MirrorTestResult, output_path: Path) -> None:
    """Generate MIRROR_TEST_REPORT.md from test results."""
    
    # Sort markers by XOR sum (failures first)
    sorted_markers = sorted(
        result.marker_results,
        key=lambda x: (-x['xor_sum'], x['marker'])
    )
    
    report = f"""# MIRROR TEST REPORT

**Document:** MIRROR_TEST_REPORT.md  
**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  
**Sprint:** 26 Track A Day 1  
**Contract:** phoenix/contracts/ICT_DATA_CONTRACT.md v1.0.0

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Verdict** | **{result.verdict}** |
| **Symbol** | {result.symbol} |
| **Test Window** | {result.test_window_start} to {result.test_window_end} |
| **Aligned Bars** | {result.aligned_bars:,} |
| **Markers Tested** | {result.markers_tested} |
| **Total XOR Sum** | {result.total_xor_sum:,} |

"""

    if result.verdict == "PASS":
        report += """
### ✅ PASS

All boolean markers produce identical results across IBKR and Dukascopy vendors
when processed through the same enrichment pipeline.

**Invariant Proven:** If the same price action flows through the same enrichment
logic, the same boolean markers fire.

"""
    else:
        report += """
### ❌ FAIL

"""
        for reason in result.failure_reasons:
            report += f"- {reason}\n"
        report += "\n"

    report += f"""
---

## Data Summary

### Bar Counts

| Source | Bars |
|--------|------|
| Dukascopy (raw) | {result.dukascopy_bars:,} |
| IBKR (raw) | {result.ibkr_bars:,} |
| **Aligned** | **{result.aligned_bars:,}** |
| Excluded (no match) | {result.excluded_bars:,} |

### Exclusions

| Category | Count | Reason |
|----------|-------|--------|
| Volume-derived markers | {len(EXCLUDED_FROM_MIRROR)} | Per contract: volume_comparability = NONE |
| Non-matching timestamps | {result.excluded_bars:,} | Bars exist in one vendor but not other |

---

## Per-Marker Results

| Marker | XOR Sum | Total Bars | Divergence Rate | Status |
|--------|---------|------------|-----------------|--------|
"""

    for m in sorted_markers:
        status = "✅ PASS" if m['xor_sum'] == 0 else "❌ FAIL"
        rate = f"{m['divergence_rate']:.4%}" if m['divergence_rate'] > 0 else "0%"
        report += f"| `{m['marker']}` | {m['xor_sum']:,} | {m['total_bars']:,} | {rate} | {status} |\n"

    # Add divergence analysis if there are failures
    failed_markers = [m for m in sorted_markers if m['xor_sum'] > 0]
    if failed_markers:
        report += f"""

---

## Divergence Analysis

### Failed Markers ({len(failed_markers)})

"""
        for m in failed_markers[:10]:  # Top 10
            report += f"""
#### `{m['marker']}`

- **XOR Sum:** {m['xor_sum']:,}
- **Divergence Rate:** {m['divergence_rate']:.4%}
- **Sample Divergent Timestamps:**
"""
            for ts in m['divergent_timestamps'][:3]:
                report += f"  - {ts}\n"

    report += f"""

---

## Test Configuration

```yaml
test_window:
  start: {result.test_window_start}
  end: {result.test_window_end}
  
symbol: {result.symbol}

enrichment_pipeline: nex_lab.data.enrichment.incremental._run_full_enrichment

markers_excluded:
{chr(10).join(f'  - {m}' for m in EXCLUDED_FROM_MIRROR)}

contract_reference: phoenix/contracts/ICT_DATA_CONTRACT.md v1.0.0
schema_hash: b848ffe506fd3fff
```

---

## Verdict

**{result.verdict}**

{"Mirror Test PASSES. Liars Paradox (Day 1.5) may proceed." if result.verdict == "PASS" else "Mirror Test FAILS. Diagnose divergences before proceeding."}

---

*Generated by phoenix/tests/test_mirror.py*
"""

    output_path.write_text(report)
    print(f"\nReport written to: {output_path}")


# =============================================================================
# PYTEST INTEGRATION
# =============================================================================

def test_mirror_xor_sum_zero():
    """
    Pytest test: Mirror Test must pass with XOR_SUM == 0.
    
    This is the gate test for Sprint 26 Track A Day 1.
    """
    result = run_mirror_test()
    
    # Generate report regardless of outcome
    report_dir = Path.home() / "phoenix" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    generate_report(result, report_dir / "MIRROR_TEST_REPORT.md")
    
    # Assert pass condition
    assert result.verdict == "PASS", (
        f"Mirror Test FAILED:\n"
        f"  Total XOR sum: {result.total_xor_sum}\n"
        f"  Markers failed: {result.markers_failed}\n"
        f"  Reasons: {result.failure_reasons}"
    )


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    # Run test and generate report
    result = run_mirror_test()
    
    # Generate report
    report_dir = Path.home() / "phoenix" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    generate_report(result, report_dir / "MIRROR_TEST_REPORT.md")
    
    # Save raw results as JSON
    results_path = report_dir / "mirror_test_results.json"
    with open(results_path, 'w') as f:
        json.dump(asdict(result), f, indent=2, default=str)
    print(f"Raw results saved to: {results_path}")
    
    # Exit with appropriate code
    sys.exit(0 if result.verdict == "PASS" else 1)
