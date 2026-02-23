# CSO DYNASTY SPECIFICATION

**SPRINT:** 26.TRACK_C  
**DATE:** 2026-01-25  
**PURPOSE:** Define minimum viable CSO state that survives sessions

---

## OVERVIEW

Dynasty = state that persists across sessions.
CSO builds judgment over time — decisions inform future decisions.

---

## STATE CLASSIFICATION

| State Type | Lifetime | Storage | Recovery |
|------------|----------|---------|----------|
| **Persistent** | Survives restart | Boardroom DB | Load from DB |
| **Session** | Current process | Memory | Recompute |
| **Ephemeral** | Per computation | Stack | Discard |

---

## PERSISTENT STATE

### CSO Decision History (Beads)

| Field | Type | Persistence Layer | Notes |
|-------|------|-------------------|-------|
| `decision_id` | str | Boardroom.beads | UUID |
| `timestamp` | datetime | Boardroom.beads | UTC |
| `symbol` | str | Boardroom.beads | EURUSD etc |
| `direction` | enum | Boardroom.beads | LONG/SHORT/NEUTRAL |
| `confidence` | float | Boardroom.beads | 0.0-1.0 |
| `reasoning` | dict | Boardroom.beads | 4Q gate results |
| `htf_context_hash` | str | Boardroom.beads | State at decision |
| `outcome` | enum | Boardroom.beads | PENDING/WIN/LOSS/SKIP |
| `outcome_pips` | float | Boardroom.beads | Null until resolved |

### Reference State

| Field | Type | Persistence Layer | Notes |
|-------|------|-------------------|-------|
| `last_pdh` | dict[symbol, float] | JSON file | Previous day highs |
| `last_pdl` | dict[symbol, float] | JSON file | Previous day lows |
| `last_pwh` | dict[symbol, float] | JSON file | Previous week highs |
| `last_pwl` | dict[symbol, float] | JSON file | Previous week lows |
| `active_fvgs` | list[FVG] | JSON file | Unfilled gaps |
| `active_obs` | list[OB] | JSON file | Unmitigated blocks |
| `swing_points` | list[Swing] | JSON file | Recent HH/HL/LH/LL |

### Performance Tracking

| Field | Type | Persistence Layer | Notes |
|-------|------|-------------------|-------|
| `decisions_total` | int | Boardroom.metrics | All-time count |
| `decisions_won` | int | Boardroom.metrics | Winning decisions |
| `decisions_lost` | int | Boardroom.metrics | Losing decisions |
| `win_rate_30d` | float | Boardroom.metrics | Rolling 30-day |
| `avg_confidence` | float | Boardroom.metrics | Confidence calibration |
| `confidence_accuracy` | dict | Boardroom.metrics | Confidence vs outcome |

### Model Parameters

| Field | Type | Persistence Layer | Notes |
|-------|------|-------------------|-------|
| `sweep_threshold_pips` | float | Config JSON | Calibrated value |
| `fvg_min_size_atr` | float | Config JSON | Calibrated value |
| `ob_lookback_bars` | int | Config JSON | Calibrated value |
| `confidence_bias` | float | Config JSON | Adjust over-/under-confidence |

---

## SESSION STATE (Ephemeral)

### Live Context

| Field | Type | Lifetime | Recovery |
|-------|------|----------|----------|
| `current_bar` | Bar | Per bar | Stream from River |
| `current_position` | dict | Session | Recompute from last decision |
| `pending_signals` | list | Session | Recompute |
| `warmup_state` | enum | Session | Check bars loaded |

### Computed Cache

| Field | Type | Lifetime | Recovery |
|-------|------|----------|----------|
| `enriched_buffer` | deque[Bar] | Session | Re-enrich last N |
| `htf_cache` | dict | Session | Recompute from daily |
| `alignment_cache` | dict | Session | Recompute |
| `quality_metrics` | dict | Session | Recompute |

### Connection State

| Field | Type | Lifetime | Recovery |
|-------|------|----------|----------|
| `river_connection` | handle | Session | Reconnect |
| `boardroom_connection` | handle | Session | Reconnect |
| `halt_signal` | HaltSignal | Session | Clear on start |

---

## BEAD SCHEMA

### CSO Decision Bead

```yaml
bead_type: cso_decision
version: 1.0

fields:
  # Identity
  decision_id: str           # UUID
  timestamp: datetime        # UTC ISO format
  sprint: str               # e.g., "S26"
  
  # Context
  symbol: str               # EURUSD
  timeframe: str            # 1m (entry TF)
  
  # Decision
  direction: enum           # LONG | SHORT | NEUTRAL
  confidence: float         # 0.0-1.0
  
  # 4Q Gate Results
  q1_htf_order_flow:
    daily_bias: str         # bullish | bearish | neutral
    weekly_bias: str
    pass: bool
    
  q2_dealing_range:
    zone: str               # premium | discount | equilibrium
    ipda_context: str
    pass: bool
    
  q3_pda_destination:
    target_type: str        # pdh | pdl | fvg | ob
    target_price: float
    pass: bool
    
  q4_timing:
    session: str            # asia | london | ny
    kz_active: bool
    pass: bool
    
  gate_pass: bool           # All 4 passed
  
  # State Hash
  state_hash: str           # compute_state_hash() at decision
  
  # Outcome (filled later)
  outcome: enum             # PENDING | WIN | LOSS | SKIP | INVALIDATED
  outcome_reason: str       # "Target hit" | "Stop hit" | "Time expired"
  outcome_pips: float       # Profit/loss in pips
  outcome_timestamp: datetime

example:
  decision_id: "cso-2026-01-25-14-30-001"
  timestamp: "2026-01-25T14:30:00Z"
  sprint: "S26"
  symbol: "EURUSD"
  timeframe: "1m"
  direction: "LONG"
  confidence: 0.85
  q1_htf_order_flow:
    daily_bias: "bullish"
    weekly_bias: "bullish"
    pass: true
  q2_dealing_range:
    zone: "discount"
    ipda_context: "ipda_20d_discount"
    pass: true
  q3_pda_destination:
    target_type: "fvg"
    target_price: 1.0920
    pass: true
  q4_timing:
    session: "london"
    kz_active: true
    pass: true
  gate_pass: true
  state_hash: "a1b2c3d4e5f6"
  outcome: "PENDING"
```

### CSO Insight Bead

```yaml
bead_type: cso_insight
version: 1.0

fields:
  insight_id: str
  timestamp: datetime
  category: enum            # PATTERN | CORRELATION | CALIBRATION
  content: str              # Human-readable insight
  evidence: dict            # Supporting data
  confidence: float
  
example:
  insight_id: "cso-insight-001"
  timestamp: "2026-01-25T18:00:00Z"
  category: "CALIBRATION"
  content: "Confidence scores overestimate win rate by 8%"
  evidence:
    sample_size: 50
    avg_confidence: 0.82
    actual_win_rate: 0.74
  confidence: 0.90
```

---

## RECOVERY FROM BEADS

### State Reconstruction Procedure

```python
def reconstruct_cso_state(boardroom: Boardroom) -> CSOState:
    """Rebuild CSO state from Boardroom beads."""
    
    # 1. Load all CSO decision beads
    decisions = boardroom.query_beads(
        role='cso',
        type='decision',
        limit=1000
    )
    
    # 2. Build performance metrics
    metrics = compute_performance_metrics(decisions)
    
    # 3. Load latest reference state
    reference = boardroom.get_latest('cso_reference_state')
    
    # 4. Validate state hash
    expected_hash = decisions[-1].state_hash if decisions else None
    
    # 5. Return reconstructed state
    return CSOState(
        decisions=decisions,
        metrics=metrics,
        reference=reference,
        last_state_hash=expected_hash
    )
```

### Bead Query Patterns

```python
# Get last N decisions for symbol
decisions = boardroom.query_beads(
    role='cso',
    type='decision',
    filters={'symbol': 'EURUSD'},
    order='timestamp DESC',
    limit=100
)

# Get decisions with specific outcome
wins = boardroom.query_beads(
    role='cso',
    type='decision',
    filters={'outcome': 'WIN'}
)

# Get insights for calibration
insights = boardroom.query_beads(
    role='cso',
    type='insight',
    filters={'category': 'CALIBRATION'}
)
```

---

## STATE MACHINE

```
                    ┌──────────────┐
                    │   OFFLINE    │
                    └──────┬───────┘
                           │ load_state()
                           ▼
                    ┌──────────────┐
         ┌─────────│   WARMING    │
         │         └──────┬───────┘
         │                │ warmup_complete
         │                ▼
  crash  │         ┌──────────────┐
    or   │  ┌──────│    READY     │◄────┐
  halt   │  │      └──────┬───────┘     │
         │  │             │ new_bar     │ bar_processed
         │  │             ▼             │
         │  │      ┌──────────────┐     │
         │  │      │  EVALUATING  │─────┘
         │  │      └──────┬───────┘
         │  │             │ decision_made
         │  │             ▼
         │  │      ┌──────────────┐
         │  └─────►│ EMIT_DECISION│
         │         └──────┬───────┘
         │                │ bead_persisted
         │                ▼
         │         ┌──────────────┐
         └────────►│   HALTED     │
                   └──────────────┘
```

---

## PERSISTENCE SCHEDULE

| Event | What Persists | When |
|-------|---------------|------|
| Decision made | Decision bead | Immediately |
| Outcome resolved | Outcome update | On fill/stop |
| Daily close | Reference levels | 17:00 NY |
| Weekly close | Weekly levels | Friday 17:00 NY |
| Shutdown | Session metrics | On graceful stop |
| Crash | Last committed bead | Recovery point |

---

## CONFIGURATION

```yaml
# Dynasty Config
dynasty:
  # Persistence
  decision_retention_days: 365
  insight_retention_days: 90
  reference_snapshot_interval: 1h
  
  # Recovery
  max_recovery_beads: 1000
  state_hash_verification: TRUE
  
  # Calibration
  recalibrate_after_decisions: 50
  confidence_smoothing_window: 30
  
  # Cleanup
  archive_after_days: 90
  prune_losing_streaks: FALSE  # Keep all for analysis
```

---

## INVARIANTS

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| INV-DYNASTY-1 | Every decision emits a bead | Unit test |
| INV-DYNASTY-2 | Bead state_hash matches compute_state_hash() | Validation |
| INV-DYNASTY-3 | Outcome resolved within 24h or marked EXPIRED | Cron job |
| INV-DYNASTY-4 | Reference state persisted daily | Scheduler |
| INV-DYNASTY-5 | No decision bead mutation after emit | Immutable beads |

---

*Generated: Sprint 26 Track C*
