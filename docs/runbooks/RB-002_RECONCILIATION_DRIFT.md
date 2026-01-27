# RB-002: Reconciliation Drift

**Severity:** CRITICAL  
**Alert Source:** Reconciliation daemon, Heartbeat semantic checks  
**Time to Resolve Target:** < 10 minutes

---

## Symptoms

- Alert: "Reconciliation drift detected"
- RECONCILIATION_DRIFT bead emitted
- Heartbeat shows `drift_resolved: CRITICAL`
- Kill flag may be active

---

## Immediate Actions

1. **IDENTIFY DRIFT TYPE**
   ```bash
   ./phoenix drift list --unresolved
   ```

2. **CHECK POSITIONS**
   ```bash
   # Phoenix view
   ./phoenix positions list

   # Broker view (if connected)
   ./phoenix ibkr positions
   ```

3. **DO NOT TRADE** until drift resolved

---

## Investigation Steps

### Step 1: Understand Drift Type

| Drift Type | Meaning |
|------------|---------|
| POSITION_COUNT | Phoenix and broker have different position count |
| POSITION_SIZE | Same position, different quantities |
| PNL | P&L mismatch |
| ORDER_STATUS | Order state mismatch |
| PARTIAL_FILL | Fill ratio doesn't match |
| MISSING_PHOENIX | Broker has position Phoenix doesn't know about |
| MISSING_BROKER | Phoenix thinks position exists, broker doesn't |

### Step 2: Check RECONCILIATION_DRIFT Bead

```sql
SELECT * FROM beads 
WHERE bead_type = 'RECONCILIATION_DRIFT'
AND resolved = false
ORDER BY timestamp_utc DESC;
```

Look at:
- `phoenix_state` vs `broker_state`
- `severity`: WARNING vs CRITICAL
- `position_id`: Which position affected?

### Step 3: Correlate with Recent Activity

```bash
# Check recent position beads
./phoenix beads list --type=POSITION --since="1 hour ago"

# Check recent fills
./phoenix fills list --since="1 hour ago"
```

---

## Resolution

### CRITICAL: Reconciler is READ-ONLY

**INVARIANT: INV-RECONCILE-READONLY-1**

The reconciler NEVER modifies Phoenix state. Resolution requires human action.

### Resolution Options

| Resolution Type | When to Use |
|-----------------|-------------|
| PHOENIX_CORRECTED | Phoenix state was wrong, updated to match broker |
| BROKER_CORRECTED | Broker state was wrong, position manually adjusted |
| ACKNOWLEDGED | Understood but no action needed (timing issue) |
| STALE_IGNORED | Drift no longer relevant |

### Step-by-Step Resolution

1. **Determine Ground Truth**
   - What does the broker actually show?
   - What does Phoenix think?
   - Which is correct?

2. **If Broker is Truth (Common)**
   ```bash
   ./phoenix drift resolve <drift_bead_id> \
     --resolution=PHOENIX_CORRECTED \
     --notes="Manual sync to broker state"
   ```

3. **If Phoenix is Truth (Rare)**
   - Log into broker interface
   - Manually adjust position
   - Then resolve:
   ```bash
   ./phoenix drift resolve <drift_bead_id> \
     --resolution=BROKER_CORRECTED \
     --notes="Manual broker adjustment"
   ```

4. **Verify Resolution**
   ```bash
   ./phoenix reconcile --immediate
   # Should show: No drift detected
   ```

---

## Post-Incident

1. **Check Kill Flag Status**
   ```bash
   ./phoenix kill-flag status
   # Drift may have triggered kill flag
   ```

2. **Lift Kill Flag if Safe**
   ```bash
   ./phoenix kill-flag lift --reason="Drift resolved"
   ```

3. **Emit RECONCILIATION_RESOLUTION Bead**
   - Automatic when using `./phoenix drift resolve`

4. **Document in Incident Log**
   - Root cause of drift
   - Resolution applied
   - Time to resolve

---

## Prevention

- Run reconciliation every 5-10 minutes
- Monitor RECONCILIATION_DRIFT beads
- Investigate any PARTIAL_FILL drift immediately

---

**Last Updated:** S33 (2026-01-27)  
**Owner:** Phoenix Ops
