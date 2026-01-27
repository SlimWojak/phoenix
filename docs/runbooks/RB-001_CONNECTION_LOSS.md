# RB-001: IBKR Connection Loss

**Severity:** CRITICAL  
**Alert Source:** Heartbeat daemon, IBKR connector  
**Time to Resolve Target:** < 5 minutes

---

## Symptoms

- Alert: "IBKR connection rotting — run RB-001"
- Heartbeat shows `ibkr_connected: false`
- IBKR_SESSION bead with event=DISCONNECT
- Orders failing with "Not connected to broker"

---

## Immediate Actions

1. **CHECK IB GATEWAY STATUS**
   ```bash
   # Check if IB Gateway process is running
   ps aux | grep -i "ibgateway\|ib gateway"
   ```

2. **CHECK NETWORK**
   ```bash
   # Verify localhost connectivity
   nc -zv 127.0.0.1 4002  # Paper port
   nc -zv 127.0.0.1 4001  # Live port
   ```

3. **CHECK PHOENIX LOGS**
   ```bash
   tail -100 logs/phoenix.log | grep -i "ibkr\|connect"
   ```

---

## Investigation Steps

### Step 1: Identify Cause

| Symptom | Likely Cause |
|---------|--------------|
| Gateway process missing | Gateway crash or auto-update |
| Process running, port closed | Gateway not logged in |
| Port open, Phoenix not connected | Phoenix reconnect exhausted |
| All healthy, still disconnected | Stale connection state |

### Step 2: Check Reconnect Status

```python
# Via Phoenix CLI or debug console
from brokers.ibkr import IBKRConnector
connector.get_reconnect_state()
# Look for: state=ESCALATED, attempts=3
```

### Step 3: Check IBKR_SESSION Beads

```sql
-- Via Athena or bead query
SELECT * FROM beads 
WHERE bead_type = 'IBKR_SESSION' 
ORDER BY timestamp_utc DESC 
LIMIT 10;
```

---

## Resolution

### Option A: Gateway Restart Required

1. **Restart IB Gateway**
   - Open IB Gateway application
   - Log in with appropriate credentials
   - Wait for "Connected" status

2. **Restart Phoenix IBKR Connector**
   ```bash
   # Restart Phoenix daemon (or specific component)
   ./phoenix restart --component=ibkr
   ```

3. **Verify Connection**
   ```bash
   ./phoenix status --component=ibkr
   # Should show: mode=PAPER, connected=true
   ```

### Option B: Phoenix Reconnect Exhausted

1. **Reset Reconnect State**
   ```bash
   # Manual reconnect trigger
   ./phoenix ibkr reconnect --force
   ```

2. **Monitor IBKR_SESSION Beads**
   - Expect: RECONNECT bead with event=CONNECT

### Option C: Persistent Failure

1. **Check IB Status Page**: https://www.interactivebrokers.com/en/software/systemStatus.php
2. **Check .env Configuration**
   ```bash
   grep IBKR .env
   # Verify: IBKR_PORT=4002 (paper), IBKR_MODE=paper
   ```
3. **Escalate to human** if issue persists > 15 minutes

---

## Post-Incident

1. **Run Reconciliation**
   ```bash
   ./phoenix reconcile --immediate
   ```

2. **Check for Drift**
   - Any positions opened/closed during disconnect?
   - RECONCILIATION_DRIFT beads present?

3. **Document in Incident Log**
   - Duration of disconnect
   - Root cause
   - Data loss (if any)

---

## Prevention

- Pin IB Gateway version (disable auto-update)
- Monitor IBKR_SESSION beads for connection gaps
- Run disconnect drill monthly (CV_S33_1_IBKR_DISCONNECT)

---

**Last Updated:** S33 (2026-01-27)  
**Owner:** Phoenix Ops
