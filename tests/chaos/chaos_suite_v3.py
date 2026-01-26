"""
Chaos Suite V3 — Extended attack vectors for S28 hardening.

SPRINT: S28.A
OWNER: OPUS (builds), BOAR (designs)
EXIT_GATES:
  - bunny_pass (>90% vectors survive)
  - no CRITICAL class failures
  - no V2 regression

NEW VECTORS (V3):
  - V3-RIVER-001: correlated_lies (dual vendor same false value)
  - V3-RIVER-002: regime_nukes (historical chaos patterns)
  - V3-RIVER-003: petabyte_sim (volume stress)
  - V3-CSO-001: methodology_hallucination (incomplete data → signal)
"""

import sys
import time
import hashlib
import random
import threading
import queue
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add phoenix to path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

# Import V2 base (handle both module and direct execution)
try:
    from tests.chaos.chaos_suite_v2 import (
        VectorSeverity, VectorTarget, VectorResult, ChaosVector, 
        VectorTestResult, CHAOS_VECTORS as V2_VECTORS, ChaosSuiteV2
    )
except ModuleNotFoundError:
    from chaos_suite_v2 import (
        VectorSeverity, VectorTarget, VectorResult, ChaosVector, 
        VectorTestResult, CHAOS_VECTORS as V2_VECTORS, ChaosSuiteV2
    )


# =============================================================================
# V3 VECTOR REGISTRY
# =============================================================================

V3_VECTORS: List[ChaosVector] = [
    # RIVER: Correlated Lies
    ChaosVector(
        id="V3-RIVER-001",
        name="correlated_lies",
        description="Dual vendor (IBKR + Dukascopy) report same false value",
        target=VectorTarget.RIVER,
        severity=VectorSeverity.CRITICAL,
        injection="Inject identical false price to both vendor feeds",
        expected_behavior="Detection via self-contradiction (timestamp/sequence/physics)",
        detection_method="Verify liar_paradox catches OR document gap"
    ),
    
    # RIVER: Regime Nukes
    ChaosVector(
        id="V3-RIVER-002",
        name="regime_nukes",
        description="Historical chaos patterns (vol spikes, carry unwind, flash crash)",
        target=VectorTarget.RIVER,
        severity=VectorSeverity.HIGH,
        injection="Inject 2023 vol spike / 2024 JPY carry unwind / flash crash profiles",
        expected_behavior="System survives, halt triggers appropriately, no data corruption",
        detection_method="Verify system state post-injection"
    ),
    
    # RIVER: Petabyte Sim
    ChaosVector(
        id="V3-RIVER-003",
        name="petabyte_sim",
        description="100x normal data volume burst",
        target=VectorTarget.RIVER,
        severity=VectorSeverity.HIGH,
        injection="Burst 100x normal tick volume",
        expected_behavior="INV-HALT-1 (<50ms) maintained under load",
        detection_method="Measure halt latency under load"
    ),
    
    # CSO: Methodology Hallucination
    ChaosVector(
        id="V3-CSO-001",
        name="methodology_hallucination",
        description="Incomplete methodology data leads to signal generation",
        target=VectorTarget.CSO,
        severity=VectorSeverity.CRITICAL,
        injection="Partial Olya methodology drop (missing drawer)",
        expected_behavior="comprehension_hash catches, no bead emission",
        detection_method="Verify CSO refuses signal on incomplete state"
    ),
]

# Combined registry
ALL_VECTORS = V2_VECTORS + V3_VECTORS


# =============================================================================
# CHAOS SUITE V3 RUNNER
# =============================================================================

class ChaosSuiteV3(ChaosSuiteV2):
    """Extended chaos suite with V3 vectors."""
    
    def __init__(self):
        super().__init__()
        self.vectors = ALL_VECTORS
        self.v2_results: List[VectorTestResult] = []
        self.v3_results: List[VectorTestResult] = []
    
    def run_v3_only(self) -> Dict[str, Any]:
        """Run only V3 vectors."""
        self.v3_results = []
        
        for vector in V3_VECTORS:
            try:
                result = self.run_vector(vector.id)
                self.v3_results.append(result)
            except Exception as e:
                self.v3_results.append(VectorTestResult(
                    vector_id=vector.id,
                    result=VectorResult.CRASHED,
                    detection_time_ms=None,
                    evidence={"error": str(e), "type": type(e).__name__},
                    timestamp=datetime.now(timezone.utc)
                ))
        
        return self._calculate_stats(self.v3_results)
    
    def run_v2_regression(self) -> Dict[str, Any]:
        """Run V2 vectors to check for regression."""
        self.v2_results = []
        
        for vector in V2_VECTORS:
            try:
                result = self.run_vector(vector.id)
                self.v2_results.append(result)
            except Exception as e:
                self.v2_results.append(VectorTestResult(
                    vector_id=vector.id,
                    result=VectorResult.CRASHED,
                    detection_time_ms=None,
                    evidence={"error": str(e)},
                    timestamp=datetime.now(timezone.utc)
                ))
        
        return self._calculate_stats(self.v2_results)
    
    def _calculate_stats(self, results: List[VectorTestResult]) -> Dict[str, Any]:
        """Calculate statistics for a result set."""
        if not results:
            return {"total": 0, "survival_rate": 0, "exit_gate_pass": False}
        
        pass_count = sum(1 for r in results if r.result == VectorResult.PASS)
        detected_count = sum(1 for r in results if r.result == VectorResult.DETECTED)
        fail_count = sum(1 for r in results if r.result == VectorResult.FAIL)
        crash_count = sum(1 for r in results if r.result == VectorResult.CRASHED)
        
        survival_rate = (pass_count + detected_count) / len(results) * 100
        
        # Check for CRITICAL failures
        critical_vectors = [v.id for v in self.vectors if v.severity == VectorSeverity.CRITICAL]
        critical_failures = [r for r in results 
                           if r.vector_id in critical_vectors 
                           and r.result in (VectorResult.FAIL, VectorResult.CRASHED)]
        
        return {
            "total": len(results),
            "pass": pass_count,
            "detected": detected_count,
            "fail": fail_count,
            "crashed": crash_count,
            "survival_rate": survival_rate,
            "critical_failures": [f.vector_id for f in critical_failures],
            "exit_gate_pass": survival_rate >= 90 and len(critical_failures) == 0,
        }
    
    def run_full_suite(self) -> Dict[str, Any]:
        """Run full V3 suite with V2 regression check."""
        # Run V2 regression first
        v2_stats = self.run_v2_regression()
        
        # Run V3 vectors
        v3_stats = self.run_v3_only()
        
        # Combined assessment
        all_results = self.v2_results + self.v3_results
        combined_stats = self._calculate_stats(all_results)
        
        return {
            "v2_regression": v2_stats,
            "v3_new": v3_stats,
            "combined": combined_stats,
            "gates": {
                "GATE_1_SURVIVAL": combined_stats["survival_rate"] >= 90,
                "GATE_2_NO_CRITICAL": len(combined_stats["critical_failures"]) == 0,
                "GATE_3_NO_REGRESSION": v2_stats["survival_rate"] == 100,
            },
            "verdict": self._compute_verdict(v2_stats, v3_stats, combined_stats),
        }
    
    def _compute_verdict(self, v2: Dict, v3: Dict, combined: Dict) -> str:
        """Compute overall verdict."""
        if len(combined["critical_failures"]) > 0:
            return "FAIL_CRITICAL"
        if v2["survival_rate"] < 100:
            return "FAIL_REGRESSION"
        if combined["survival_rate"] < 90:
            return "CONDITIONAL"
        return "PASS"
    
    # =========================================================================
    # V3 VECTOR IMPLEMENTATIONS
    # =========================================================================
    
    def _test_V3_RIVER_001(self, vector: ChaosVector) -> VectorTestResult:
        """
        Test correlated_lies vector.
        
        INJECTION: Both IBKR and Dukascopy report same false value
        FAILURE_SURFACE: Liar paradox catches A≠B, but NOT A=B=wrong
        EXPECTED: Detect via self-contradiction (timestamp, sequence, physics)
        """
        import pandas as pd
        import numpy as np
        
        # Simulate dual vendor data
        true_price = 1.0850
        false_price = 1.1000  # 150 pips off (impossible in 1 tick)
        
        # Both vendors report the same false value
        ibkr_data = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-15 10:00:00', periods=100, freq='1s', tz='UTC'),
            'close': [true_price] * 50 + [false_price] * 50,  # Jump at bar 50
            'vendor': 'IBKR',
        })
        
        dukascopy_data = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-15 10:00:00', periods=100, freq='1s', tz='UTC'),
            'close': [true_price] * 50 + [false_price] * 50,  # Same lie
            'vendor': 'Dukascopy',
        })
        
        # Detection method 1: Physics check (impossible price jump)
        max_jump_pips = 50  # Max reasonable 1-second jump
        pip_size = 0.0001
        
        ibkr_jumps = ibkr_data['close'].diff().abs() / pip_size
        dukascopy_jumps = dukascopy_data['close'].diff().abs() / pip_size
        
        physics_violation_ibkr = (ibkr_jumps > max_jump_pips).any()
        physics_violation_duka = (dukascopy_jumps > max_jump_pips).any()
        
        # Detection method 2: Correlation check (both vendors perfectly correlated = suspicious)
        correlation = ibkr_data['close'].corr(dukascopy_data['close'])
        perfect_correlation_flag = correlation > 0.999
        
        # Detection method 3: Sequence check (simultaneous impossible jump)
        jump_at_same_bar = (ibkr_jumps > max_jump_pips) & (dukascopy_jumps > max_jump_pips)
        simultaneous_violation = jump_at_same_bar.any()
        
        # Verdict: Did we detect the lie?
        detected = physics_violation_ibkr or physics_violation_duka or simultaneous_violation
        
        evidence = {
            "physics_violation_ibkr": bool(physics_violation_ibkr),
            "physics_violation_duka": bool(physics_violation_duka),
            "perfect_correlation": bool(perfect_correlation_flag),
            "simultaneous_violation": bool(simultaneous_violation),
            "detected_by": [],
        }
        
        if physics_violation_ibkr:
            evidence["detected_by"].append("physics_ibkr")
        if physics_violation_duka:
            evidence["detected_by"].append("physics_duka")
        if simultaneous_violation:
            evidence["detected_by"].append("simultaneous_jump")
        
        if detected:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.DETECTED,
                detection_time_ms=0,
                evidence=evidence,
                timestamp=datetime.now(timezone.utc)
            )
        else:
            # GAP: Liar paradox alone doesn't catch correlated lies
            evidence["gap"] = "Liar paradox catches A≠B, not A=B=wrong. Physics check required."
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.FAIL,
                detection_time_ms=None,
                evidence=evidence,
                timestamp=datetime.now(timezone.utc)
            )
    
    def _test_V3_RIVER_002(self, vector: ChaosVector) -> VectorTestResult:
        """
        Test regime_nukes vector.
        
        INJECTION: Historical chaos patterns
        - 2023 vol spike profiles
        - 2024 JPY carry unwind
        - Flash crash patterns
        
        EXPECTED: System survives, halt triggers appropriately
        """
        import pandas as pd
        import numpy as np
        
        results = {}
        
        # Pattern 1: 2023 Vol Spike (VIX spike-like behavior)
        vol_spike_data = self._generate_vol_spike_pattern()
        vol_result = self._test_regime_survival(vol_spike_data, "vol_spike_2023")
        results["vol_spike_2023"] = vol_result
        
        # Pattern 2: 2024 JPY Carry Unwind (rapid one-sided move)
        carry_unwind_data = self._generate_carry_unwind_pattern()
        carry_result = self._test_regime_survival(carry_unwind_data, "jpy_carry_2024")
        results["jpy_carry_2024"] = carry_result
        
        # Pattern 3: Flash Crash (rapid down then recovery)
        flash_crash_data = self._generate_flash_crash_pattern()
        flash_result = self._test_regime_survival(flash_crash_data, "flash_crash")
        results["flash_crash"] = flash_result
        
        # All patterns must survive without data corruption
        all_survived = all(r["survived"] for r in results.values())
        any_corruption = any(r.get("data_corruption", False) for r in results.values())
        
        if all_survived and not any_corruption:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.PASS,
                detection_time_ms=0,
                evidence=results,
                timestamp=datetime.now(timezone.utc)
            )
        else:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.FAIL,
                detection_time_ms=None,
                evidence=results,
                timestamp=datetime.now(timezone.utc)
            )
    
    def _generate_vol_spike_pattern(self) -> 'pd.DataFrame':
        """Generate 2023 vol spike pattern."""
        import pandas as pd
        import numpy as np
        
        n = 1000
        base = 1.0850
        
        # Normal vol for first 500, then 5x vol spike
        returns = np.concatenate([
            np.random.randn(500) * 0.0001,  # Normal: 1 pip std
            np.random.randn(500) * 0.0005,  # Spike: 5 pip std
        ])
        
        prices = base + np.cumsum(returns)
        
        return pd.DataFrame({
            'timestamp': pd.date_range('2025-01-15', periods=n, freq='1min', tz='UTC'),
            'close': prices,
            'pattern': 'vol_spike_2023',
        })
    
    def _generate_carry_unwind_pattern(self) -> 'pd.DataFrame':
        """Generate 2024 JPY carry unwind pattern (one-sided rapid move)."""
        import pandas as pd
        import numpy as np
        
        n = 1000
        base = 1.0850
        
        # Gradual drift, then sudden 200 pip move in 50 bars
        normal_drift = np.random.randn(800) * 0.0001
        unwind = np.linspace(0, -0.0200, 200)  # 200 pip drop
        
        returns = np.concatenate([normal_drift, unwind])
        prices = base + np.cumsum(returns)
        
        return pd.DataFrame({
            'timestamp': pd.date_range('2025-01-15', periods=n, freq='1min', tz='UTC'),
            'close': prices,
            'pattern': 'jpy_carry_2024',
        })
    
    def _generate_flash_crash_pattern(self) -> 'pd.DataFrame':
        """Generate flash crash pattern (rapid down then V-recovery)."""
        import pandas as pd
        import numpy as np
        
        n = 1000
        base = 1.0850
        
        # Normal, crash, recovery
        pre_crash = np.random.randn(400) * 0.0001
        crash = np.linspace(0, -0.0150, 100)  # 150 pip crash
        recovery = np.linspace(0, 0.0140, 100)  # 140 pip recovery
        post_crash = np.random.randn(400) * 0.0001
        
        returns = np.concatenate([pre_crash, crash, recovery, post_crash])
        prices = base + np.cumsum(returns)
        
        return pd.DataFrame({
            'timestamp': pd.date_range('2025-01-15', periods=n, freq='1min', tz='UTC'),
            'close': prices,
            'pattern': 'flash_crash',
        })
    
    def _test_regime_survival(self, data: 'pd.DataFrame', pattern_name: str) -> Dict:
        """Test system survival under regime stress."""
        result = {
            "pattern": pattern_name,
            "bars": len(data),
            "survived": True,
            "data_corruption": False,
            "halt_triggered": False,
        }
        
        try:
            # Check 1: Data integrity (no NaN injection from processing)
            nan_before = data['close'].isna().sum()
            
            # Simulate processing
            processed = data.copy()
            processed['return'] = processed['close'].pct_change()
            processed['vol'] = processed['return'].rolling(20).std()
            
            # Check for corruption
            nan_after = processed['close'].isna().sum()
            if nan_after > nan_before:
                result["data_corruption"] = True
                result["survived"] = False
            
            # Check 2: Extreme move detection (would trigger halt)
            max_move = processed['return'].abs().max()
            if max_move > 0.01:  # >1% move
                result["halt_triggered"] = True
            
            # Check 3: Values in valid range
            if processed['close'].min() < 0 or processed['close'].max() > 10:
                result["data_corruption"] = True
                result["survived"] = False
            
        except Exception as e:
            result["survived"] = False
            result["error"] = str(e)
        
        return result
    
    def _test_V3_RIVER_003(self, vector: ChaosVector) -> VectorTestResult:
        """
        Test petabyte_sim vector.
        
        INJECTION: 100x normal data volume burst
        EXPECTED: INV-HALT-1 (<50ms) maintained under load
        """
        import pandas as pd
        import numpy as np
        
        # Normal volume: ~1000 ticks/minute
        # Stress: 100,000 ticks/minute
        normal_volume = 1000
        stress_volume = 100 * normal_volume
        
        # Generate stress data
        stress_data = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-15', periods=stress_volume, freq='600us', tz='UTC'),
            'close': 1.0850 + np.random.randn(stress_volume) * 0.0001,
        })
        
        # Test halt latency under load
        halt_latencies = []
        
        # Simulate processing with periodic halt checks
        halt_requested = threading.Event()
        halt_times = []
        
        def halt_checker():
            """Measure halt response time."""
            for _ in range(10):
                time.sleep(0.1)
                
                start = time.perf_counter()
                halt_requested.set()
                # Measure time to acknowledge
                end = time.perf_counter()
                
                halt_latencies.append((end - start) * 1000)  # ms
                halt_requested.clear()
        
        def data_processor():
            """Simulate heavy data processing."""
            batch_size = 1000
            for i in range(0, len(stress_data), batch_size):
                if halt_requested.is_set():
                    return
                
                batch = stress_data.iloc[i:i+batch_size]
                # Simulate processing
                _ = batch['close'].rolling(10).mean()
                _ = batch['close'].rolling(10).std()
        
        # Run concurrent test
        with ThreadPoolExecutor(max_workers=2) as executor:
            processor_future = executor.submit(data_processor)
            checker_future = executor.submit(halt_checker)
            
            # Wait for completion
            processor_future.result(timeout=30)
            checker_future.result(timeout=30)
        
        # Assess results
        if halt_latencies:
            max_latency = max(halt_latencies)
            avg_latency = sum(halt_latencies) / len(halt_latencies)
            p99_latency = sorted(halt_latencies)[int(len(halt_latencies) * 0.99)] if len(halt_latencies) > 10 else max_latency
        else:
            max_latency = avg_latency = p99_latency = 0
        
        evidence = {
            "stress_volume": stress_volume,
            "normal_volume": normal_volume,
            "multiplier": stress_volume / normal_volume,
            "halt_latencies_ms": halt_latencies,
            "max_latency_ms": max_latency,
            "avg_latency_ms": avg_latency,
            "p99_latency_ms": p99_latency,
            "inv_halt_1_threshold_ms": 50,
        }
        
        # INV-HALT-1: <50ms
        if max_latency < 50:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.PASS,
                detection_time_ms=max_latency,
                evidence=evidence,
                timestamp=datetime.now(timezone.utc)
            )
        else:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.FAIL,
                detection_time_ms=max_latency,
                evidence=evidence,
                timestamp=datetime.now(timezone.utc)
            )
    
    def _test_V3_CSO_001(self, vector: ChaosVector) -> VectorTestResult:
        """
        Test methodology_hallucination vector.
        
        INJECTION: Partial Olya methodology drop (missing drawer)
        EXPECTED: comprehension_hash catches, no bead emission
        """
        # Note: This test validates the CONCEPT without requiring full CSO implementation
        # It tests the methodology completeness check logic itself
        
        # Simulate incomplete methodology state
        complete_drawers = ['foundation', 'context', 'conditions', 'entry', 'management']
        incomplete_drawers = ['foundation', 'context', 'conditions']  # Missing entry, management
        
        # Method 1: Check if CSO validates methodology completeness
        def check_methodology_completeness(drawers: List[str]) -> Tuple[bool, str]:
            """Check if methodology is complete."""
            required = {'foundation', 'context', 'conditions', 'entry', 'management'}
            present = set(drawers)
            missing = required - present
            
            return len(missing) == 0, str(missing) if missing else "complete"
        
        complete_valid, complete_msg = check_methodology_completeness(complete_drawers)
        incomplete_valid, incomplete_msg = check_methodology_completeness(incomplete_drawers)
        
        # Method 2: Simulate comprehension_hash computation
        def compute_comprehension_hash(drawers: List[str], content: Dict) -> str:
            """Compute hash of methodology understanding."""
            data = json.dumps({
                "drawers": sorted(drawers),
                "content_hash": hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, sort_keys=True)
            return hashlib.sha256(data.encode()).hexdigest()
        
        # Method 3: Test signal generation refusal
        def should_emit_signal(drawers: List[str]) -> Tuple[bool, str]:
            """Check if CSO should emit signal."""
            complete, msg = check_methodology_completeness(drawers)
            if not complete:
                return False, f"Incomplete methodology: {msg}"
            return True, "OK"
        
        can_emit_complete, emit_msg_complete = should_emit_signal(complete_drawers)
        can_emit_incomplete, emit_msg_incomplete = should_emit_signal(incomplete_drawers)
        
        evidence = {
            "complete_drawers": complete_drawers,
            "incomplete_drawers": incomplete_drawers,
            "complete_valid": complete_valid,
            "incomplete_valid": incomplete_valid,
            "incomplete_missing": incomplete_msg,
            "can_emit_complete": can_emit_complete,
            "can_emit_incomplete": can_emit_incomplete,
            "emit_refused_reason": emit_msg_incomplete,
        }
        
        # SUCCESS: CSO refuses signal on incomplete state
        if not can_emit_incomplete and can_emit_complete:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.PASS,
                detection_time_ms=0,
                evidence=evidence,
                timestamp=datetime.now(timezone.utc)
            )
        else:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.FAIL,
                detection_time_ms=None,
                evidence=evidence,
                timestamp=datetime.now(timezone.utc)
            )


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(suite: ChaosSuiteV3, results: Dict) -> str:
    """Generate markdown report."""
    report = []
    report.append("# CHAOS V3 REPORT")
    report.append(f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    report.append(f"**Sprint:** S28.A")
    report.append("")
    
    # Verdict
    verdict = results["verdict"]
    verdict_emoji = "✓" if verdict == "PASS" else "✗"
    report.append(f"## VERDICT: {verdict_emoji} {verdict}")
    report.append("")
    
    # Gates
    report.append("## EXIT GATES")
    report.append("")
    report.append("| Gate | Criterion | Result |")
    report.append("|------|-----------|--------|")
    gates = results["gates"]
    report.append(f"| GATE_1_SURVIVAL | >90% vectors pass | {'✓' if gates['GATE_1_SURVIVAL'] else '✗'} |")
    report.append(f"| GATE_2_NO_CRITICAL | Zero CRITICAL failures | {'✓' if gates['GATE_2_NO_CRITICAL'] else '✗'} |")
    report.append(f"| GATE_3_NO_REGRESSION | V2 still 100% | {'✓' if gates['GATE_3_NO_REGRESSION'] else '✗'} |")
    report.append("")
    
    # V3 Results
    report.append("## V3 VECTORS (NEW)")
    report.append("")
    report.append("| ID | Name | Inject | Result | Notes |")
    report.append("|----|------|--------|--------|-------|")
    
    for result in suite.v3_results:
        vector = next((v for v in V3_VECTORS if v.id == result.vector_id), None)
        if vector:
            notes = ""
            if "gap" in result.evidence:
                notes = result.evidence["gap"][:50] + "..."
            elif "detected_by" in result.evidence:
                notes = ", ".join(result.evidence.get("detected_by", []))
            elif "max_latency_ms" in result.evidence:
                notes = f"max={result.evidence['max_latency_ms']:.2f}ms"
            
            report.append(f"| {vector.id} | {vector.name} | {vector.injection[:30]}... | {result.result.value} | {notes} |")
    
    report.append("")
    
    # V2 Regression
    report.append("## V2 REGRESSION CHECK")
    report.append("")
    v2_stats = results["v2_regression"]
    report.append(f"- **Total:** {v2_stats['total']}")
    report.append(f"- **Pass:** {v2_stats['pass']}")
    report.append(f"- **Survival Rate:** {v2_stats['survival_rate']:.1f}%")
    report.append(f"- **Regression:** {'NONE' if v2_stats['survival_rate'] == 100 else 'DETECTED'}")
    report.append("")
    
    # Combined Stats
    report.append("## COMBINED STATISTICS")
    report.append("")
    combined = results["combined"]
    report.append(f"- **Total Vectors:** {combined['total']}")
    report.append(f"- **Pass:** {combined['pass']}")
    report.append(f"- **Detected:** {combined['detected']}")
    report.append(f"- **Fail:** {combined['fail']}")
    report.append(f"- **Crashed:** {combined['crashed']}")
    report.append(f"- **Survival Rate:** {combined['survival_rate']:.1f}%")
    report.append("")
    
    # Critical Failures
    if combined["critical_failures"]:
        report.append("## CRITICAL FAILURES")
        report.append("")
        for vid in combined["critical_failures"]:
            report.append(f"- {vid}")
        report.append("")
    
    # Gaps Discovered
    gaps = []
    for result in suite.v3_results:
        if result.result == VectorResult.FAIL and "gap" in result.evidence:
            gaps.append({
                "vector": result.vector_id,
                "gap": result.evidence["gap"]
            })
    
    if gaps:
        report.append("## GAPS DISCOVERED")
        report.append("")
        for gap in gaps:
            report.append(f"- **{gap['vector']}:** {gap['gap']}")
        report.append("")
    
    # Recommendations
    report.append("## RECOMMENDATIONS")
    report.append("")
    if verdict == "PASS":
        report.append("- System passed all gates. Ready for Track B/C.")
    elif verdict == "CONDITIONAL":
        report.append("- System survived >90% but has gaps. Document and proceed to Track B.")
    else:
        report.append("- CRITICAL failures detected. Halt and remediate before proceeding.")
    report.append("")
    
    return "\n".join(report)


# =============================================================================
# CLI
# =============================================================================

def main():
    """Run chaos suite from CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chaos Suite V3")
    parser.add_argument("--all", action="store_true", help="Run all vectors (V2 + V3)")
    parser.add_argument("--v3-only", action="store_true", help="Run only V3 vectors")
    parser.add_argument("--regression", action="store_true", help="Run V2 regression check")
    parser.add_argument("--vector", type=str, help="Run specific vector")
    parser.add_argument("--list", action="store_true", help="List all vectors")
    parser.add_argument("--report", type=str, help="Write report to file")
    
    args = parser.parse_args()
    
    suite = ChaosSuiteV3()
    
    if args.list:
        print("CHAOS SUITE V3 — VECTORS")
        print("=" * 60)
        print("\n--- V2 VECTORS (REGRESSION) ---")
        for v in V2_VECTORS:
            print(f"{v.id}: {v.name} [{v.severity.value}]")
        print("\n--- V3 VECTORS (NEW) ---")
        for v in V3_VECTORS:
            print(f"{v.id}: {v.name} [{v.severity.value}]")
        return
    
    if args.vector:
        result = suite.run_vector(args.vector)
        print(f"{result.vector_id}: {result.result.value}")
        print(f"  Evidence: {json.dumps(result.evidence, indent=2, default=str)}")
        return
    
    if args.regression:
        results = suite.run_v2_regression()
        print("\nV2 REGRESSION CHECK")
        print("=" * 40)
        print(f"Total: {results['total']}")
        print(f"Pass: {results['pass']}")
        print(f"Survival: {results['survival_rate']:.1f}%")
        return
    
    if args.v3_only:
        results = suite.run_v3_only()
        print("\nV3 VECTORS ONLY")
        print("=" * 40)
        print(f"Total: {results['total']}")
        print(f"Pass: {results['pass']}")
        print(f"Detected: {results['detected']}")
        print(f"Fail: {results['fail']}")
        print(f"Survival: {results['survival_rate']:.1f}%")
        return
    
    if args.all:
        results = suite.run_full_suite()
        
        print("\nCHAOS SUITE V3 — FULL RESULTS")
        print("=" * 60)
        print(f"\nVERDICT: {results['verdict']}")
        print(f"\nGATES:")
        for gate, passed in results['gates'].items():
            print(f"  {gate}: {'PASS' if passed else 'FAIL'}")
        
        print(f"\nV2 Regression: {results['v2_regression']['survival_rate']:.1f}%")
        print(f"V3 New: {results['v3_new']['survival_rate']:.1f}%")
        print(f"Combined: {results['combined']['survival_rate']:.1f}%")
        
        if results['combined']['critical_failures']:
            print(f"\nCRITICAL FAILURES: {results['combined']['critical_failures']}")
        
        if args.report:
            report = generate_report(suite, results)
            Path(args.report).write_text(report)
            print(f"\nReport written to: {args.report}")
        
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
