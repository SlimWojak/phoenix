# RB-008: Pacing Violation

**Severity:** WARNING  
**Alert Source:** IBKR connector, Order submission  
**Time to Resolve Target:** < 5 minutes (usually self-resolving)

---

## Symptoms

- Order submission delayed or rejected
- Warning in logs: "Pacing violation" or similar
- IBKR returning error codes 162, 201
- Order rate temporarily throttled

---

## Background

IBKR enforces pacing rules to prevent API abuse:

| Resource | Limit |
|----------|-------|
| Orders per second | ~50 |
| Market data subscriptions | Varies by plan |
| Historical data requests | 60/10 min |
| Account queries | ~1/second |

---

## Immediate Actions

1. **WAIT 10 SECONDS**
   - Pacing violations usually auto-clear

2. **CHECK ORDER STATUS**
   ```bash
   ./phoenix orders list --state=PENDING
   ```

3. **CHECK LOGS**
   ```bash
   tail -50 logs/phoenix.log | grep -i "pacing\|limit\|throttle"
   ```

---

## Investigation Steps

### Step 1: Identify Violation Type

| Error Code | Meaning |
|------------|---------|
| 162 | Historical data pacing |
| 201 | Order rate pacing |
| 1100 | Max messages per second |
| 2103 | Connection issue (may be pacing) |

### Step 2: Check Recent Activity

```bash
# Check order submission rate
./phoenix orders list --since="1 minute ago" | wc -l

# Check API call rate
./phoenix metrics api-calls --last=60s
```

### Step 3: Identify Cause

| Cause | Solution |
|-------|----------|
| Batch order submission | Spread orders over time |
| Rapid retry loop | Add backoff |
| Historical data burst | Implement rate limiting |
| Multiple clients | Use unique client IDs |

---

## Resolution

### Most Cases: Wait

Pacing violations typically clear in:
- 10 seconds for order pacing
- 60 seconds for data pacing
- 10 minutes for historical data

### If Persistent

1. **Reduce Order Rate**
   ```python
   # In config
   ORDER_RATE_LIMIT_SEC = 0.5  # Max 2 orders/sec
   ```

2. **Add Request Spacing**
   - Ensure minimum 100ms between API calls
   - Use exponential backoff on failures

3. **Check for Loops**
   - Ensure no infinite retry without backoff

---

## Post-Incident

1. **Review API Usage Patterns**
   - Any burst activity?
   - Unnecessary repeated calls?

2. **Tune Rate Limiting**
   - Adjust `ORDER_RATE_LIMIT_SEC`
   - Add jitter to prevent synchronization

3. **Document Pattern**
   - What triggered the pacing?
   - How to prevent?

---

## Prevention

### Implement Rate Limiting

```python
# Example rate limiter
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, calls_per_second: float = 2.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = datetime.min
    
    def wait(self):
        now = datetime.now()
        elapsed = (now - self.last_call).total_seconds()
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = datetime.now()
```

### Best Practices

1. **Batch Carefully**
   - Don't submit all orders at once
   - Space orders 100-500ms apart

2. **Cache Aggressively**
   - Don't re-fetch static data
   - Cache account info for 30s

3. **Monitor API Metrics**
   - Track calls per minute
   - Alert before hitting limits

---

**Last Updated:** S33 (2026-01-27)  
**Owner:** Phoenix Ops
