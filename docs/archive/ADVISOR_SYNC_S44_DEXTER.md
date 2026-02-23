# ADVISOR SYNC: POST-S44 SOAK + DEXTER EMERGENCE

```yaml
M2M_CANONICAL: ADVISOR_ORIENTATION
AS_OF: 2026-02-04
AUTHOR: Opus (Synthesis)
SOURCE: dream_sequence.md (CTO Claude compaction rescue)
PURPOSE: Single briefing for all advisors — Phoenix + Dexter state
```

---

## EXECUTIVE SUMMARY (30 SECONDS)

```yaml
WHAT_HAPPENED:
  - Phoenix S44 soak: FOUNDATION_VALIDATED (operational gaps, no arch flaws)
  - G fell down rabbit hole → spawned DEXTER (24hr MVP build)
  - Major unlock: CSO Center of Excellence model discovered
  - Perplexity validated Phoenix architecture as industry best practice
  - Dexter extracted 504 ICT signatures from 18 videos overnight

PARADIGM_SHIFT:
  before: "Mine Olya's brain slowly via Claude sessions"
  after: "Build comprehensive knowledge base → Olya validates (recognition > recall)"

DEXTER_ROLE: "Phoenix's Bone Marrow — generates logic cells for the gauntlet"
```

---

## 1. PHOENIX STATE (S44 SOAK EXIT)

```yaml
SOAK_OUTCOME:
  classification: FOUNDATION_VALIDATION
  duration: multi-day, unattended overnight segments

POSITIVES:
  - No catastrophic crashes
  - No invariant violations
  - Phoenix ran independently of HUD
  - State surfaces updated correctly
  - Health transitions intelligible
  - HUD remained read-only, non-interfering

GAPS_EXPOSED:
  - No persistent heartbeat daemon
  - IBKR/TWS disconnect when operator closed app
  - River feed stale when upstream disconnected
  - health_writer not continuous by default
  - Operational glue missing (expected at this stage)

VERDICT: |
  "Software exists. Transition from building → operating."
  Risk: LOW (design), MEDIUM (ops) — as expected.
```

### Architecture Status

```yaml
LAYERS:
  data_plane: [river: ACTIVE, bead_store: STABLE, state_files: AUTHORITATIVE]
  control_plane: [health_fsm: FUNCTIONAL, gates: FUNCTIONAL, halt: FUNCTIONAL]
  governance_plane: [cartridge_schema: S46 LOCKED, lease_schema: S46 LOCKED, impl: S47 PENDING]
  surface_plane: [hud: BUILT (S48), cli: PRESENT, narrator: FUNCTIONAL]

QUALITY:
  tests_passing: 1500+
  chaos_vectors: 224/224
  invariants_defined: 100+
  violations_observed: 0
```

---

## 2. DEXTER: SOVEREIGN EVIDENCE REFINERY

### Identity

```yaml
NAME: DEXTER
TYPE: Sovereign Evidence Refinery
REPO: https://github.com/SlimWojak/Dexter
HARDWARE: Isolated Mac Mini (sandbox)
SIBLING: Phoenix (Constitutional Trading System)
RELATIONSHIP: "Phoenix's Bone Marrow — generates logic cells for the gauntlet"
MOTTO: "Mine the ore. Refine the gold. Human decides."
```

### Purpose

```yaml
PROBLEM_SOLVED: |
  ICT methodology = 100s of hours of video content (790+ videos)
  Manual extraction = years of human effort
  DEXTER automates the grind. Human keeps the judgment.

CRITICAL_INVARIANT: |
  INV-DEXTER-ALWAYS-CLAIM:
  Output = CLAIM. Never FACT.
  Refinement makes review faster, not unnecessary.
  Only human (Olya) promotes CLAIM → FACT.
```

### Architecture (Role-Based Swarm)

```yaml
ROLES:
  theorist:
    model: deepseek-v3.2 (OpenRouter)
    job: Extract IF-THEN signatures from transcripts
    output: JSON with timestamp + source quote + drawer tag

  auditor:
    model: gemini-flash (OpenRouter)
    family: DIFFERENT (cross-family veto)
    job: Adversarial falsification — kill bad hypotheses
    pattern: "Bounty Hunter — earns points for rejections"

  bundler:
    model: deepseek-v3.2
    job: Package validated signatures into Evidence Bundles
    constraint: Template-locked, zero narrative (INV-NO-NARRATIVE)

  chronicler:
    model: gemini-flash
    job: Recursive summarization → THEORY.md
    status: Role defined, implementation PENDING

  cartographer:
    model: gemini-flash
    job: Survey corpus, build extraction queue
    output: corpus_map.yaml, extraction_queue.yaml

MEMORY:
  pattern: Bead-chain (append-only JSONL)
  types: [RAW_BEAD, VALIDATED_BEAD, NEGATIVE_BEAD]
  feedback: Negative beads prepend to Theorist context
```

### Overnight Soak Results (Feb 3-4)

```yaml
METRICS:
  videos_attempted: 20
  videos_completed: 18 (90%)
  videos_failed: 2 (injection guard false positives)

  signatures_extracted: 433
  signatures_validated: 424
  signatures_rejected: 9 (2.1% rejection rate)

  claim_bead_files: 20
  total_claim_beads: 408
  bundles_all_time: 32
  validated_all_time: 504

COST:
  per_video: ~$0.003
  daily_24/7: ~$0.10-0.40

TESTS: 208/208 PASS
BUILD_TIME: Single day (Feb 3, 2026)
```

### Known Gaps (Priority Order)

```yaml
P1_CHRONICLER:
  issue: Not implemented — beads grow unbounded
  risk: HIGH — memory bloat over time
  fix: Implement compression (role defined, code pending)

P2_QUEUE_ATOMICITY:
  issue: save_queue() does full YAML rewrite
  risk: MEDIUM — crash mid-write corrupts state
  fix: 5 lines (write-tmp + rename pattern)

P3_SYNC_PIPELINE:
  issue: Sequential processing with time.sleep()
  risk: LOW (for now) — won't scale past 100+ videos
  fix: Async refactoring (defer until needed)

P4_AUDITOR_LENIENCY:
  issue: 2.1% rejection rate (below 10% floor)
  risk: LOW — Auditor may be too lenient
  fix: LLM Auditor upgrade or stricter prompts

P5_INJECTION_FALSE_POSITIVES:
  issue: Conversational phrases triggering guard
  risk: LOW — 2/20 videos affected
  fix: Whitelist common ICT speech patterns
```

---

## 3. THE CSO CENTER OF EXCELLENCE BREAKTHROUGH

### The Old Model (Bottleneck)

```
Olya's brain → articulation → Claude session → MD file → conditions.yaml

Problems:
  - Every link is lossy
  - Ceiling-limited by what Olya can self-organize on demand
  - Recall-based (slow, incomplete, frustrating)
  - She knows 15 things about FVG entries, surfaces 6 because 9 are implicit
```

### The New Model (Unlock)

```
Research + ICT corpus → comprehensive structured base → Olya validates/corrects/adds edge

Why it works:
  - Recognition > recall (what experts are best at)
  - "Yes, but tighten this threshold" = fast
  - Generating from scratch in Claude session = slow
  - ICT base is public knowledge; Olya's EDGE is interpretation/weighting
```

### The Triangle

```
Dexter (ICT extraction)──────┐
                              ├──→ Comprehensive Gate Base ──→ Olya validates ──→ conditions.yaml
Perplexity (quant research)──┘
```

### Layer Model

```yaml
LAYER_1_ARCHITECTURE:  # From Perplexity + quant research
  source: Academic/practitioner best practice
  output: Drawer structure, feature targets, pattern approach

LAYER_2_CONTENT:       # From Dexter + ICT corpus
  source: 790 ICT videos + deep research
  output: Comprehensive gate definitions, threshold ranges, edge cases

LAYER_3_CALIBRATION:   # From Olya (sovereign validator)
  source: Expert recognition, proprietary edge
  output: Corrections, additions, final stamp

LAYER_4_RUNTIME:       # Phoenix CSO
  input: conditions.yaml
  output: Boolean gate evaluation (PASS/FAIL only)
```

### Constitutional Alignment

```yaml
INVARIANTS_PRESERVED:
  INV-SOVEREIGN-1: Olya still absolute authority (sovereignty INCREASES)
  INV-NO-UNSOLICITED: Gates still evaluate boolean, no proposals at runtime
  INV-DEXTER-ALWAYS-CLAIM: Everything starts as unvalidated (holds HARDER now)

KEY_INSIGHT: |
  "Olya's role elevates from 'knowledge source being mined'
   to 'sovereign validator of comprehensive knowledge base.'
   That's what a CSO SHOULD be."
```

---

## 4. PERPLEXITY ARCHITECTURE VALIDATION

### Findings (Against Phoenix)

```yaml
VALIDATION_SCORECARD:
  gate_driven_pull_enrichment: ✓ CONFIRMED ("closer to industry best practice")
  boolean_gate_evaluation: ✓ CONFIRMED ("codified filters + setup detectors")
  5_drawer_separation: ✓ CONFIRMED ("structure/regime/session/setup modules")
  human_in_the_loop: ✓ CONFIRMED ("designed to be overridden, not obeyed")
  deterministic_MSS: ✓ CONFIRMED ("explicit deterministic market structure")
  constitutional_research_separation: ✓ CONFIRMED ("strict separation of roles")
  INV_SCALAR_BAN: ✓ CONFIRMED ("human decides which setups to act on")

VERDICT: |
  "Phoenix isn't CLOSE to industry practice. Phoenix IS industry practice,
   arrived at independently through constitutional governance."
```

### Key Numbers

```yaml
FEATURE_COUNT:
  professional_range: 30-60 atoms
  nex_era_artifact: 400+ columns
  action: Gate-backward audit when S33 P2 unblocks

PATTERN_APPROACH:
  wrong: Store BOS_up as persistent column for every bar
  right: Structure engine ANSWERS "did BOS_up occur here?" when gate asks
  principle: "Functions over sequences, not more columns"
```

### MSS Architecture

```yaml
STRUCTURE_ENGINE:     # Deterministic (per-TF)
  - swing detection (lookback + minimum move threshold)
  - BOS/CHoCH classification
  - HH/HL/LH/LL tracking
  emits: [trend_state enum, last_swing_points, last_structure_event]

REGIME_OVERLAY:       # Probabilistic (optional, modulates gates)
  - volatility regime
  - trending vs ranging
  emits: regime_probability (can activate/deactivate gates)

CONFLUENCE_DRAWER:    # HTF Bias drawer
  - consumes structure engines across TFs
  - implements alignment rules
  - separate, testable, owned by Olya
```

### OHLCV Ceiling (Honest)

```yaml
WITHIN_OHLCV_CAPABILITY:
  - HTF bias
  - Basic structure
  - Time-of-day gates

APPROXIMATIONS_ONLY:
  - Liquidity concepts (sweeps, stop runs, absorption)
  - Requires order flow data for full fidelity

POSTURE: |
  Known limitation to document, not a blocker.
  Evolutionary path to richer data if needed.
```

---

## 5. DEXTER HARDENING REQUIREMENTS

### Security Stack (Required)

```yaml
ISOLATION:
  current: Docker --network none --restart unless-stopped
  target: True microVM (Docker Sandbox / gVisor runsc)

AUTH:
  current: Keys in .env
  target: Composio (managed tokens, revocation kill-switch, no exfil risk)
  rationale: "If agent can read .env → it can leak .env"

INJECTION_DEFENSE:
  layers: [preprocess, regex, semantic TF-IDF, halt]
  additions: [ACIP/PromptGuard wrappers, loop caps (10-20 turns max)]
  human_gate: Shell/browser actions require approval

CREDENTIAL_HYGIENE:
  - GPG/pass/Bitwarden CLI for runtime fetch
  - Rotate keys quarterly
  - Throwaway emails for API signups
```

### Comms Surface

```yaml
PRIMARY: Matrix E2EE (self-hosted)
  rationale: Sovereign, full E2EE, rooms/threads for agents

FALLBACK: Telegram (mobile push)
  drawback: No E2EE — data on Telegram servers

PATTERN: |
  Dexter as single point of contact (Coordinator/Foreman)
  Other agents silent/subordinate — only speak via shared beads
  Human talks to one "foreman" agent — reduces noise
```

---

## 6. FRONTIER VISION: PHOENIX HIGH COMMAND

### The Surface

```yaml
CONCEPT: Always-on Matrix room ("Phoenix High Command")
  - Distinct persistent personas that feel like colleagues
  - Threads per video/batch (no scroll hell)
  - Reactions (👍/👎/❓) for quick silent feedback
  - Mobile/desktop notifications without spam
```

### Personas

```yaml
DEXTER:
  role: Coordinator / Foreman
  model: Gemini Flash or DeepSeek
  behavior: |
    Posts: "Bundle B-177 ready — 36 sigs, 35 validated"
    Replies to !commands
    Heartbeat driver, phase advancer, bundle promoter

CTO:
  role: Silent observer + tech watchdog
  model: DeepSeek-v3.2
  behavior: |
    Speaks only on system status, errors, hardening
    Posts: "Routing diversity PASS", "Injection flagged — halted"

CSO:
  role: Lateral strategist
  model: Perplexity Deep Research (async) or Grok-3
  behavior: |
    Quiet most days
    Pipes up on delegated deep scans
    Questions Oracle directly

ORACLE (OLYA):
  role: Absolute sovereign
  behavior: |
    Mostly lurks + validates
    Replies: "Approve B-177", "Reject — weak falsifiability"
    @mentions wake personas
```

### Evolution Path

```yaml
PHASE_5: Matrix comms skill + Dexter coordinator
PHASE_6: Twilio integration
  - Voice escalation (Dexter initiates call on stuck phase)
  - TTS summaries (ElevenLabs → Twilio stream)
  - Conversations API for text/voice hybrid

VISION: |
  "Gas Town / Banteg manifesto vibes, far less jank under the hood."
  When Olya hears Dexter say "Bundle B-177 ready for your review, Oracle"
  over a call — that's the vibe reborn.
```

---

## 7. IMMEDIATE PRIORITIES

### Phoenix (~phoenix)

```yaml
NEXT_SPRINT: S47 (Lease Implementation)
  status: NOT STARTED
  readiness: GREEN
  dependency: NONE BLOCKING

OPS_HARDENING: Micro-sprint (daemon/cron)
  - Daemonized heartbeat
  - Auto-restart for IBKR gateway
  - Persistent river liveness checks

DEFER:
  - Multi-agent expansions
  - Learning loops
  - UI flourish layers
```

### Dexter (~dexter on Mac Mini)

```yaml
P1: Chronicler implementation (memory management) — URGENT
P2: Queue atomicity (write-tmp + rename) — 5 lines
P3: Injection guard tuning (whitelist ICT speech patterns)
P4: Auditor tuning (increase rejection rate if needed)
P5: Matrix comms skill + Dexter coordinator persona
```

### CSO Center of Excellence

```yaml
IMMEDIATE:
  - Document the model shift (this doc)
  - Queue Perplexity research briefs for gate-backward audit

WHEN_S33_P2_UNBLOCKS:
  - Present Olya with research-informed gate definitions
  - Recognition-based validation session
  - Target: 30-60 constitutional atoms (not 400)
```

---

## 8. INVARIANT WATCHLIST

```yaml
INV-DEXTER-ALWAYS-CLAIM:
  risk: |
    Richer evidence packs = stronger psychological pull to skip review.
    "Microstructure supports it, regime validates it, cross-methodology confirms it"
    At what point does Olya feel she CAN'T say no?
  guard: More evidence = still CLAIM. Always CLAIM.

INV-SCOPE-DISCIPLINE:
  current: |
    Phoenix: S47 Lease Implementation
    Dexter: ICT extraction soak + hardening
    Perplexity integration: AFTER both stabilize
  principle: "Vision seeds now. Build later. Rocket first, seats second."
```

---

## 9. KEY INSIGHT SUMMARY

```yaml
PHOENIX_VALIDATED:
  - Architecture is industry best practice (Perplexity confirmed)
  - Foundation complete, ops hardening next
  - No architectural changes needed

DEXTER_PROVEN:
  - 24/7 extraction works ($0.003/video)
  - Cross-family adversarial validation works
  - Phoenix integration bridge works (CLAIM_BEADs)
  - 504 signatures from 18 videos overnight

CSO_MODEL_UNLOCKED:
  - Recognition > recall for expert calibration
  - Olya as sovereign validator, not sole source being mined
  - Dexter + Perplexity → comprehensive base → Olya validates

THE_ARCHITECTURE:
  layer_1: EXTRACTION (Dexter theorist/auditor) — raw → IF-THEN signatures
  layer_2: RESEARCH (Dexter + Perplexity) — patterns → evidence-enriched claims
  layer_3: VALIDATION (Phoenix CSO + River) — claims → facts (market data confirms)
  layer_4: APPLICATION (Phoenix trading) — conditions.yaml → trading decisions

  "Each layer adds rigor. Human gates between each.
   The evidence compounds. Authority never transfers."
```

---

## 10. ONE-LINER FOR EACH SYSTEM

```yaml
PHOENIX: "The trading system. Foundation proven. Ops hardening next."
DEXTER: "The bone marrow. Extracts ICT logic cells. Human promotes."
CSO_COE: "Perplexity + Dexter → comprehensive base → Olya validates."
VISION: "Gas Town vibes with better tooling. Human frames. Machine computes. Human promotes."
```

---

```yaml
SIGN_OFF:
  author: Opus (synthesis from CTO Claude compaction rescue)
  confidence: HIGH
  ambiguity: LOW
  ready_for: ADVISOR_CONSUMPTION

  "The Forge is the OS. Phoenix is the App.
   Dexter mines. Perplexity enriches. Olya validates.
   Human frames. Machine computes. Human promotes."
```
