# SKILL.md — Phoenix Operating Patterns

**Skill:** Phoenix Constitutional Trading System
**Version:** 2.0
**Updated:** 2026-01-23
**Jurisdiction:** ~/echopeso/phoenix (sibling to ~/echopeso/god_mode)
**Sprint:** S28.D STEEL_PIPES (Complete)

---

## LEVEL 1: METADATA (Always Loaded)

### Identity

```yaml
PROJECT: Phoenix
TYPE: Constitutional Trading System
STATUS: Foundation Complete (Sprint 26)
RELATIONSHIP: 
  sibling: God_Mode (forge/lawgiver)
  pattern: "Forge builds tools, Phoenix protects capital"
```

### Communication Standard

```yaml
FORMAT: DENSE_M2M (Machine-to-Machine)

RULES:
  - YAML/structured output preferred
  - zero prose preamble
  - no "I think..." hedging
  - no restating context back
  - binary verdicts (PASS/FAIL/CONDITIONAL)
  - explicit refs (file:line, contract:clause)

ANTI-PATTERNS:
  - prose paragraphs explaining reasoning
  - "Let me help you with that..."
  - recap loops ("As we discussed...")
  - compliments/acknowledgments
  - rhetorical questions
```

### Core Invariants

```yaml
SOVEREIGNTY:
  INV-SOVEREIGN-1: "Human sovereignty over capital is absolute"
  INV-SOVEREIGN-2: "T2 (capital-affecting) requires human gate"

HALT:
  INV-HALT-1: "halt_local < 50ms (proven: 0.003ms)"
  INV-HALT-2: "halt_cascade < 500ms (proven: 22.59ms)"

GOVERNANCE:
  INV-GOV-1: "all Phoenix organs inherit GovernanceInterface"
  INV-GOV-NO-T1-WRITE-EXEC: "T1 cannot write execution_state"
  INV-GOV-HALT-BEFORE-ACTION: "gate checks halt before capital action"

DATA:
  INV-CONTRACT-1: "deterministic state machine"
  INV-DATA-CANON: "single pipeline truth (River)"
```

### Role Map

```yaml
ROLES:
  G (Sovereign):
    authority: vision, veto, capital decisions
    mode: curator + filter (advisors expand, G distills for CTO)
    
  CTO (Claude):
    authority: synthesis, coordination, coherence
    mode: receives DENSE only, routes to specialists
    
  OWL (Gemini):
    authority: contract law, structural audit
    mode: clause-level review, ripple analysis
    
  GPT (Architect Lint):
    authority: spec tightening, edge cases
    mode: flag tables (L1-Ln), required fixes
    
  BOAR (Grok):
    authority: chaos audit, adversarial stress
    mode: entropy injection, "dumbest failure" finder
    
  OPUS (Cursor):
    authority: primary builder
    mode: executes briefs, dense reports
```

---

## LEVEL 2: INSTRUCTIONS (Loaded When Triggered)

### Brief Template

```yaml
BRIEF: {SPRINT}.{TRACK}.{DAY}
MISSION: {NAME}
OWNER: {ADVISOR}
FORMAT: DENSE

CONTEXT:
  status: {prior work}
  proven: {invariants}
  
PURPOSE:
  build|prove|audit: {objective}
  invariant: "{quoted invariant}"

TASK:
  - {numbered tasks}
  
DELIVERABLES:
  code:
    - {file paths}
  tests:
    - {test files}
  docs:
    - {reports}

EXIT_GATES:
  {gate_name}:
    criterion: {measurable}
    test: {test file}
    proof: {mechanical evidence}

PASS_CONDITION:
  {binary criteria}

FAIL_CONDITION:
  {halt triggers}

REPORT_FORMAT: DENSE

REF:
  - {reference docs}
```

### Report Template

```yaml
{TRACK}: COMPLETE
MISSION: {NAME}
RESULT: PASS|FAIL|CONDITIONAL

{TASK_RESULTS}:
  - {task}: {outcome}
  
METRICS:
  {key measurements}

EXIT_GATES:
  {gate}: {criterion} → {verdict} ✓|✗

INVARIANTS_PROVEN:
  {INV-*}: {evidence}

DELIVERABLES:
  {categorized file lists}

NEXT: {unlocked work}
```

### Advisor Lint Template

```yaml
LINT: {ADVISOR}_AUDIT
SCOPE: {target document/code}
STATUS: {verdict}

FLAGS:
  {id}: 
    status: PASS|FAIL|WARN
    issue: {description}
    fix: {required change}
    blocking: YES|NO

STRUCTURAL_FINDINGS:
  - loc: {location}
    invariant: {related INV-*}
    observation: {finding}

RECOMMENDATION:
  {action items}
```

### Contract Template

```yaml
CONTRACT: {NAME}
VERSION: {semver}
STATUS: DRAFT|CANON
LOCATION: phoenix/CONSTITUTION/{category}/{name}.yaml

INVARIANTS:
  {INV-*}: "{quoted law}"

INTERFACE:
  properties:
    {name}:
      type: {type}
      required: TRUE|FALSE
      semantics: {meaning}
      enforcement: {how tested}

  methods:
    {name}:
      signature: {params} -> {return}
      latency: {constraint if any}
      semantics: {behavior}
      test: {test file}

ENFORCEMENT:
  tests_required:
    - {test files}
    
  contract_validity:
    rule: "A contract is invalid unless an automated test can fail it"
```

### Boardroom Bead Pattern

```yaml
BEAD_SCHEMA:
  purpose: immutable decision artifact
  persistence: boardroom/beads/
  
  structure:
    bead_id: str (uuid)
    bead_type: enum[DECISION, HALT, VIOLATION, SPAWN, KILL]
    timestamp: datetime (UTC)
    source_module: str
    state_hash: str
    payload: dict
    outcome: dict (filled async, <24h)
    
  invariants:
    INV-DYNASTY-1: "every T1/T2 decision → bead"
    INV-DYNASTY-5: "beads immutable once written"
```

### Multi-Advisor Coordination

```yaml
POLLING_PATTERN:
  1. CTO drafts position/contract
  2. fan out: OWL + GPT + BOAR (parallel)
  3. each responds independently (no cross-contamination)
  4. G curates: extracts DENSE signal for CTO
  5. CTO synthesizes convergence
  6. divergence → escalate to G

JOIST_PATTERN (contract hardening):
  1. CTO drafts contract
  2. GPT lints (spec flags L1-Ln)
  3. OWL audits (structural coherence)
  4. BOAR stresses (chaos vectors)
  5. CTO amends (synthesized v0.2+)
  6. OPUS builds (from hardened spec)
  7. BOAR post-audit (what did we miss)

FILTER_PATTERN:
  advisors → expand/explore → G
  G → probe/extract → DENSE summary
  DENSE summary → CTO
  (protects CTO context, preserves advisor depth)
```

---

## LEVEL 3: RESOURCES (Loaded As Needed)

### Directory Structure

```
~/echopeso/phoenix/
├── SKILL.md                    # THIS FILE
├── CLAUDE.md                   # CLI orientation
├── GEMINI.md                   # Owl orientation
├── README.md                   # Project overview
│
├── CONSTITUTION/               # The Law (S28.D populated)
│   ├── CONSTITUTION_MANIFEST.yaml
│   ├── invariants/             # 6 proven invariants
│   │   ├── INV-HALT-1.yaml
│   │   ├── INV-HALT-2.yaml
│   │   ├── INV-CONTRACT-1.yaml
│   │   ├── INV-DATA-CANON.yaml
│   │   ├── INV-GOV-HALT-BEFORE-ACTION.yaml
│   │   └── INV-EXEC-LIFECYCLE-1.yaml
│   ├── roles/                  # 3 role definitions
│   │   ├── sovereign.role.yaml
│   │   ├── cto.role.yaml
│   │   └── cso.role.yaml
│   └── wiring/                 # Signal flow
│       └── halt_propagation.wiring.yaml
│
├── contracts/                  # Data contracts
│   ├── ICT_DATA_CONTRACT.md
│   ├── GOVERNANCE_INTERFACE_CONTRACT.md
│   ├── truth_teller.py
│   └── mirror_markers.py
│
├── governance/                 # GovernanceInterface (S26-S28)
│   ├── interface.py            # ABC for all organs
│   ├── halt.py                 # <50ms halt
│   ├── telemetry.py            # Quality reporting
│   ├── tokens.py               # T2 approval
│   └── errors.py               # Error classification
│
├── monitoring/                 # Observability (S28.B)
│   ├── alerts.py               # Thresholds + debounce + auto-halt
│   └── dashboard.py            # Web health view
│
├── execution/                  # Execution path (S28.C)
│   ├── position.py             # Lifecycle state machine
│   ├── broker_stub.py          # Paper broker
│   ├── replay.py               # Deterministic harness
│   ├── intent.py               # Order intents
│   └── halt_gate.py            # Halt-first pattern
│
├── cso/                        # Chief Strategy Officer
│   ├── knowledge/              # 5-drawer methodology (59 signals)
│   │   ├── foundation.yaml
│   │   ├── context.yaml
│   │   ├── conditions.yaml
│   │   ├── entry.yaml
│   │   ├── management.yaml
│   │   └── index.yaml
│   ├── observer.py             # Passive observer
│   └── beads.py                # Decision artifacts
│
├── enrichment/                 # Data enrichment (L1-L6)
│   └── layers/                 # ICT marker calculation
│
├── dispatcher/                 # Worker coordination
│   ├── dispatcher.py
│   ├── worker_base.py
│   └── tmux_control.py
│
├── docs/                       # Core documents
│   ├── VISION_v4.md
│   ├── PHOENIX_MANIFESTO.md
│   ├── ADVISOR_ORIENTATION.md  # Bootstrap guide
│   └── *_REPORT.md             # Sprint reports
│
└── tests/                      # 60+ tests
    ├── test_halt_*.py
    ├── test_execution_path.py
    ├── test_monitoring.py
    └── chaos/                  # Chaos suite v3
```

### God_Mode Integration Points

```yaml
SHARED_INFRASTRUCTURE:
  boardroom: ~/echopeso/god_mode/boardroom/
    - bead persistence
    - cross-jurisdiction coordination
    
  hive: ~/echopeso/god_mode/hive/
    - HIVE_OPS.md (orchestration patterns)
    - tmux coordination
    
  takopi: ~/echopeso/god_mode/bridge/takopi/
    - Telegram bridge
    - sovereign mobile interface

SUBSUME_NOT_IMPORT:
  rule: "Phoenix has zero runtime dependencies on God_Mode code"
  pattern: copy → refactor → contract → validate
  rationale: pure jurisdiction, no grandfather clause
```

### Key Reference Documents

```yaml
ORIENTATION_PRIORITY:
  P0 (always):
    - SKILL.md (this file)
    - CONSTITUTION_AS_CODE.md
    
  P1 (context):
    - PHOENIX_FOUNDATION_OVERVIEW.md
    - current SPRINT_*.md
    
  P2 (reference):
    - VISION_v4.md
    - PHOENIX_MANIFESTO.md
    - relevant contracts/
```

### Sprint 28 Proven State

```yaml
S28_STATUS: STEEL_PIPES (Complete)

TRACK_A_CHAOS_V3:
  vectors: 4/4 pass (100%)
  regime_nukes: bounds checking implemented
  correlated_lies: detection proven
  petabyte_sim: latency maintained

TRACK_B_MONITORING:
  dashboard: operational
  alerts: threshold + debounce
  auto_halt: >3 CRITICAL → halt
  bead_emission: on CRITICAL

TRACK_C_EXECUTION:
  position_lifecycle: PENDING→OPEN→CLOSED/HALTED
  paper_broker: P&L v0 (simplified)
  replay_harness: deterministic (hash match)
  tests: 23/23 pass

TRACK_D_CONSOLIDATION:
  constitution: 6 invariants + 3 roles + 1 wiring
  docs: stale refs cleaned
  readme: current

METHODOLOGY:
  architecture: 5-drawer model
  signals: 59 (foundation/context/conditions/entry/management)
  location: cso/knowledge/*.yaml
  status: DRAFT v0, pending Olya validation

INVARIANTS_PROVEN:
  INV-HALT-1: 0.003ms
  INV-HALT-2: 22.59ms
  INV-CONTRACT-1: hash match
  INV-DATA-CANON: XOR == 0
  INV-GOV-HALT-BEFORE-ACTION: tests pass
  INV-EXEC-LIFECYCLE-1: enforced

S29_UNLOCKED:
  - CSO active implementation
  - Real methodology signals
  - P&L v1 (fees/slippage)
  - Live broker integration
```

---

## TRIGGERS

```yaml
LOAD_LEVEL_2_WHEN:
  - drafting briefs
  - reviewing advisor output
  - writing contracts
  - creating reports
  - coordinating multi-advisor work

LOAD_LEVEL_3_WHEN:
  - navigating codebase
  - understanding God_Mode integration
  - referencing proven invariants
  - onboarding new session
```

---

**OINK OINK.** 🐗🔥
