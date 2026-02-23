# RB-003: Stalled Position

**Severity:** WARNING (escalates to CRITICAL after 10min)  
**Alert Source:** Heartbeat semantic checks, Position tracker  
**Time to Resolve Target:** < 15 minutes

---

## Symptoms

- Alert: "Position stalled > 5min" or "Position stalled > 10min"
- POSITION bead with state=STALLED
- Heartbeat shows `stalled_positions: WARNING/CRITICAL`
- Order submitted but no broker acknowledgment

---

## Immediate Actions

1. **IDENTIFY STALLED POSITION**
   ```bash
   ./phoenix positions list --state=STALLED
   ```

2. **CHECK IBKR CONNECTION**
   ```bash
   ./phoenix ibkr status
   # If disconnected: See RB-001
   ```

3. **CHECK ORDER STATUS IN BROKER**
   - Log into IBKR TWS/Portal
   - Find the order by ID
   - Note actual status

---

## Investigation Steps

### Step 1: Understand STALLED State

**INVARIANT: INV-POSITION-SUBMITTED-TTL-1**

SUBMITTED positions timeout to STALLED after 60s if no broker acknowledgment.

| State Flow | Meaning |
|------------|---------|
| SUBMITTED → STALLED | 60s timeout, no broker response |
| STALLED → FILLED | Late broker response (good!) |
| STALLED → CANCELLED | Human intervention |

### Step 2: Check Position History

```bash
./phoenix position history <position_id>
```

Look for:
- When did it enter SUBMITTED?
- How long has it been STALLED?
- Any error messages?

### Step 3: Check Broker-Side Status

In IBKR TWS/Portal, look for:
- Order ID in "Orders" tab
- Status: Submitted? Filled? Rejected?
- Any error messages?

---

## Resolution

### CRITICAL: No Auto-Retry

**WATCHPOINT: WP_C1**

STALLED positions do NOT auto-retry. Human decides next action.

### Option A: Order Actually Filled

If broker shows order was filled:

1. **Wait for Late Response**
   - Phoenix may receive delayed fill notification
   - Position will transition: STALLED → FILLED

2. **Manual Sync if Needed**
   ```bash
   ./phoenix position sync <position_id> --broker-state=FILLED
   ```

### Option B: Order Rejected/Failed

If broker shows order was rejected:

1. **Cancel Position**
   ```bash
   ./phoenix position cancel <position_id> --reason="Broker rejection"
   ```

2. **Check Rejection Reason**
   - Insufficient margin?
   - Invalid symbol?
   - Market closed?

### Option C: Order Still Pending

If broker shows order still pending:

1. **Cancel in Broker**
   - Cancel the order in IBKR TWS

2. **Cancel in Phoenix**
   ```bash
   ./phoenix position cancel <position_id> --reason="Manual cancel"
   ```

3. **Consider Re-submitting**
   - New T2 approval required
   - Fresh state anchor needed

---

## Post-Incident

1. **Run Reconciliation**
   ```bash
   ./phoenix reconcile --immediate
   ```

2. **Check for Drift**
   - STALLED → CANCELLED but broker filled = DRIFT!

3. **Document in Incident Log**
   - Root cause (network? broker issue? Phoenix bug?)
   - Resolution time
   - Any capital impact

---

## Prevention

- Monitor SUBMITTED timeout alerts
- Keep IBKR connection healthy
- Run stalled position drill monthly

---

**Last Updated:** S33 (2026-01-27)  
**Owner:** Phoenix Ops
