# RB-007: IB Gateway Auto-Update

**Severity:** WARNING → CRITICAL  
**Alert Source:** IBKR connector, Heartbeat  
**Time to Resolve Target:** < 10 minutes

---

## Symptoms

- IBKR connection lost unexpectedly
- IBKR_SESSION bead with event=DISCONNECT
- IB Gateway process restarted
- Gateway version changed in subsequent CONNECT bead

---

## Background

IB Gateway can auto-update without warning, causing:
- Process restart (connection loss)
- Configuration reset
- API version changes
- Session invalidation

---

## Immediate Actions

1. **CHECK GATEWAY VERSION**
   ```bash
   # Compare pre/post disconnect beads
   ./phoenix beads list --type=IBKR_SESSION --limit=5
   # Look for gateway_version field
   ```

2. **CHECK GATEWAY PROCESS**
   ```bash
   ps aux | grep -i "ibgateway"
   ```

3. **VERIFY RECONNECTION**
   ```bash
   ./phoenix ibkr status
   ```

---

## Investigation Steps

### Step 1: Confirm Auto-Update

Signs of auto-update:
- Gateway process PID changed
- Gateway version number changed
- Unexpected restart around market close

### Step 2: Check Gateway Logs

IB Gateway logs location:
- macOS: `~/Jts/<version>/`
- Linux: `~/Jts/<version>/`

```bash
tail -50 ~/Jts/*/logs/ibgateway*.log
```

### Step 3: Verify Configuration

After update, verify:
- API settings preserved
- Paper mode still selected
- Correct port listening

---

## Resolution

### Step 1: Reconnect Phoenix

If Phoenix didn't auto-reconnect:

```bash
./phoenix ibkr reconnect --force
```

### Step 2: Validate Account

Ensure still connected to correct account:

```bash
./phoenix ibkr account
# Should show: DU* for paper, U* for live
```

### Step 3: Run Reconciliation

Check for any missed fills during disconnect:

```bash
./phoenix reconcile --immediate
```

---

## Prevention

### Pin Gateway Version (Recommended)

1. **Disable Auto-Update in Gateway**
   - Settings → Configuration → API → Settings
   - Uncheck "Auto Update"

2. **Manual Update Schedule**
   - Update during non-trading hours
   - Test in paper mode first

3. **Document Version**
   ```bash
   # Record current version
   echo "IB Gateway: $(./phoenix ibkr version)" >> logs/versions.log
   ```

### Monitor for Updates

- Check IBKR release notes monthly
- Test new versions in paper before live

---

## Post-Incident

1. **Document Version Change**
   - Old version → New version
   - Any behavior changes noticed

2. **Update Configuration if Needed**
   - Some updates require config changes

3. **Test Critical Paths**
   - Submit test paper order
   - Verify fill received

---

**Last Updated:** S33 (2026-01-27)  
**Owner:** Phoenix Ops
