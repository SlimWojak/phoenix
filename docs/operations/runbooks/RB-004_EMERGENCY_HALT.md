# RB-004: Emergency Halt

**Severity:** CRITICAL  
**Alert Source:** Manual trigger, Signalman auto-halt, System anomaly  
**Time to Resolve Target:** Immediate (< 50ms halt)

---

## Symptoms

- Alert: "Emergency halt triggered"
- KILL_FLAG bead emitted
- All new entries blocked
- Existing positions preserved (exit-only mode)

---

## Immediate Actions

1. **VERIFY HALT IS ACTIVE**
   ```bash
   ./phoenix kill-flag status
   # Should show: active=true
   ```

2. **CHECK HALT REASON**
   ```bash
   ./phoenix kill-flag reason
   ```

3. **DO NOT PANIC** — halt is protective, not destructive

---

## Common Halt Triggers

| Trigger | Description |
|---------|-------------|
| SIGNALMAN | Auto-halt from decay detection |
| MANUAL | Human-triggered halt |
| SYSTEM | System anomaly detected |
| AUTO_HALT | >3 CRITICAL alerts in 300s |

---

## Resolution

### CRITICAL: ONE-WAY-KILL

**INVARIANT: INV-SIGNALMAN-DECAY-1**

Kill flags are ONE-WAY. Once triggered, require explicit human lift.

### Step 1: Understand Why Halt Was Triggered

```bash
# Check recent KILL_FLAG beads
./phoenix beads list --type=KILL_FLAG --since="1 hour ago"

# Check Signalman decay metrics
./phoenix signalman status
```

### Step 2: Assess Current State

1. **Check Open Positions**
   ```bash
   ./phoenix positions list --state=OPEN
   ```

2. **Check Pending Orders**
   ```bash
   ./phoenix orders list --state=PENDING
   ```

3. **Check IBKR Connection**
   ```bash
   ./phoenix ibkr status
   ```

### Step 3: Resolve Root Cause

Before lifting halt, must address:

- **Signalman decay?** — Wait for metrics to stabilize
- **Connection loss?** — See RB-001
- **Drift detected?** — See RB-002
- **Manual halt?** — Confirm with whoever triggered

### Step 4: Lift Kill Flag

Only when root cause resolved:

```bash
./phoenix kill-flag lift \
  --reason="Root cause resolved: <description>" \
  --operator="<your name>"
```

**Python equivalent (until CLI wired):**
```python
from governance.halt import HaltManager

# Get your halt manager instance
manager.clear_halt()  # Clears signal + restores RUNNING state

# Or for global mesh:
from governance.halt import HaltMesh
mesh = HaltMesh()
mesh.clear_all()  # Clears all modules
```

This emits KILL_FLAG bead with `active=false`.

---

## Post-Incident

1. **Run Full Health Check**
   ```bash
   ./phoenix health full
   ```

2. **Run Reconciliation**
   ```bash
   ./phoenix reconcile --immediate
   ```

3. **Document in Incident Log**
   - Halt trigger
   - Duration of halt
   - Root cause
   - Resolution
   - Capital impact (if any)

---

## Drill Procedure (CV_S33_11)

For monthly drill:

1. **Trigger Manual Halt**
   ```bash
   ./phoenix kill-flag set --reason="Drill - RB-004"
   ```
   
   **Python equivalent:**
   ```python
   from governance.halt import HaltManager
   manager = HaltManager(module_id="drill_test")
   result = manager.request_halt()
   print(f"Halt latency: {result.latency_ms:.3f}ms")
   ```

2. **Verify Behavior**
   - New entries blocked?
   - Existing positions preserved?
   - Alerts firing?

3. **Follow Full Resolution**
   - Time the procedure
   - Document friction points

4. **Lift Halt**
   ```bash
   ./phoenix kill-flag lift --reason="Drill complete"
   ```
   
   **Or run full automated drill:**
   ```bash
   python drills/rb004_halt_drill.py
   ```

---

## Prevention

- Monitor Signalman decay metrics daily
- Keep reconciliation running
- Test halt procedures monthly

---

**Last Updated:** S33 (2026-01-27)  
**Owner:** Phoenix Ops
