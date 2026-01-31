# RB-005: Kill Flag Active

**Severity:** WARNING → CRITICAL  
**Alert Source:** KillManager, Signalman  
**Time to Resolve Target:** Depends on root cause

---

## Symptoms

- Alert: "Kill flag active for strategy X"
- New entries blocked for affected strategy
- KILL_FLAG bead with `active=true`
- Promotion blocked (INV-PROMOTION-SAFE-1)

---

## Immediate Actions

1. **IDENTIFY AFFECTED STRATEGY**
   ```bash
   ./phoenix kill-flag list --active
   ```

2. **CHECK KILL REASON**
   ```bash
   ./phoenix kill-flag details <strategy_id>
   ```

3. **ASSESS IMPACT**
   - Is this strategy currently trading?
   - Any open positions?

---

## Kill Flag vs Emergency Halt

| Kill Flag | Emergency Halt |
|-----------|----------------|
| Per-strategy | System-wide |
| Blocks new entries for strategy | Blocks ALL new entries |
| Decay-triggered | Anomaly-triggered |
| Can coexist with live trading | Full stop |

---

## Investigation Steps

### Step 1: Understand Trigger Source

```bash
./phoenix beads list --type=KILL_FLAG --strategy=<strategy_id>
```

| Trigger | Cause |
|---------|-------|
| SIGNALMAN | Multi-signal decay detected |
| MANUAL | Human judgment |
| SYSTEM | Automated rule violation |

### Step 2: Check Decay Metrics (if Signalman)

```bash
./phoenix signalman metrics <strategy_id>
```

Look for:
- `sharpe_drift`: Significant Sharpe decline?
- `win_rate_drift`: Win rate degradation?
- `ks_p_value`: Distribution shift detected?

### Step 3: Review Recent Performance

```bash
./phoenix beads list --type=PERFORMANCE --strategy=<strategy_id> --limit=10
```

Compare recent vs historical metrics.

---

## Resolution

### When to Lift Kill Flag

| Condition | Action |
|-----------|--------|
| Decay was temporary (news event) | Wait for metrics to recover |
| Decay was permanent | Consider strategy retirement |
| False positive | Adjust Signalman thresholds |
| Manual kill (investigation complete) | Lift if safe |

### Step-by-Step Lift

1. **Confirm Root Cause Resolved**
   ```bash
   ./phoenix signalman metrics <strategy_id>
   # Should show: decay_active=false
   ```

2. **Lift Kill Flag**
   ```bash
   ./phoenix kill-flag lift \
     --strategy=<strategy_id> \
     --reason="Metrics recovered / Investigation complete" \
     --operator="<your name>"
   ```

3. **Verify Flag Lifted**
   ```bash
   ./phoenix kill-flag status <strategy_id>
   # Should show: active=false
   ```

---

## Post-Incident

1. **Document Decision**
   - Why was flag lifted?
   - What changed?

2. **Monitor Closely**
   - Watch next 24h of performance
   - Re-trigger if decay resumes

3. **Update Signalman if False Positive**
   - Adjust thresholds
   - Document pattern

---

## Prevention

- Monitor Signalman decay alerts daily
- Review strategy performance weekly
- Consider retiring chronically decaying strategies

---

**Last Updated:** S33 (2026-01-27)  
**Owner:** Phoenix Ops
