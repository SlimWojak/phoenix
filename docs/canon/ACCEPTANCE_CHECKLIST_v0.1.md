# T5: ACCEPTANCE CHECKLIST — a8ra v0.1

```yaml
TRACK: S50.T5.ACCEPTANCE_CHECKLIST
DATE: 2026-02-22
OWNER: CTO (draft) → G (sign-off)
PURPOSE: "Does it do what we said? Can G operate it solo?"
GATE: G signs — "I understand this, I trust this, I can operate this"
```

---

## SECTION A: SPRINT EXIT GATES (S28-S50)

```yaml
# Every sprint that shipped — does its exit gate still hold?

S28_CONSTITUTIONAL_FOUNDATION:
  gate: "Constitutional interface enforced on all organs"
  holds: ✅ (INV-GOV-1 tested, GovernanceInterface in 90 test files)

S29_HALT_SYSTEM:
  gate: "halt_local < 50ms, halt_cascade < 500ms"
  holds: ✅ (INV-HALT-1, INV-HALT-2 — tested in test_halt_latency.py)

S30_POSITION_LIFECYCLE:
  gate: "9-state position FSM with T2 human gate"
  holds: ✅ (INV-POSITION-SM-1, position_lifecycle.yaml schema)

S35_CFP:
  gate: "Conditional facts with provenance, causal ban enforced"
  holds: ✅ (INV-CFP-CAUSAL-BAN — 4 test files in tests/test_cfp/)

S36_CSO_HARNESS:
  gate: "CSO outputs gate status only, never grades"
  holds: ✅ (INV-HARNESS-1 through INV-HARNESS-5 — 5 test files)

S37_MEMORY_DISCIPLINE:
  gate: "CLAIM/FACT/CONFLICT bead separation with provenance"
  holds: ✅ (INV-FACT-ENCAPSULATES-CLAIM — tests/test_athena/)

S38_HUNT:
  gate: "Exhaustive grid compute, no survivor ranking"
  holds: ✅ (INV-HUNT-EXHAUSTIVE — tests/test_hunt/)

S39_VALIDATION:
  gate: "Decomposed outputs, ScalarBanLinter"
  holds: ✅ (INV-SCALAR-BAN — tests/test_validation/)

S40_SLEEP_SAFE:
  gate: "System survives coordinated chaos, self-healing FSM"
  holds: ✅ (INV-CIRCUIT-1, INV-CIRCUIT-2 — tests/test_self_healing/)

S41_GUARD_DOG:
  gate: "ContentClassifier catches heresy at narrator chokepoint"
  holds: ✅ (INV-SLM-BOUNDARY — tests/test_slm_boundary.py)

S42_TRUST_CLOSURE:
  gate: "48 gates mapped, operator boundaries documented"
  holds: ✅ (INV-GATE-GLOSSARY — cso/knowledge/GATE_GLOSSARY.yaml)

S43_FOUNDATION_TIGHTENING:
  gate: "Centralized config, narrator template linting"
  holds: ✅ (tests/test_narrator_templates.py)

S44_LIVE_VALIDATION:
  gate: "IBKR paper end-to-end, 24h soak, zero invariant violations"
  holds: ✅ (FOUNDATION_VALIDATED — INV-NO-CORE-REWRITES-POST-S44 active)

S45_RESEARCH_UX:
  status: BLOCKED (Olya paced) — not required for v0.1
  holds: N/A

S46_CARTRIDGE_LEASE_DESIGN:
  gate: "Design locked, advisor consensus, all questions resolved"
  holds: ✅ → UPGRADED to v1.1 (cabinet model, S50)

S47_LEASE_IMPLEMENTATION:
  gate: "Lease state machine operational, halt override < 50ms"
  holds: ✅ (120 lease tests, 16 chaos vectors — all pass)

S48_HUD_SURFACE:
  gate: "HUD displays real Phoenix state with <500ms latency"
  holds: ✅ (surfaces/hud/ operational)

S49_BOOTSTRAP_AND_DEPLOY:
  gate: "One command + secrets = operational office"
  holds: ✅ (INV-BOOTSTRAP-IDEMPOTENT, INV-SINGLE-COMMAND-SETUP)

S50_SEAL:
  gate: "Cabinet refactor + GPT hardening + invariant freeze + full suite + acceptance"
  holds: 🔄 THIS DOCUMENT
```

---

## SECTION B: SYSTEM METRICS

```yaml
tests:
  passed: 1615
  failed: 0
  xfailed: 22 (documented, strict)
  skipped: 2
  collection_errors: 7 (pre-existing, not S50)
  duration: 374s

chaos:
  vectors: 264
  passed: 264
  failed: 0
  suites: 14 files (S30-S39 + S47 + NEX + v2 + v3)

invariants:
  tier_1_constitutional: 18 (enumerated, enforcement mapped)
  tier_2_subsystem: ~95+ (frozen by commit)
  tier_3_methodology: 21 (CSO authority)
  tier_4_mission_control: 17 (phoenix-swarm/)
  total: 150+

governance:
  bead_types: 17+
  gates_mapped: 48
  sprints_complete: 20 (S28-S44, S46-S50)
  lease_tests: 120
  cabinet_tests: 18

pre_commit_hooks:
  ruff: PASS
  ruff_format: PASS
  constitutional_scalar_ban: PASS
  constitutional_provenance: PASS
  mypy: 174 pre-existing (deferred, not S50)

commit: 06dcff8 (s50 deliverables, not pushed)
branch: s35-cfp-complete
```

---

## SECTION C: OFFICE VERIFICATION

```yaml
PHOENIX_OFFICE:
  identity: ✅ (CLAUDE.md operational)
  heartbeat: ✅ (health_fsm.py)
  checkpoint: ✅ (bead store, state anchor)
  coordination: ✅ (phoenix-swarm/)

DEXTER_OFFICE:
  identity: ✅ (CLAUDE.md operational)
  status: Gate 1 PASS (274 tests, 789 Genesis beads)
  parallel: ✅ (independent of Phoenix v0.1)

ORACLE_OFFICE:
  identity: ✅ (CLAUDE.md operational)
  status: Blocked on Olya availability (S45)
  note: Not required for v0.1 — CSO COE model accepted

MISSION_CONTROL:
  design: v0.2 LOCKED (13/13 decisions, 32 MC invariants)
  ground_tests: 6/6 PASS
  phoenix_swarm: Built (30 files, coordination scaffold)
```

---

## SECTION D: BOOTSTRAP VERIFICATION

```yaml
question: "Fresh Mac → operational in <30min?"

bootstrap_sh: ✅ (INV-BOOTSTRAP-IDEMPOTENT — runs N times without damage)
secrets_keychain: ✅ (INV-NO-SECRETS-IN-FILES — zero secrets in repo)
single_command: ✅ (INV-SINGLE-COMMAND-SETUP)
verify_office: ✅ (T3 Task 3 — all imports clean)

operator_docs:
  OPERATOR_SETUP.md: ✅ (docs/operations/)
  ESCALATION_LADDER.md: ✅ (T4 — G signed)
  REPO_MAP.md: ✅ (root)
```

---

## SECTION E: WHAT SHIPS

```yaml
a8ra_v0.1_INCLUDES:
  - Constitutional governance engine (18 core invariants)
  - Lease/Cartridge system v1.1 (cabinet model, self-contained 5-drawer)
  - 9-state position lifecycle with T2 human gate
  - IBKR integration (paper validated, live ready)
  - 5-drawer CSO gate evaluation (48 gates, boolean only)
  - Halt system (<50ms local, <500ms cascade)
  - Guard dog with cabinet content scanning
  - Heartbeat, health FSM, circuit breaker
  - HUD surface (SwiftUI, <500ms latency)
  - Athena memory (CLAIM/FACT/CONFLICT, append-only)
  - Bootstrap (one command + secrets = operational)
  - Escalation ladder (4-tier, documented)
  - 150+ frozen invariants
  - 1615 passing tests, 264 chaos vectors

a8ra_v0.1_DOES_NOT_INCLUDE:
  - Bead Field analytical substrate (ships separately as Dexter Gate 1)
  - Bridge (Phase 2 — after both v0.1 + Gate 1 stable)
  - Dream Cycle (Phase 3 — DGX Spark, Gate 5+)
  - Multi-cartridge support (v1.2+, earned by operator friction)
  - Olya research UX (S45 — operator paced)
  - Mobile command plane (Phase 1 ntfy operational, Phase 2 Matrix on M3)
```

---

## SECTION F: KNOWN TECH DEBT

```yaml
ACCEPTED_FOR_v0.1:
  mypy: "174 pre-existing errors across 21 files. Polish sprint post-v0.1."
  collection_errors: "7 in test_chaos_bunny.py + test_historical_nukes.py. Pre-existing."
  methodology_template: "conditions.yaml retained alongside methodology_template.yaml (15+ imports)"
  full_invariant_enumeration: "Tier 2 frozen by commit hash, not line-by-line. Post-v0.1 polish."

NOT_ACCEPTED:
  test_failures: 0
  invariant_violations: 0
  S50_regressions: 0
```

---

## SECTION G: SOVEREIGN SIGN-OFF

```yaml
# G completes this section

OPERATOR_CONFIDENCE:
  understand: [ ] "I understand what this system does and does not do"
  trust: [ ] "I trust the test suite proves what it claims"
  operate: [ ] "I can bootstrap, monitor, halt, and recover solo"
  escalate: [ ] "I know who to call (Tier 1-4 ladder)"
  boundaries: [ ] "I know what v0.1 includes and excludes"

SOVEREIGN_DECLARATION:
  statement: "a8ra v0.1 is accepted for operational deployment"
  signed: ________________
  date: 2026-02-22

# Upon signature: CTO proceeds to T6 (SEAL — version tag + push)
```
