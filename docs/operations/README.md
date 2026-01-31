# Operations — How to Run Phoenix

Operational documentation for running Phoenix in production.

## Runbooks (runbooks/)

Emergency procedures. Format: `RB-{number}_{TITLE}.md`

| Runbook | Trigger |
|---------|---------|
| `RB-001_CONNECTION_LOSS.md` | IBKR connection drop |
| `RB-002_RECONCILIATION_DRIFT.md` | Position mismatch |
| `RB-003_STALLED_POSITION.md` | Position stuck |
| `RB-004_EMERGENCY_HALT.md` | Kill switch |
| `RB-005_KILL_FLAG_ACTIVE.md` | Flag triggered |
| `RB-006_TELEGRAM_DOWN.md` | Bot unreachable |
| `RB-007_GATEWAY_AUTO_UPDATE.md` | TWS update |
| `RB-008_PACING_VIOLATION.md` | API rate limit |

## Operator Guides (operator/)

Human guidance for operators (G, Olya).

| File | Purpose |
|------|---------|
| `START_HERE.md` | New session orientation |
| `OPERATOR_EXPECTATIONS.md` | What Phoenix expects from you |
| `WHEN_TO_IGNORE_PHOENIX.md` | Override guidance |
