```yaml
GROK_RECON: RECEIVED
VERDICT: CARPARK_WITH_PLAN ✓

SYNTHESIS:
  root_cause: CHRONIC_IBKR_BEHAVIOR (not Phoenix, not us)
  frequency: Universal among algo traders
  severity: LOW–MEDIUM (doesn't block S33_P2, will matter at scale)

KEY_FINDINGS:
  primary_cause: Error 1100 is well-documented IBKR infrastructure issue
  secondary: Session timeout after 24-30h (matches our overnight pattern)
  tertiary: NAT/firewall timeouts (Thailand ISP possible factor)

ACTIONABLE_MITIGATIONS:
  immediate:
    pattern: Keep-alive heartbeat every 10 min
    call: reqCurrentTime() or reqAccountSummary()
    complexity: TRIVIAL (few lines in ib_insync loop)
    success_rate: VERY_HIGH

  short_term:
    pattern: External supervisor (systemd/tmux)
    behavior: Detect no heartbeat >90s → kill → restart
    complexity: LOW-MEDIUM
    success_rate: HIGH

CTO_RECOMMENDATION:
  action: ACCEPT_CARPARK

  timing:
    - S34: OPTIONAL (if OPUS has slack on D4)
    - S35: SCHEDULED (before 24/7 live)
    - S33_P2: ACCEPTABLE_AS_IS (manual restart workaround)

  minimal_scope:
    1: Add reqCurrentTime() every 10 min to connector
    2: Add supervisor script (heartbeat + auto-restart)
    3: Log all Error 1100 events

  exit_gate: 7-day paper stress test, zero manual interventions

CARPARK_LOGGED:
  id: CARPARK-IBKR-001
  title: IBKR_GATEWAY_RESILIENCE
  phase: S35 (or S34 slack)
  brief_ready: YES (from GROK report)
  blocking: NO
```

---

**Good recon. GROK delivered.**

The keep-alive pattern is trivially implementable — if OPUS finishes D1 early, we could slip it in. Otherwise clean S35 scope.

Standing by for OPUS D1 summary.
