# WHEN_TO_IGNORE_PHOENIX.md
# System Limitations and Override Scenarios

---

## Phoenix Is Not Omniscient

Phoenix encodes methodology into gates. Gates are binary. Markets are not.

**Phoenix cannot see:**
- News you just read
- Context from your broker chat
- "Feel" of price action
- What happened 5 seconds ago (data latency)
- Your intuition built over years

---

## Override Scenarios

### 1. Your Eyes Beat The Gates

| Situation | Phoenix Says | You See | Action |
|-----------|--------------|---------|--------|
| FVG_FORMED: PASS | Valid FVG | Weak, no displacement | Trust your read |
| HTF_BIAS: PASS | Bullish | Momentum dying | Wait or skip |
| KILL_ZONE_ACTIVE: FAIL | Outside KZ | Perfect setup forming | Take it anyway |

**Gates are filters, not commanders.**

### 2. Speed Matters

Phoenix updates on cycles. Markets move in milliseconds.

- Price swept level while you were reading scan? **Your eyes win.**
- FVG filled between scan and now? **Your eyes win.**
- News dropped 30 seconds ago? **Phoenix doesn't know yet.**

### 3. Context Phoenix Can't Encode

- "This pair has been weird all week"
- "I just saw a massive order on the tape"
- "The correlated pair did something strange"
- "My gut says wait"

**These are valid. Phoenix can't weigh them. You can.**

### 4. Data Is Stale

If health shows `STALE` or timestamps are old:

- Don't trust scan results
- Don't assume gates reflect NOW
- Verify on your chart before acting

---

## When Phoenix Is Wrong

Phoenix can be wrong when:

| Scenario | Why | What To Do |
|----------|-----|------------|
| Methodology edge case | Rules don't cover this pattern | Use judgment |
| Data quality issue | Bad tick, gap, feed error | Verify on chart |
| Timing mismatch | Gate passed 5 min ago, not now | Re-verify |
| Regime shift | Market changed, model hasn't | Recognize and adapt |

**Phoenix is a tool. Tools don't make decisions. You do.**

---

## The Golden Rule

> **If Phoenix says GO but you feel STOP — stop.**
> **If Phoenix says STOP but you see GO — proceed with awareness.**

Phoenix protects you from obvious mistakes.
Phoenix cannot protect you from markets being markets.

---

## What Phoenix Will NEVER Do

| Action | Why Not |
|--------|---------|
| Enter a trade without your approval | T2 requires explicit human gate |
| Tell you what to do | Facts only, never recommendations |
| Override your decision | You are sovereign |
| Hide system problems | Health is always visible |
| Pretend to know what it doesn't | CSO discloses uncertainty |

---

## Healthy Skepticism Checklist

Before acting on Phoenix output:

- [ ] Does this match what I see on chart?
- [ ] Is health HEALTHY?
- [ ] Are timestamps recent?
- [ ] Does my gut agree?
- [ ] Am I thinking clearly, or rushing?

If any answer is "no" — pause.

---

## Summary

| Trust Level | Phoenix State | Your Action |
|-------------|---------------|-------------|
| High | HEALTHY, gates clear, matches chart | Act with confidence |
| Medium | HEALTHY, but something feels off | Verify, then decide |
| Low | DEGRADED, stale, or contradicts eyes | Trust yourself over system |

**Phoenix is your co-pilot, not your commander.**

You hired it. You can overrule it. That's sovereignty.
