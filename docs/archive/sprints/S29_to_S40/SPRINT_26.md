# SPRINT 26: FOUNDATION PROOF

**Document:** SPRINT_26.md  
**Date:** 2026-01-23  
**Author:** Claude (CTO) — Opus via Cursor  
**Status:** APPROVED — Ready for Execution  
**Codename:** The River  
**Reviewed:** CTO (Opus) + Wise Owl (Gemini) feedback integrated  
**Supersedes:** SPRINT_26_SKELETON.md (draft)

---

## Context: Why This Sprint

### The Epiphany

On 2026-01-22, we attempted to use God_Mode's forge to build Meridian's Data Integrity Layer. The forge produced garbage. This forced an honest question that triggered the Phoenix reframe:

> "The governance patterns we learned building the forge ARE the architecture the trading system needs."

**The Shift:** Forge = OS, Phoenix = first App. Hive builds, Forge governs.

### The Founding Act

Sprint 26 is the **First Physical Act of Phoenix**. Before we build organs that drink from data (CSO, Enrichment, Execution), we must prove the River is clean.

**Theme:** Prove the River before building organs that drink from it.

**Gate:** Phoenix cannot build CSO, Enrichment, or Execution until River integrity is proven.

---

## NEX Salvage Context (DATA_PIPELINE_AUTOPSY.md)

The audit completed on 2026-01-22 found:

| Finding | Status | Implication |
|---------|--------|-------------|
| **Data Flow** | Sound architecture | 6 raw → 68+ enriched columns works |
| **12-Layer Enrichment** | Functional | ICT markers computable |
| **INV-DATA Compliance** | PARTIAL | Pipeline hash missing, forward-fills exist |
| **Flakiness Indicators** | 14 found | Silent failures, exception swallowing |
| **Volume Semantics** | UNKNOWN | Dukascopy tick count vs IBKR volume |

**Strategy:** In-Flight Refit. Salvage NEX components, wrap in `GovernanceInterface`. Don't modify legacy code — swallow it in governance wrappers.

---

## Sprint 26 Architecture

### Four Tracks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SPRINT 26: FOUNDATION PROOF                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Track A: THE RIVER (Data Integrity Proof)                                 │
│  ├── Day 0.5: Schema Lockdown (ICT Data Contract)                          │
│  ├── Day 1: Mirror Test (IBKR ↔ Dukascopy equivalence)                     │
│  ├── Day 1.5: Liar's Paradox (Truth Teller awakeness)                      │
│  ├── Day 2: Chaos Bunny (gaps, latency injection)                          │
│  ├── Day 2.5: Historical Nukes (JPY carry, vol spikes)                     │
│  └── Deliverable: RIVER_VALIDATION_REPORT.md                               │
│                                                                             │
│  Track B: THE SKELETON (Governance Foundation)                              │
│  ├── Day 1-2: GovernanceInterface implementation                           │
│  ├── Day 2-3: Halt test harness (<50ms proof)                              │
│  ├── Day 3-4: Quality telemetry stub (Truth Teller schema)                 │
│  └── Deliverable: phoenix/governance/ module                               │
│                                                                             │
│  Track C: THE ORACLE (Cold Start + Calibration)                            │
│  ├── Day 2: NEX salvage compatibility audit                                │
│  ├── Day 3: Visual Anchor Map (CSO sight calibration)                      │
│  ├── Day 3.5: Minimum viable Dynasty definition                            │
│  ├── Day 4: Fallback strategy (Plan B if Olya session thin)                │
│  └── Deliverable: COLD_START_STRATEGY.md + VISUAL_ANCHOR_MAP.md            │
│                                                                             │
│  Track D: THE HANDS (Dispatcher/Worker Control)                            │
│  ├── Day 1-2: TMUX C2 skeleton                                             │
│  ├── Day 2-3: Worker spawn/kill integration                                │
│  ├── Day 3-4: Halt signal propagation test                                 │
│  └── Deliverable: phoenix/dispatcher/ module                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Track Dependencies

```
Day 0.5: Schema Lockdown ─────────────────────────┐
                                                  │
Day 1:   Track A (Mirror) ─────┐                  │
         Track D (TMUX C2) ────┼── Parallel ──────┤
                               │                  │
Day 2:   Track A (Liar) ───────┤                  │
         Track B (GovInterface)┼── Parallel       │
         Track C (NEX Audit) ──┘                  │
                                                  │
Day 3:   Track A (Chaos) ──────┐                  │
         Track B (Halt Tests) ─┼── Parallel       │
         Track C (Visual Map) ─┘                  │
                                                  │
Day 4:   Track A (Nukes) ──────┐                  │
         Track B (Telemetry) ──┼── Converge ──────┘
         Track C (Fallback) ───┤
         Track D (Halt Prop) ──┘
                               │
                               ▼
                    EXIT GATE VALIDATION
```

---

## Track A: The River (Data Integrity Proof)

### A.0: Schema Lockdown (Day 0.5) — PREREQUISITE

**Purpose:** Finalize ICT Data Contract before any tests. If IBKR and Dukascopy disagree on column semantics, Mirror Test fails on definitions, not data.

**Deliverable:** `phoenix/contracts/ICT_DATA_CONTRACT.md`

**Content:**

| Layer | Column Set | Definition |
|-------|------------|------------|
| **Raw (6 cols)** | timestamp, open, high, low, close, volume | UTC timestamp, 1-min bars, volume = ??? |
| **Enriched (68+ cols)** | Per 12-layer spec | Exact column names, types, semantics |

**Critical Question to Resolve:**
- Is Dukascopy volume (tick count) compatible with IBKR volume (traded shares)?
- Answer determines whether volume-based ICT markers (sweep strength) are cross-vendor comparable.

**Exit Gate:** ICT_DATA_CONTRACT.md signed off before Mirror Test begins.

---

### A.1: Mirror Test (Day 1)

**Purpose:** Prove vendor equivalence via structural parity.

**Test Specification:**

```python
# audit_vendor_mirror.py

def mirror_test(symbol: str = "EURUSD", hours: int = 48) -> MirrorReport:
    """
    Compare IBKR and Dukascopy for structural equivalence.
    
    INVARIANT: ICT markers must be BIT-IDENTICAL.
    We don't care if price differs by 0.1 pip.
    We care if is_fvg, is_sweep, is_ob differ AT ALL.
    """
    
    # PHASE 1: Load 48-hour window from both vendors
    ibkr_raw = load_vendor("ibkr", symbol, hours)
    duka_raw = load_vendor("dukascopy", symbol, hours)
    
    # PHASE 2: Normalize timeline (UTC, sequence_id alignment)
    ibkr_norm, duka_norm = normalize_timeline(ibkr_raw, duka_raw)
    
    # PHASE 3: Pass BOTH through SAME enrichment engine
    ibkr_enriched = enrich(ibkr_norm)  # 68 columns
    duka_enriched = enrich(duka_norm)  # 68 columns
    
    # PHASE 4: XOR comparison on boolean markers
    marker_cols = ["is_fvg", "is_sweep", "is_ob", "is_bos", "is_choch", ...]
    xor_sum = 0
    divergences = []
    
    for col in marker_cols:
        xor = ibkr_enriched[col] ^ duka_enriched[col]
        if xor.any():
            xor_sum += xor.sum()
            divergences.append({
                "column": col,
                "bars": xor[xor].index.tolist()
            })
    
    # PHASE 5: Verdict
    return MirrorReport(
        symbol=symbol,
        window_hours=hours,
        bars_compared=len(ibkr_enriched),
        xor_sum=xor_sum,
        divergences=divergences,
        verdict="PASS" if xor_sum == 0 else "FAIL"
    )
```

**Pass Criteria:** `XOR_SUM == 0` across 2,880 bars (48hr)

**Fail Action:** HALT — Fix vendor seam before proceeding.

**Owl Enhancement:** If not bit-identical, quantify fragility:
- 99.9% match → Acceptable, document edge cases
- 80% match → ICT logic too sensitive to vendor noise, needs hardening

---

### A.2: Liar's Paradox Test (Day 1.5)

**Purpose:** Verify Truth Teller (INV-CONTRACT-3) is ACTIVE guardian, not passive observer.

**Test Specification:**

```python
# test_liars_paradox.py

def test_liars_paradox():
    """
    Inject intentional lie, verify system catches it.
    
    Mirror Test proves sources match.
    Liar's Paradox proves the guardian is AWAKE.
    """
    
    # PHASE 1: Get clean data
    clean_data = load_vendor("ibkr", "EURUSD", hours=1)
    
    # PHASE 2: Inject 1-pip lie on random bar
    poisoned_data = clean_data.copy()
    poison_idx = random.choice(poisoned_data.index)
    poisoned_data.loc[poison_idx, "close"] += 0.0001  # 1 pip
    
    # PHASE 3: Run through canonical pipeline
    quality_before = get_quality_score()
    result = process_through_pipeline(poisoned_data)
    quality_after = get_quality_score()
    
    # PHASE 4: Verify detection
    assert quality_after < quality_before, "Lie passed undetected!"
    assert result.alerts, "No alert raised for poisoned data!"
    
    # SUCCESS: Quality degradation detected within 1 processing cycle
```

**Pass Criteria:** Injected 1-pip error detected within 1 cycle

**Fail Action:** HALT — Truth Teller broken, cannot trust data quality.

---

### A.3: Chaos Bunny — Gaps (Day 2)

**Purpose:** Test degradation paths under gap injection.

**Test Specification:**

```python
# test_chaos_gaps.py

def test_chaos_bunny_gaps():
    """
    Inject 10% gaps, verify graceful degradation.
    System must NOT crash. Quality score must DROP.
    """
    
    # Load 24hr clean data
    clean_data = load_vendor("ibkr", "EURUSD", hours=24)
    
    # Inject 10% gaps (random bar removal)
    gap_count = int(len(clean_data) * 0.10)
    gap_indices = random.sample(list(clean_data.index), gap_count)
    gapped_data = clean_data.drop(gap_indices)
    
    # Process through pipeline
    try:
        result = process_through_pipeline(gapped_data)
        
        # Verify: No crash
        assert result is not None, "Pipeline crashed on gaps!"
        
        # Verify: Quality score dropped
        assert result.quality_score < 0.95, "Quality didn't degrade with 10% gaps!"
        
        # Verify: Gaps flagged (not forward-filled silently)
        assert result.gap_count == gap_count, "Gaps not properly flagged!"
        
    except Exception as e:
        pytest.fail(f"Pipeline crashed: {e}")
```

**Pass Criteria:** 10% gap injection → quality score drops, no crash

**Fail Action:** Fix degradation paths.

---

### A.4: Chaos Bunny — Latency (Day 2.5)

**Purpose:** Test stale data handling.

**Test Specification:**

```python
# test_chaos_latency.py

def test_chaos_bunny_latency():
    """
    Inject 500ms latency spike, verify stale flag triggers.
    """
    
    # Simulate perception that's 500ms stale
    perception = get_current_perception()
    perception.timestamp = datetime.now(UTC) - timedelta(milliseconds=500)
    
    # Attempt entry decision
    decision = make_entry_decision(perception)
    
    # Verify: Entry blocked due to stale perception
    assert decision.blocked, "Entry allowed on stale perception!"
    assert decision.block_reason == "STALE_PERCEPTION"
    
    # Verify: Exit still permitted (INV-DATA-3)
    exit_decision = make_exit_decision(perception)
    assert not exit_decision.blocked, "Exit blocked on stale perception!"
```

**Pass Criteria:** 500ms spike → stale flag triggers, entries blocked

**Fail Action:** Fix perception freshness handling.

---

### A.5: Historical Nukes (Day 3)

**Purpose:** Prove resilience on regime extremes.

**Test Events:**

| Event | Date Range | Characteristic |
|-------|------------|----------------|
| **2024 JPY Carry Unwind** | Aug 2024 | Flash crash, gap cascade |
| **2023 Vol Spikes** | Mar 2023 | Banking crisis volatility |

**Test Specification:**

```python
# test_historical_nukes.py

@pytest.mark.parametrize("event,start,end", [
    ("jpy_carry_unwind", "2024-08-01", "2024-08-10"),
    ("vol_spikes_2023", "2023-03-08", "2023-03-20"),
])
def test_historical_nuke(event: str, start: str, end: str):
    """
    Replay historical regime extremes without crash.
    Document edge cases for future reference.
    """
    
    # Load historical data
    historical = load_historical("EURUSD", start, end)
    
    # Process through pipeline
    try:
        result = process_through_pipeline(historical)
        
        # Verify: No crash
        assert result is not None, f"Pipeline crashed on {event}!"
        
        # Document: Edge cases found
        if result.warnings:
            log_regime_edge_cases(event, result.warnings)
            
    except Exception as e:
        pytest.fail(f"Pipeline crashed on {event}: {e}")
```

**Pass Criteria:** Both events replay without crash

**Fail Action:** Document regime edge cases, assess if blocking.

---

### A.6: Deliverable

**File:** `docs/RIVER_VALIDATION_REPORT.md`

**Content:**

```markdown
# RIVER VALIDATION REPORT

**Sprint:** 26
**Date:** [DATE]
**Status:** PASS/FAIL

## Test Matrix

| Test | Result | Notes |
|------|--------|-------|
| Schema Lockdown | PASS/FAIL | ICT_DATA_CONTRACT signed |
| Mirror Test (48hr) | PASS/FAIL | XOR_SUM = [N] |
| Liar's Paradox | PASS/FAIL | Detection latency: [N]ms |
| Chaos: Gaps (10%) | PASS/FAIL | Quality degraded: [Y/N] |
| Chaos: Latency (500ms) | PASS/FAIL | Entries blocked: [Y/N] |
| Historical: JPY Carry | PASS/FAIL | Edge cases: [list] |
| Historical: Vol Spikes | PASS/FAIL | Edge cases: [list] |

## Structural Convergence Score

If Mirror Test not bit-identical:
- Match rate: [N]%
- Divergent markers: [list]
- Assessment: [Trade/Harden/Block]

## River Health Baseline

- Completeness: [N]%
- Temporal regularity: [N]%  
- Semantic validity: [N]%
- Overall: [N]%

## Exit Gate

- [ ] All tests PASS or documented exceptions
- [ ] River Health > 95%
- [ ] Degradation paths verified
```

---

## Track B: The Skeleton (Governance Foundation)

### B.1: GovernanceInterface Implementation (Day 1-2)

**Purpose:** Create base class all Phoenix organs must inherit.

**Location:** `phoenix/governance/interface.py`

**Implementation:**

```python
"""
GovernanceInterface — Base class for Phoenix organs.
Contract enforced at compilation, not hope.

Source: GOVERNANCE_INTERFACE.py from recombobulation_pack.md
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import time

class ForgeResponse(Enum):
    RECOVERABLE = "recoverable"
    DEGRADED = "degraded"  
    CRITICAL = "critical"

class ModuleTier(Enum):
    TIER_0 = "infrastructure"  # No capital impact
    TIER_1 = "advisory"        # Influences, doesn't execute
    TIER_2 = "capital"         # Requires human gate

@dataclass
class QualityTelemetry:
    quality_score: float        # 0.0 to 1.0
    source_identity: str        # "ibkr", "dukascopy", etc.
    is_synthetic: bool          # True if gap-filled
    latency_ms: float           # Perception age
    timestamp: float            # When measured

class GovernanceException(Exception):
    """Typed exception for Forge handling."""
    def __init__(self, response_type: ForgeResponse, message: str, context: Dict[str, Any]):
        self.response_type = response_type
        self.message = message
        self.context = context
        super().__init__(message)

class GovernanceInterface(ABC):
    """
    Base class all Phoenix organs must inherit.
    
    Enforces:
    - INV-CONTRACT-1: Deterministic state machine
    - INV-CONTRACT-2: <50ms halt obligation
    - INV-CONTRACT-3: Data quality telemetry
    - INV-CONTRACT-5: Typed error response
    - INV-CONTRACT-7: Tier declaration
    - INV-CONTRACT-8: Chaos compatibility
    """
    
    def __init__(self):
        self._halt_requested = False
        self._state_hash = None
        self._sequence_id = 0
    
    # ═══════════════════════════════════════════════════════════
    # INV-CONTRACT-7: TIER DECLARATION
    # ═══════════════════════════════════════════════════════════
    @property
    @abstractmethod
    def module_tier(self) -> ModuleTier:
        """Declare capital proximity."""
        pass
    
    @property
    @abstractmethod
    def enforced_invariants(self) -> List[str]:
        """Which INV-* this module enforces."""
        pass
    
    # ═══════════════════════════════════════════════════════════
    # INV-CONTRACT-1: DETERMINISTIC STATE MACHINE
    # ═══════════════════════════════════════════════════════════
    @abstractmethod
    def process_state(
        self, 
        input_data: Any, 
        prior_state: Optional[Dict] = None
    ) -> Dict:
        """
        Pure state transition: S_n = f(S_{n-1}, I_n)
        
        Output MUST include:
        - sequence_id: int (monotonic)
        - prior_state_hash: str (chain integrity)
        - timestamp: datetime (from injected clock)
        """
        pass
    
    def compute_state_hash(self, state: Dict) -> str:
        """Deterministic hash for replay verification."""
        return hashlib.sha256(
            str(sorted(state.items())).encode()
        ).hexdigest()[:16]
    
    # ═══════════════════════════════════════════════════════════
    # INV-CONTRACT-2: <50ms HALT OBLIGATION
    # ═══════════════════════════════════════════════════════════
    def request_halt(self):
        """Called by Forge to request graceful shutdown."""
        self._halt_requested = True
    
    def check_halt(self) -> bool:
        """
        MUST be called between processing steps.
        
        CRITICAL: If building a while loop, insert:
            if self.check_halt():
                return self._graceful_shutdown()
        """
        return self._halt_requested
    
    def _graceful_shutdown(self) -> Dict:
        """Return safe shutdown state."""
        return {
            "status": "halted",
            "sequence_id": self._sequence_id,
            "state_hash": self._state_hash,
            "halt_time": time.time()
        }
    
    # ═══════════════════════════════════════════════════════════
    # INV-CONTRACT-3: DATA QUALITY TELEMETRY
    # ═══════════════════════════════════════════════════════════
    @abstractmethod
    def get_quality_telemetry(self) -> QualityTelemetry:
        """Report current data quality metrics."""
        pass
    
    # ═══════════════════════════════════════════════════════════
    # INV-CONTRACT-5: TYPED ERROR RESPONSE
    # ═══════════════════════════════════════════════════════════
    @abstractmethod
    def handle_error(self, error: Exception) -> ForgeResponse:
        """
        Map exceptions to Forge actions.
        No silent failures allowed.
        
        Returns:
        - RECOVERABLE: Log + continue
        - DEGRADED: Disable sub-layer, continue core
        - CRITICAL: EMERGENCY_HALT
        """
        pass
    
    # ═══════════════════════════════════════════════════════════
    # INV-CONTRACT-8: CHAOS COMPATIBILITY
    # ═══════════════════════════════════════════════════════════
    @abstractmethod
    def get_failure_modes(self) -> List[str]:
        """Declare known failure modes for fuzz testing."""
        pass
    
    @abstractmethod
    def get_degradation_paths(self) -> Dict[str, str]:
        """Map failure mode to degradation action."""
        pass
```

**Test Suite Required:**

```python
# phoenix/governance/tests/test_interface.py

def test_halt_obligation():
    """Verify <50ms halt compliance."""
    organ = MockOrgan()
    organ.start_processing()
    
    start = time.perf_counter()
    organ.request_halt()
    organ.wait_for_halt()
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    assert elapsed_ms < 50, f"Halt took {elapsed_ms:.1f}ms, must be <50ms"

def test_state_determinism():
    """Verify same input produces same output."""
    organ = MockOrgan()
    input_data = {"test": "data"}
    
    result1 = organ.process_state(input_data)
    result2 = organ.process_state(input_data)
    
    assert result1["state_hash"] == result2["state_hash"]
```

**Exit Gate:** Interface implemented, halt test passing.

---

### B.2: Halt Test Harness (Day 2-3)

**Purpose:** Prove <50ms halt on mock organ.

**Location:** `phoenix/governance/tests/test_halt_harness.py`

**Implementation:**

```python
"""
Halt Test Harness — Prove sovereignty membrane works.

INVARIANT: Kill switch must work in <50ms. Always.
"""

import threading
import time
import signal
import pytest

class HaltTestHarness:
    """
    Test harness for <50ms halt obligation.
    
    Simulates various processing loads and verifies
    halt response time under each condition.
    """
    
    def __init__(self, organ: GovernanceInterface):
        self.organ = organ
        self.results = []
    
    def run_halt_test(self, load_type: str) -> float:
        """
        Run halt test under specific load.
        Returns halt time in milliseconds.
        """
        # Start processing in background
        processing_thread = threading.Thread(
            target=self._simulate_load,
            args=(load_type,)
        )
        processing_thread.start()
        
        # Wait for processing to start
        time.sleep(0.1)
        
        # Send halt signal, measure response
        start = time.perf_counter()
        self.organ.request_halt()
        processing_thread.join(timeout=0.1)  # 100ms max wait
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        self.results.append({
            "load_type": load_type,
            "halt_time_ms": elapsed_ms,
            "passed": elapsed_ms < 50
        })
        
        return elapsed_ms
    
    def _simulate_load(self, load_type: str):
        """Simulate different processing loads."""
        if load_type == "idle":
            while not self.organ.check_halt():
                time.sleep(0.001)
        elif load_type == "cpu_heavy":
            while not self.organ.check_halt():
                _ = sum(range(10000))  # CPU work
        elif load_type == "io_wait":
            while not self.organ.check_halt():
                time.sleep(0.01)  # Simulated I/O
        elif load_type == "enrichment_loop":
            # Simulate 12-layer enrichment
            for layer in range(12):
                if self.organ.check_halt():
                    return
                time.sleep(0.005)  # 5ms per layer

@pytest.mark.parametrize("load_type", [
    "idle",
    "cpu_heavy", 
    "io_wait",
    "enrichment_loop"
])
def test_halt_under_load(load_type: str):
    """Verify <50ms halt under various loads."""
    organ = MockOrgan()
    harness = HaltTestHarness(organ)
    
    halt_time = harness.run_halt_test(load_type)
    
    assert halt_time < 50, f"Halt under {load_type} took {halt_time:.1f}ms"
```

**Exit Gate:** All load types halt in <50ms.

---

### B.3: Quality Telemetry Stub (Day 3-4)

**Purpose:** Implement Truth Teller schema emitting to test sink.

**Location:** `phoenix/governance/telemetry.py`

**Implementation:**

```python
"""
Quality Telemetry — Truth Teller implementation.

INV-CONTRACT-3: No lies. Every data point carries quality score.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
import json

@dataclass
class QualityReport:
    """Single quality measurement."""
    timestamp: datetime
    source: str
    quality_score: float          # 0.0 to 1.0
    completeness: float           # 40% weight
    temporal_regularity: float    # 30% weight
    semantic_validity: float      # 30% weight
    is_degraded: bool
    degradation_reason: Optional[str] = None

@dataclass
class TelemetrySink:
    """Collects quality reports for analysis."""
    reports: List[QualityReport] = field(default_factory=list)
    
    def emit(self, report: QualityReport):
        """Record quality report."""
        self.reports.append(report)
        
        # INV-CONTRACT-3A: Degraded has teeth
        if report.is_degraded:
            self._enforce_degradation_penalty(report)
    
    def _enforce_degradation_penalty(self, report: QualityReport):
        """
        DEGRADED is not a log message. DEGRADED has TEETH.
        
        River Health < 95% → Order sizing restricted to 50%
        """
        if report.quality_score < 0.95:
            # Set global degradation flag
            self._set_position_sizing_restriction(0.5)
    
    def get_river_health(self) -> float:
        """Calculate current River health from recent reports."""
        if not self.reports:
            return 1.0
        
        recent = self.reports[-100:]  # Last 100 reports
        return sum(r.quality_score for r in recent) / len(recent)
    
    def to_json(self) -> str:
        """Export for persistence/debugging."""
        return json.dumps([
            {
                "timestamp": r.timestamp.isoformat(),
                "source": r.source,
                "quality_score": r.quality_score,
                "is_degraded": r.is_degraded
            }
            for r in self.reports
        ], indent=2)

class TruthTeller:
    """
    Quality assessment engine.
    
    Formula: 40% completeness + 30% temporal + 30% semantic
    """
    
    def __init__(self, sink: TelemetrySink):
        self.sink = sink
    
    def assess(self, data: "DataFrame", source: str) -> QualityReport:
        """
        Assess data quality and emit report.
        
        Checks:
        - Completeness: Are all expected bars present?
        - Temporal: Is rhythm steady or burst refresh?
        - Semantic: Do values make sense? (High >= Low, etc.)
        """
        completeness = self._check_completeness(data)
        temporal = self._check_temporal_regularity(data)
        semantic = self._check_semantic_validity(data)
        
        # Weighted score
        quality_score = (
            0.40 * completeness +
            0.30 * temporal +
            0.30 * semantic
        )
        
        # Determine degradation
        is_degraded = quality_score < 0.95 or semantic < 0.5
        degradation_reason = None
        if is_degraded:
            if semantic < 0.5:
                degradation_reason = "SEMANTIC_FAILURE"
            else:
                degradation_reason = "QUALITY_BELOW_THRESHOLD"
        
        report = QualityReport(
            timestamp=datetime.now(timezone.utc),
            source=source,
            quality_score=quality_score,
            completeness=completeness,
            temporal_regularity=temporal,
            semantic_validity=semantic,
            is_degraded=is_degraded,
            degradation_reason=degradation_reason
        )
        
        self.sink.emit(report)
        return report
    
    def _check_completeness(self, data) -> float:
        """Check if all expected bars present."""
        if len(data) == 0:
            return 0.0
        
        expected_bars = self._calculate_expected_bars(data)
        actual_bars = len(data)
        
        return min(1.0, actual_bars / expected_bars)
    
    def _check_temporal_regularity(self, data) -> float:
        """Check timestamp rhythm."""
        if len(data) < 2:
            return 1.0
        
        diffs = data.index.to_series().diff().dropna()
        expected_diff = pd.Timedelta(minutes=1)
        
        regular_count = (diffs == expected_diff).sum()
        return regular_count / len(diffs)
    
    def _check_semantic_validity(self, data) -> float:
        """Check data makes sense."""
        violations = 0
        total_checks = len(data) * 2
        
        # High >= Low
        violations += (data["high"] < data["low"]).sum()
        
        # High >= Open, High >= Close
        violations += (data["high"] < data["open"]).sum()
        violations += (data["high"] < data["close"]).sum()
        
        # Low <= Open, Low <= Close
        violations += (data["low"] > data["open"]).sum()
        violations += (data["low"] > data["close"]).sum()
        
        return 1.0 - (violations / total_checks) if total_checks > 0 else 0.0
```

**Exit Gate:** Truth Teller schema emitting to test sink, quality formula verified.

---

### B.4: Deliverable

**Location:** `phoenix/governance/`

**Structure:**

```
phoenix/
└── governance/
    ├── __init__.py
    ├── interface.py         # GovernanceInterface ABC
    ├── telemetry.py         # TruthTeller + TelemetrySink
    ├── exceptions.py        # GovernanceException
    └── tests/
        ├── __init__.py
        ├── test_interface.py
        ├── test_halt_harness.py
        └── test_telemetry.py
```

---

## Track C: The Oracle (Cold Start + Calibration)

### C.1: NEX Salvage Compatibility Audit (Day 2)

**Purpose:** Determine which NEX components can seed Phoenix.

**Deliverable Section in:** `COLD_START_STRATEGY.md`

**Audit Checklist:**

| Component | Location | Salvageable? | Governance Wrap Needed? |
|-----------|----------|--------------|-------------------------|
| IBKR Gateway | `~/nex/nex_lab/data/vendors/ibkr.py` | YES | YES — PhoenixRiverNode |
| Dukascopy Loader | `~/nex/nex_lab/data/loaders.py` | YES | YES — Add quality telemetry |
| 12-Layer Enrichment | `~/nex/nex_lab/data/enrichment/` | YES | YES — Add halt checks |
| 5yr Backdata | `~/nex/nex_lab/data/fx/*.parquet` | YES | NO — Static data |
| Validators | `~/nex/nex_lab/data/validators.py` | PARTIAL | YES — Remove forward-fill |

**Wrapper Pattern (Owl Directive):**

```python
# phoenix/river/ibkr_node.py

class PhoenixRiverNode(GovernanceInterface):
    """
    Governance wrapper around legacy NEX IBKR provider.
    
    Pattern: Don't modify legacy code. Swallow it.
    """
    
    def __init__(self, legacy_provider):
        super().__init__()
        self._legacy = legacy_provider
        self._truth_teller = TruthTeller(TelemetrySink())
    
    @property
    def module_tier(self) -> ModuleTier:
        return ModuleTier.TIER_0  # Infrastructure
    
    @property
    def enforced_invariants(self) -> List[str]:
        return ["INV-DATA-1", "INV-DATA-2", "INV-DATA-3"]
    
    def process_state(self, input_data: Any, prior_state: Optional[Dict] = None) -> Dict:
        # Check halt before processing
        if self.check_halt():
            return self._graceful_shutdown()
        
        # Call legacy provider
        raw_data = self._legacy.get_data(input_data)
        
        # Assess quality (new governance layer)
        quality = self._truth_teller.assess(raw_data, "ibkr")
        
        # Build governed state
        state = {
            "sequence_id": self._sequence_id,
            "prior_state_hash": self._state_hash,
            "data": raw_data,
            "quality": quality,
            "timestamp": datetime.now(timezone.utc)
        }
        
        self._sequence_id += 1
        self._state_hash = self.compute_state_hash(state)
        
        return state
```

---

### C.2: Visual Anchor Map (Day 3)

**Purpose:** Define what CSO "sees" vs what Olya sees.

**Risk (Owl Identified):** If CSO looks at 15m chart but Olya talks about 1m fractal, Intertwine fails instantly.

**Deliverable:** `docs/VISUAL_ANCHOR_MAP.md`

**Content:**

```markdown
# VISUAL ANCHOR MAP

**Purpose:** Calibrate CSO sight to Olya's screen.

## Chart Configuration Baseline

| Parameter | Olya's Setting | CSO Must Match |
|-----------|----------------|----------------|
| Primary Timeframe | [TBD] | YES |
| FVG Visualization | [Color/Style TBD] | YES |
| Session Markers | [LOKZ/NYOKZ style TBD] | YES |
| Swing Point Labels | [TBD] | YES |
| Indicator Set | [TBD] | YES |

## Capture Requirements

| Element | Capture Method | Frequency |
|---------|----------------|-----------|
| Chart Screenshot | Ghost Worker | Every 60s |
| Voice Stream | Local Buffer | Real-time |
| Cursor Position | [TBD] | [TBD] |

## Calibration Session

Before CSO goes live, Olya walks through her setup:
1. Open standard chart configuration
2. CSO screenshots and maps elements
3. Olya confirms: "Yes, that's what I see"
4. Map locked as VISUAL_BASELINE_v1

## Drift Detection

If Olya changes chart settings mid-session:
- CSO detects visual drift
- Flags for recalibration
- Does NOT certify beads until aligned
```

**Action Required:** Schedule 30-min Olya calibration session.

---

### C.3: Minimum Viable Dynasty (Day 3.5)

**Purpose:** Define how many certified beads before CSO is "useful."

**Deliverable Section in:** `COLD_START_STRATEGY.md`

**Analysis:**

| Dynasty Size | CSO Capability | Use Case |
|--------------|----------------|----------|
| 0 beads | Recording only | Bootstrap mode |
| 10 beads | Pattern hints | Basic correlation |
| 50 beads | Session memory | "You mentioned this before" |
| 200+ beads | Doctrine inference | "This contradicts INV-OLYA-017" |

**Minimum Viable:** 50 certified beads across 3+ trading sessions.

---

### C.4: Fallback Strategy (Day 4)

**Purpose:** Plan B if Olya's first session is thin.

**Deliverable Section in:** `COLD_START_STRATEGY.md`

**Plan B: NEX Replay Analysis**

If first Olya session produces <10 certified beads:

1. **Feed Historical Data:** Load 2024 JPY carry unwind period
2. **Load Old Journals:** If Olya has trading notes, ingest them
3. **CSO Narrates Past:** Ask CSO to narrate historical data as if live
4. **Validation:** Compare CSO narrative to Olya's memory of that period
5. **Gate:** If CSO can't accurately narrate past, it can't narrate future

**Exit Gate:** Plan B documented, ready to execute if needed.

---

### C.5: Deliverables

**Files:**
- `docs/COLD_START_STRATEGY.md`
- `docs/VISUAL_ANCHOR_MAP.md`

---

## Track D: The Hands (Dispatcher/Worker Control)

### D.1: TMUX C2 Skeleton (Day 1-2)

**Purpose:** Allow Dispatcher to spawn/control Workers via TMUX.

**Location:** `phoenix/dispatcher/tmux_c2.py`

**Implementation:**

```python
"""
TMUX Command & Control — Worker management.

Per HIVE_OPS.md, this enables:
- Dispatcher spawning Workers in tmux
- Health monitoring
- Halt signal propagation
"""

import subprocess
import time
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class WorkerStatus:
    session: str
    window: str
    pid: Optional[int]
    is_alive: bool
    last_output: str

class TmuxC2:
    """
    TMUX Command & Control for Worker management.
    
    Responsibilities:
    - Spawn workers in tmux windows
    - Monitor health via output sampling
    - Propagate halt signals
    - Kill workers on timeout
    """
    
    def __init__(self, session_name: str = "hive"):
        self.session_name = session_name
        self.workers: Dict[str, WorkerStatus] = {}
    
    def spawn_worker(self, window_name: str, command: str) -> WorkerStatus:
        """
        Spawn a worker in a new tmux window.
        
        Args:
            window_name: Name for the tmux window
            command: Command to run in the window
        """
        # Create window
        subprocess.run([
            "tmux", "new-window",
            "-t", self.session_name,
            "-n", window_name
        ], check=True)
        
        # Send command
        subprocess.run([
            "tmux", "send-keys",
            "-t", f"{self.session_name}:{window_name}",
            command, "C-m"
        ], check=True)
        
        status = WorkerStatus(
            session=self.session_name,
            window=window_name,
            pid=None,  # Would need to extract from tmux
            is_alive=True,
            last_output=""
        )
        
        self.workers[window_name] = status
        return status
    
    def send_halt_signal(self, window_name: str) -> float:
        """
        Send halt signal to worker, measure response time.
        
        Returns: Halt time in milliseconds
        """
        start = time.perf_counter()
        
        # Send interrupt
        subprocess.run([
            "tmux", "send-keys",
            "-t", f"{self.session_name}:{window_name}",
            "C-c"
        ], check=True)
        
        # Wait for exit (max 100ms)
        for _ in range(10):
            if not self._is_window_active(window_name):
                break
            time.sleep(0.01)
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms
    
    def broadcast_halt(self) -> Dict[str, float]:
        """
        Send halt to ALL workers.
        
        Returns: Dict of window_name -> halt_time_ms
        """
        results = {}
        for window_name in self.workers:
            results[window_name] = self.send_halt_signal(window_name)
        return results
    
    def get_worker_output(self, window_name: str, lines: int = 20) -> str:
        """Capture recent output from worker window."""
        result = subprocess.run([
            "tmux", "capture-pane",
            "-t", f"{self.session_name}:{window_name}",
            "-p", "-S", f"-{lines}"
        ], capture_output=True, text=True)
        return result.stdout
    
    def _is_window_active(self, window_name: str) -> bool:
        """Check if window still has active process."""
        result = subprocess.run([
            "tmux", "list-windows",
            "-t", self.session_name,
            "-F", "#{window_name}"
        ], capture_output=True, text=True)
        return window_name in result.stdout
```

---

### D.2: Halt Signal Propagation Test (Day 3-4)

**Purpose:** Verify halt signal reaches all workers in <50ms.

**Test:**

```python
# phoenix/dispatcher/tests/test_halt_propagation.py

def test_broadcast_halt():
    """Verify halt reaches all workers in <50ms."""
    c2 = TmuxC2("test_hive")
    
    # Spawn 3 workers
    c2.spawn_worker("worker1", "sleep 999")
    c2.spawn_worker("worker2", "sleep 999")
    c2.spawn_worker("worker3", "sleep 999")
    
    time.sleep(0.5)  # Let workers start
    
    # Broadcast halt
    results = c2.broadcast_halt()
    
    # Verify all halted in <50ms
    for window, halt_time in results.items():
        assert halt_time < 50, f"{window} took {halt_time:.1f}ms to halt"
```

---

### D.3: Deliverable

**Location:** `phoenix/dispatcher/`

**Structure:**

```
phoenix/
└── dispatcher/
    ├── __init__.py
    ├── tmux_c2.py           # TMUX Command & Control
    ├── worker_manager.py    # Worker lifecycle
    └── tests/
        ├── __init__.py
        └── test_halt_propagation.py
```

---

## Effort Estimates

| Track | Phase | Effort | Priority |
|-------|-------|--------|----------|
| **A** | Schema Lockdown | 1 hr | P0 |
| **A** | Mirror Test | 3 hrs | P0 |
| **A** | Liar's Paradox | 1.5 hrs | P0 |
| **A** | Chaos: Gaps | 2 hrs | P1 |
| **A** | Chaos: Latency | 1.5 hrs | P1 |
| **A** | Historical Nukes | 2 hrs | P1 |
| **B** | GovernanceInterface | 3 hrs | P0 |
| **B** | Halt Harness | 2 hrs | P0 |
| **B** | Quality Telemetry | 2 hrs | P1 |
| **C** | NEX Salvage Audit | 2 hrs | P1 |
| **C** | Visual Anchor Map | 1.5 hrs | P1 |
| **C** | Min Viable Dynasty | 1 hr | P2 |
| **C** | Fallback Strategy | 1 hr | P2 |
| **D** | TMUX C2 | 3 hrs | P1 |
| **D** | Halt Propagation | 2 hrs | P1 |
| **Total** | | **~28 hrs** | |

**Fits within 3-4 sprint days with parallel execution.**

---

## Execution Model

### Option 1: HIVE Execution (Recommended for Parallel)

Per `HIVE_OPS.md`:

```bash
# 1. Start Watchdog
tmux new-session -d -s hive -n watchdog
tmux send-keys -t hive:watchdog 'cd /Users/echopeso/God_Mode && source .venv/bin/activate && python3 -m god_mode.patrols.watchdog --tier 1' Enter

# 2. Create Planner window
tmux new-window -t hive -n planner
tmux send-keys -t hive:planner 'cd /Users/echopeso/God_Mode && claude --model sonnet --permission-mode bypassPermissions' Enter

# 3. Create Worker windows (one per track)
tmux new-window -t hive -n worker-river     # Track A
tmux new-window -t hive -n worker-skeleton  # Track B
tmux new-window -t hive -n worker-oracle    # Track C
tmux new-window -t hive -n worker-hands     # Track D
```

**CTO (Web/Desktop):** Strategy, brief handoffs
**Dispatcher (Claude Code):** Coordinates HIVE, boardroom ops
**Workers (Sonnet):** Execute track tasks

### Option 2: Cursor Execution (Recommended for Deep Focus)

Execute sequentially with Opus in Cursor:
1. Day 1: Track A (Schema + Mirror) + Track D (TMUX C2)
2. Day 2: Track A (Liar + Chaos) + Track B (GovInterface)
3. Day 3: Track B (Halt + Telemetry) + Track C (Audit + Visual)
4. Day 4: Track A (Nukes) + Track C (Fallback) + Integration

---

## Exit Gates

### Sprint 26 → 27 Gate

| Criterion | Target | Blocking? |
|-----------|--------|-----------|
| Schema Lockdown | ICT_DATA_CONTRACT.md signed | YES |
| Mirror Test | XOR_SUM == 0 or documented exceptions | YES |
| Liar's Paradox | Detection in <1 cycle | YES |
| Chaos: Gaps | No crash, quality degraded | YES |
| Chaos: Latency | Entries blocked on stale | YES |
| Historical Nukes | No crash | NO (document edge cases) |
| GovernanceInterface | Implemented + halt test passing | YES |
| Quality Telemetry | Emitting to test sink | YES |
| NEX Salvage Audit | Report complete | NO |
| Visual Anchor Map | Document ready | NO (can iterate) |
| Cold Start Strategy | Documented | NO |
| TMUX C2 | Spawn/halt working | YES |

**Sprint 27 Unlocks:** CSO implementation (first runtime organ)

---

## Key Files for Fresh CTO

| File | Purpose |
|------|---------|
| **This brief** | Sprint 26 mission + execution |
| `docs/VISION_v4.md` | North Star |
| `docs/ORIENTATION.md` | Quick context |
| `docs/PHOENIX_MANIFESTO.md` | Character handles |
| `docs/recombobulation_pack.md` | Deep reference |
| `docs/DATA_PIPELINE_AUTOPSY.md` | NEX analysis |
| `hive/HIVE_OPS.md` | HIVE execution model |

---

## Boardroom Handoff

```bash
# Emit Sprint 26 start bead
python3 boardroom/boardroom.py emit cto handoff S26 "Sprint 26 brief approved. Phoenix Foundation Proof begins. Four tracks: River, Skeleton, Oracle, Hands."
```

---

## Closing Notes

Sprint 26 is the **First Physical Act of Phoenix**.

We're not building a trader yet. We're building the floor that will hold Olya's Oracle and G's Sovereign Capital.

**By the end of Sprint 26:**
- The River is proven clean (or we know exactly where it's not)
- The Governance skeleton can halt anything in <50ms
- The Cold Start strategy is documented
- The Dispatcher can control Workers

**Sprint 27 unlocks CSO** — the first organ that drinks from the River.

---

**The forge is the OS. Phoenix is the first app. The River is sacred.**

**OINK OINK.** 🐗🔥

---

*Brief drafted: 2026-01-23*
*CTO: Claude Opus (Cursor)*
*Wise Owl Feedback: Integrated*
*Status: READY FOR EXECUTION*
