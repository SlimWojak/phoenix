"""
Chaos Suite V2 — BOAR attack vectors for S27 components.

SPRINT: S27.0
OWNER: OPUS (builds), BOAR (designs)
EXIT_GATE: bunny_pass (>90% vectors survive)

VECTORS:
- heresy_hallucination: CSO drafts bead from hallucinated comprehension
- synthetic_leak: NEX forward-fill survives subsumption
- flow_shatter: news flash tanks context_quality
- zombie_bleed: halt orphans workers
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timezone

# Add phoenix to path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


# =============================================================================
# VECTOR TYPES
# =============================================================================

class VectorSeverity(Enum):
    """Chaos vector severity."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VectorTarget(Enum):
    """Target component."""
    CSO = "cso"
    NEX = "nex"
    EXECUTION = "execution"
    DISPATCHER = "dispatcher"
    RIVER = "river"


class VectorResult(Enum):
    """Vector test result."""
    PASS = "pass"           # System handled correctly
    FAIL = "fail"           # System failed silently
    DETECTED = "detected"   # System detected and flagged
    CRASHED = "crashed"     # System crashed


@dataclass
class ChaosVector:
    """Chaos test vector definition."""
    id: str
    name: str
    description: str
    target: VectorTarget
    severity: VectorSeverity
    injection: str
    expected_behavior: str
    detection_method: str


@dataclass
class VectorTestResult:
    """Result of running a chaos vector."""
    vector_id: str
    result: VectorResult
    detection_time_ms: Optional[float]
    evidence: Dict[str, Any]
    timestamp: datetime


# =============================================================================
# VECTOR REGISTRY
# =============================================================================

CHAOS_VECTORS: List[ChaosVector] = [
    # CSO vectors
    ChaosVector(
        id="V2-CSO-001",
        name="heresy_hallucination",
        description="CSO drafts bead from hallucinated comprehension",
        target=VectorTarget.CSO,
        severity=VectorSeverity.CRITICAL,
        injection="Inject fake comprehension_hash without corresponding input",
        expected_behavior="CSO rejects bead or marks UNVERIFIED",
        detection_method="Check bead.verified_hash matches actual input"
    ),
    ChaosVector(
        id="V2-CSO-002",
        name="cso_exec_write",
        description="CSO attempts write to execution_state",
        target=VectorTarget.CSO,
        severity=VectorSeverity.CRITICAL,
        injection="Call CSO method that writes to execution_state",
        expected_behavior="TierViolationError raised (INV-GOV-NO-T1-WRITE-EXEC)",
        detection_method="Catch TierViolationError"
    ),
    ChaosVector(
        id="V2-CSO-003",
        name="bead_mutation",
        description="Attempt to mutate bead after creation",
        target=VectorTarget.CSO,
        severity=VectorSeverity.HIGH,
        injection="Modify bead.content after emit",
        expected_behavior="BeadImmutableError raised",
        detection_method="Catch BeadImmutableError"
    ),
    
    # NEX/River vectors
    ChaosVector(
        id="V2-NEX-001",
        name="synthetic_leak",
        description="NEX forward-fill survives subsumption",
        target=VectorTarget.NEX,
        severity=VectorSeverity.CRITICAL,
        injection="Create gap in data, run enrichment",
        expected_behavior="NaN preserved, not forward-filled",
        detection_method="Check NaN count unchanged"
    ),
    ChaosVector(
        id="V2-NEX-002",
        name="schema_drift",
        description="Enrichment produces wrong column count",
        target=VectorTarget.NEX,
        severity=VectorSeverity.HIGH,
        injection="Run enrichment with edge case data",
        expected_behavior="Column count matches contract",
        detection_method="Assert column count == schema"
    ),
    ChaosVector(
        id="V2-NEX-003",
        name="determinism_break",
        description="Same input produces different output",
        target=VectorTarget.NEX,
        severity=VectorSeverity.CRITICAL,
        injection="Run enrichment twice with same seed",
        expected_behavior="Outputs identical (INV-CONTRACT-1)",
        detection_method="Hash comparison"
    ),
    
    # Execution vectors
    ChaosVector(
        id="V2-EXEC-001",
        name="halt_bypass",
        description="Action executes without halt check",
        target=VectorTarget.EXECUTION,
        severity=VectorSeverity.CRITICAL,
        injection="Call action with halt_signal=True",
        expected_behavior="HaltException raised (INV-GOV-HALT-BEFORE-ACTION)",
        detection_method="Verify exception raised"
    ),
    ChaosVector(
        id="V2-EXEC-002",
        name="capital_leak",
        description="T0/T1 module writes capital state",
        target=VectorTarget.EXECUTION,
        severity=VectorSeverity.CRITICAL,
        injection="Call submit_order from non-T2",
        expected_behavior="TierViolationError raised",
        detection_method="Catch exception"
    ),
    ChaosVector(
        id="V2-EXEC-003",
        name="intent_nondeterministic",
        description="Intent object not deterministic",
        target=VectorTarget.EXECUTION,
        severity=VectorSeverity.HIGH,
        injection="Create intent twice with same params",
        expected_behavior="intent_hash identical",
        detection_method="Hash comparison"
    ),
    
    # Dispatcher vectors
    ChaosVector(
        id="V2-DISP-001",
        name="zombie_bleed",
        description="Halt orphans workers",
        target=VectorTarget.DISPATCHER,
        severity=VectorSeverity.HIGH,
        injection="Broadcast halt, kill dispatcher without cleanup",
        expected_behavior="All workers stopped, no orphans",
        detection_method="tmux list-sessions empty"
    ),
    ChaosVector(
        id="V2-DISP-002",
        name="cascade_timeout",
        description="Halt cascade exceeds SLO",
        target=VectorTarget.DISPATCHER,
        severity=VectorSeverity.HIGH,
        injection="Spawn 10 workers, broadcast halt",
        expected_behavior="Cascade < 500ms (INV-HALT-2)",
        detection_method="Timing measurement"
    ),
    
    # River vectors (deferred)
    ChaosVector(
        id="V2-RIVER-001",
        name="flow_shatter",
        description="News flash tanks context_quality",
        target=VectorTarget.RIVER,
        severity=VectorSeverity.MEDIUM,
        injection="Inject news event, measure quality",
        expected_behavior="Quality degrades gracefully",
        detection_method="Quality score trajectory"
    ),
]


# =============================================================================
# RUNNER
# =============================================================================

class ChaosSuiteV2:
    """Chaos suite runner."""
    
    def __init__(self):
        self.vectors = CHAOS_VECTORS
        self.results: List[VectorTestResult] = []
    
    def run_vector(self, vector_id: str) -> VectorTestResult:
        """Run a single chaos vector."""
        vector = next((v for v in self.vectors if v.id == vector_id), None)
        if not vector:
            raise ValueError(f"Unknown vector: {vector_id}")
        
        # Dispatch to appropriate test
        test_fn = getattr(self, f"_test_{vector.id.replace('-', '_')}", None)
        if test_fn:
            return test_fn(vector)
        else:
            return VectorTestResult(
                vector_id=vector_id,
                result=VectorResult.FAIL,
                detection_time_ms=None,
                evidence={"error": "No test implementation"},
                timestamp=datetime.now(timezone.utc)
            )
    
    def run_all(self) -> Dict[str, Any]:
        """Run all chaos vectors."""
        self.results = []
        
        for vector in self.vectors:
            try:
                result = self.run_vector(vector.id)
                self.results.append(result)
            except Exception as e:
                self.results.append(VectorTestResult(
                    vector_id=vector.id,
                    result=VectorResult.CRASHED,
                    detection_time_ms=None,
                    evidence={"error": str(e)},
                    timestamp=datetime.now(timezone.utc)
                ))
        
        # Calculate stats
        pass_count = sum(1 for r in self.results if r.result == VectorResult.PASS)
        detected_count = sum(1 for r in self.results if r.result == VectorResult.DETECTED)
        fail_count = sum(1 for r in self.results if r.result == VectorResult.FAIL)
        crash_count = sum(1 for r in self.results if r.result == VectorResult.CRASHED)
        
        survival_rate = (pass_count + detected_count) / len(self.results) * 100
        
        return {
            "total": len(self.results),
            "pass": pass_count,
            "detected": detected_count,
            "fail": fail_count,
            "crashed": crash_count,
            "survival_rate": survival_rate,
            "exit_gate_pass": survival_rate >= 90,
        }
    
    # =========================================================================
    # VECTOR TEST IMPLEMENTATIONS
    # =========================================================================
    
    def _test_V2_NEX_001(self, vector: ChaosVector) -> VectorTestResult:
        """Test synthetic_leak vector."""
        import pandas as pd
        import numpy as np
        
        from enrichment.layers import l1_time_sessions
        
        # Create data with explicit gap
        df = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-15', periods=100, freq='1min', tz='UTC'),
            'close': [1.0850] * 50 + [np.nan] * 10 + [1.0860] * 40,
            'high': 1.0855,
            'low': 1.0845,
        })
        
        # Count NaN before
        nan_before = df['close'].isna().sum()
        
        # Run L1 (should preserve NaN, not fill)
        result = l1_time_sessions.enrich(df)
        
        # The close column should still have NaN
        nan_after = result['close'].isna().sum()
        
        if nan_after == nan_before:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.PASS,
                detection_time_ms=0,
                evidence={"nan_before": nan_before, "nan_after": nan_after},
                timestamp=datetime.now(timezone.utc)
            )
        else:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.FAIL,
                detection_time_ms=None,
                evidence={"nan_before": nan_before, "nan_after": nan_after},
                timestamp=datetime.now(timezone.utc)
            )
    
    def _test_V2_NEX_003(self, vector: ChaosVector) -> VectorTestResult:
        """Test determinism_break vector."""
        import pandas as pd
        import numpy as np
        import hashlib
        
        from enrichment.layers import l1_time_sessions
        
        # Create identical inputs
        np.random.seed(42)
        df1 = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-15', periods=100, freq='1min', tz='UTC'),
            'close': 1.0850 + np.random.randn(100) * 0.001,
            'high': 1.0855,
            'low': 1.0845,
        })
        
        np.random.seed(42)
        df2 = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-15', periods=100, freq='1min', tz='UTC'),
            'close': 1.0850 + np.random.randn(100) * 0.001,
            'high': 1.0855,
            'low': 1.0845,
        })
        
        # Run enrichment
        result1 = l1_time_sessions.enrich(df1)
        result2 = l1_time_sessions.enrich(df2)
        
        # Compare hashes
        hash1 = hashlib.sha256(result1.to_json().encode()).hexdigest()
        hash2 = hashlib.sha256(result2.to_json().encode()).hexdigest()
        
        if hash1 == hash2:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.PASS,
                detection_time_ms=0,
                evidence={"hash1": hash1[:16], "hash2": hash2[:16]},
                timestamp=datetime.now(timezone.utc)
            )
        else:
            return VectorTestResult(
                vector_id=vector.id,
                result=VectorResult.FAIL,
                detection_time_ms=None,
                evidence={"hash1": hash1[:16], "hash2": hash2[:16]},
                timestamp=datetime.now(timezone.utc)
            )


# =============================================================================
# CLI
# =============================================================================

def main():
    """Run chaos suite from CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chaos Suite V2")
    parser.add_argument("--all", action="store_true", help="Run all vectors")
    parser.add_argument("--vector", type=str, help="Run specific vector")
    parser.add_argument("--list", action="store_true", help="List all vectors")
    
    args = parser.parse_args()
    
    suite = ChaosSuiteV2()
    
    if args.list:
        print("CHAOS SUITE V2 — VECTORS")
        print("=" * 60)
        for v in suite.vectors:
            print(f"{v.id}: {v.name}")
            print(f"  Target: {v.target.value}")
            print(f"  Severity: {v.severity.value}")
            print()
        return
    
    if args.vector:
        result = suite.run_vector(args.vector)
        print(f"{result.vector_id}: {result.result.value}")
        print(f"  Evidence: {result.evidence}")
        return
    
    if args.all:
        results = suite.run_all()
        print("\nCHAOS SUITE V2 — RESULTS")
        print("=" * 60)
        print(f"Total: {results['total']}")
        print(f"Pass: {results['pass']}")
        print(f"Detected: {results['detected']}")
        print(f"Fail: {results['fail']}")
        print(f"Crashed: {results['crashed']}")
        print(f"Survival Rate: {results['survival_rate']:.1f}%")
        print(f"Exit Gate: {'PASS' if results['exit_gate_pass'] else 'FAIL'}")
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
