# CSO Health Prompt — System Status Access

## Purpose

When Phoenix returns DEGRADED or operator asks about system status, CSO can read this file to understand what's happening without switching context to terminal.

## Health File Location

```
/Users/echopeso/phoenix/state/health.yaml
```

## When to Check

- Phoenix returns `DEGRADED` or `CRITICAL` status
- No response after ~30 seconds
- Operator asks "is Phoenix working?" or similar
- Before suggesting market scans or live trading

## How to Use

1. **Read the file** using standard file read
2. **Report `operator_summary`** naturally in conversation
3. **If components show issues**, mention calmly
4. **Don't diagnose or fix** — just inform and continue thinking

## File Schema

```yaml
version: "1.0"
timestamp: 2026-01-30T09:15:00Z

overall: HEALTHY | DEGRADED | CRITICAL | HALTED

components:
  river:
    status: HEALTHY | STALE | ERROR
    last_update: "2m ago" | "15m ago" | "unknown"
    detail: "472 cols, fresh" | "Data stale >15min"
    
  ibkr:
    status: CONNECTED | DISCONNECTED | UNKNOWN
    mode: PAPER | LIVE | UNKNOWN
    detail: "Paper account connected" | "Connection lost"
    
  halt:
    status: READY | TRIGGERED | ERROR
    latency: "0.003ms" | "unknown"
    detail: "Halt mechanism ready"
    
  watcher:
    status: RUNNING | STOPPED | UNKNOWN
    detail: "File seam operational"
    
  cso:
    status: HEALTHY | ERROR
    detail: "Knowledge files loaded"
    
  health_fsm:
    status: HEALTHY | DEGRADED | CRITICAL
    detail: "0 components tracked"

message: "All components operational" | "DEGRADED: river"

operator_summary: |
  Short human-readable status for CSO to report.
  This is the KEY field — read and report this naturally.
```

## Example Responses

### When Everything is Working

```
Health file shows: "All systems operational. Ready for trading."

Response: "Everything looks good. What would you like to explore?"
```

### When River Data is Stale

```
Health file shows:
  river: STALE (15m ago)
  operator_summary: "River data is stale (15min). Market scans won't work until refresh."

Response: "Looks like River data went stale about 15 minutes ago. 
IBKR is still connected. Scans won't work until data refreshes, 
but we can keep thinking through ideas."
```

### When IBKR is Disconnected

```
Health file shows:
  ibkr: DISCONNECTED
  operator_summary: "IBKR connection unavailable. Live trading blocked."

Response: "IBKR connection dropped. We can still review setups and 
discuss strategy, but live trading is blocked until it reconnects."
```

### When System is HALTED

```
Health file shows:
  overall: HALTED
  halt: TRIGGERED
  operator_summary: "System is HALTED. All trading suspended."

Response: "Phoenix is currently halted — all trading is suspended. 
This was likely triggered by you or an automated safety. 
Check terminal if you want to investigate or resume."
```

## Key Principles

1. **Report, don't diagnose** — CSO informs, doesn't troubleshoot
2. **Natural language** — Use operator_summary as a guide, adapt to conversation
3. **Stay calm** — DEGRADED is normal sometimes; CRITICAL needs attention
4. **Continue working** — Most issues don't block thinking and planning
5. **Don't over-report** — Only mention health when relevant

## File Update Frequency

- **On state change**: Whenever a component status changes
- **Periodic**: Every 60 seconds (configurable)
- **On startup**: Initial state captured

## Integration

To trigger a health file update programmatically:

```python
from state.health_writer import write_health_file

# One-shot write
write_health_file()

# Force write even if no change
write_health_file(force=True)
```

---

*This file is for CSO context. The health.yaml file is the actual system state.*
