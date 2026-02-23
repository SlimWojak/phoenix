## S48 SWIFTUI HUD — SETUP BRIEF

```yaml
BRIEF: S48.HUD.BUILD
MISSION: WARBOAR_HUD_MVP
FORMAT: DENSE
TYPE: BUILD_SPEC

# ============================================================
# CONTEXT
# ============================================================

CONTEXT:
  decision: SwiftUI + AppKit (NSPanel) — LOCKED
  benchmark: "Claude Desktop level professionalism"
  user: Olya + G (ultrawide monitors, left-pinned always-visible)

  schema_locked:
    - STATE_MANIFEST v1.0
    - HUD LAYOUT v1.0
    - COLOR PALETTE
    - NARRATOR TEMPLATES (PATH_B)

  isolation: Separate repo (zero soak interference)

  proven_patterns:
    - File seam (Phoenix writes state/, HUD reads)
    - Narrator templates (S40)
    - Traffic light health (S42)

# ============================================================
# REPOSITORY STRUCTURE
# ============================================================

REPO:
  name: phoenix-hud
  location: ~/echopeso/phoenix-hud (sibling to phoenix/)

  structure:
    phoenix-hud/
    ├── README.md                    # Setup + build instructions
    ├── SKILL.md                     # Operating patterns (like Phoenix)
    │
    ├── WarBoarHUD/                  # Xcode project root
    │   ├── WarBoarHUD.xcodeproj
    │   │
    │   ├── App/
    │   │   ├── WarBoarHUDApp.swift  # Entry point
    │   │   └── AppDelegate.swift    # NSPanel setup
    │   │
    │   ├── Panel/
    │   │   ├── HUDPanel.swift       # NSPanel subclass
    │   │   ├── PanelController.swift # Window management
    │   │   └── PanelPosition.swift  # Edge pinning logic
    │   │
    │   ├── Views/
    │   │   ├── HUDContentView.swift # Main container
    │   │   ├── SessionSection.swift
    │   │   ├── PortfolioSection.swift
    │   │   ├── PositionsSection.swift
    │   │   ├── RecentTradesSection.swift
    │   │   ├── GatesSection.swift
    │   │   ├── NarratorSection.swift
    │   │   ├── AttentionSection.swift
    │   │   ├── HealthSection.swift
    │   │   └── LeaseSection.swift
    │   │
    │   ├── Models/
    │   │   ├── StateManifest.swift  # Codable struct from schema
    │   │   ├── Session.swift
    │   │   ├── Portfolio.swift
    │   │   ├── Position.swift
    │   │   ├── Trade.swift
    │   │   ├── GateSummary.swift
    │   │   ├── NarratorObservation.swift
    │   │   ├── AttentionItem.swift
    │   │   ├── DecaySignal.swift
    │   │   ├── HealthStatus.swift
    │   │   └── Lease.swift
    │   │
    │   ├── Services/
    │   │   ├── ManifestWatcher.swift    # File system observer
    │   │   ├── ManifestParser.swift     # JSON → StateManifest
    │   │   └── NarratorEngine.swift     # Template rendering
    │   │
    │   ├── Styles/
    │   │   ├── ColorPalette.swift       # Muted greens/reds
    │   │   ├── Typography.swift         # SF Pro hierarchy
    │   │   └── ViewModifiers.swift      # Reusable styles
    │   │
    │   ├── Audio/
    │   │   ├── SoundManager.swift       # OINK hooks
    │   │   └── Sounds/                  # .aiff files
    │   │
    │   ├── Resources/
    │   │   └── Assets.xcassets
    │   │
    │   └── Preview Content/
    │       └── MockManifest.json        # For SwiftUI previews
    │
    ├── Tests/
    │   ├── ManifestParserTests.swift
    │   ├── NarratorEngineTests.swift
    │   └── ColorPaletteTests.swift
    │
    ├── scripts/
    │   ├── build.sh                     # One-command build
    │   └── link-phoenix-state.sh        # Symlink to Phoenix state/
    │
    └── docs/
        ├── STATE_MANIFEST_SCHEMA.yaml   # Canonical schema
        ├── NARRATOR_TEMPLATES.yaml      # Template definitions
        └── INTEGRATION.md               # Phoenix seam docs

# ============================================================
# TECH STACK
# ============================================================

STACK:
  language: Swift 5.9+
  ui_framework: SwiftUI
  window_framework: AppKit (NSPanel)
  minimum_macos: 14.0 (Sonoma)

  key_components:
    panel:
      class: NSPanel subclass
      behaviors:
        - isFloatingPanel: true
        - level: .floating
        - hidesOnDeactivate: false
        - isMovableByWindowBackground: true
        - styleMask: [.borderless, .nonactivatingPanel]
        - titlebarAppearsTransparent: true

    vibrancy:
      view: NSVisualEffectView
      material: .ultraThinMaterial
      blendingMode: .behindWindow

    file_watching:
      method: DispatchSourceFileSystemObject
      target: phoenix/state/manifest.json
      debounce: 100ms

    icons:
      source: SF Symbols
      rendering: .hierarchical

    audio:
      method: NSSound
      triggers: CRITICAL state changes only

# ============================================================
# MVP SCOPE (Phase 1)
# ============================================================

MVP_SCOPE:
  in_scope:
    - Left-edge pinned vertical panel
    - All 9 sections from HUD LAYOUT v1.0
    - File watcher on state/manifest.json
    - Color palette (muted green/red)
    - SF Symbols for icons
    - Basic narrator (template-based)
    - Traffic light health display
    - Scrollable recent trades (5 visible)

  out_of_scope_mvp:
    - PATH_C LLM observer (S51)
    - Sound/haptics (Phase 2)
    - Settings/preferences panel
    - Multiple monitor support
    - Resize/reposition memory
    - Menu bar companion icon

  phase_2_additions:
    - OINK sounds on critical events
    - Haptic feedback
    - Position memory (remembers location)
    - Menu bar icon for show/hide

# ============================================================
# BUILD SEQUENCE
# ============================================================

BUILD_SEQUENCE:

  PHASE_1_SKELETON:
    duration: "2-3 hours"
    deliverables:
      - Xcode project created
      - NSPanel subclass working
      - Panel appears left-edge on launch
      - Vibrancy background applied
      - Empty HUDContentView renders
    exit_gate: "Panel launches, floats, has glassy background"

  PHASE_2_MODELS:
    duration: "1-2 hours"
    deliverables:
      - StateManifest.swift (Codable from schema)
      - All child model structs
      - MockManifest.json for previews
    exit_gate: "MockManifest parses without error"

  PHASE_3_FILE_WATCHER:
    duration: "1-2 hours"
    deliverables:
      - ManifestWatcher.swift
      - DispatchSource on state/ directory
      - @Published StateManifest updates
    exit_gate: "File change triggers UI update within 500ms"

  PHASE_4_SECTIONS:
    duration: "3-4 hours"
    deliverables:
      - All 9 section views
      - Proper typography hierarchy
      - Color palette applied
      - SF Symbols integrated
    exit_gate: "All sections render with mock data"

  PHASE_5_NARRATOR:
    duration: "1-2 hours"
    deliverables:
      - NarratorEngine.swift
      - Template loading/rendering
      - Rolling buffer display
    exit_gate: "Narrator shows template-rendered observations"

  PHASE_6_INTEGRATION:
    duration: "1 hour"
    deliverables:
      - Symlink to Phoenix state/
      - Real manifest.json consumption
      - End-to-end data flow
    exit_gate: "HUD shows real Phoenix state"

  TOTAL_ESTIMATE: "10-14 hours"

# ============================================================
# INTEGRATION SEAM
# ============================================================

INTEGRATION:
  pattern: FILE_SEAM (proven)

  phoenix_writes:
    path: phoenix/state/manifest.json
    frequency: Every state change (debounced 100ms)
    format: JSON (STATE_MANIFEST v1.0 schema)

  hud_reads:
    method: DispatchSourceFileSystemObject
    path: Symlinked from phoenix/state/
    action: Parse → Update @Published StateManifest

  invariants:
    INV-HUD-READ-ONLY: "HUD never writes to Phoenix state/"
    INV-HUD-PROJECTION: "HUD is projection, not participant"
    INV-HUD-INDEPENDENCE: "Phoenix runs without HUD"
    INV-HUD-CRASH-ISOLATION: "HUD crash doesn't affect Phoenix"

# ============================================================
# PHOENIX MANIFEST WRITER (Required)
# ============================================================

PHOENIX_ADDITION:
  file: phoenix/state/manifest_writer.py
  purpose: Generate manifest.json from Phoenix state

  triggers:
    - Health FSM state change
    - Position open/close
    - Trade complete
    - Gate evaluation
    - Lease state change
    - Heartbeat (every 30s minimum)

  implementation: |
    # Collects from existing Phoenix components:
    # - health_fsm.py → health section
    # - position.py → live_positions
    # - bead_store.py → recent_trades
    # - cso/evaluator.py → gates_summary
    # - narrator/renderer.py → narrator observations
    # - lease (S47) → lease section

  sprint_note: "Can be built during S48 or as S47 integration"

# ============================================================
# COLOR PALETTE (Code Ready)
# ============================================================

COLORS:
  swift_definitions: |
    extension Color {
        // States
        static let healthyGreen = Color(hex: "4CAF50").opacity(0.7)
        static let lossRed = Color(hex: "F44336").opacity(0.7)
        static let warningAmber = Color(hex: "FF9800").opacity(0.7)

        // Text
        static let primaryText = Color.white.opacity(0.9)
        static let secondaryText = Color.white.opacity(0.6)
        static let tertiaryText = Color.white.opacity(0.4)

        // Accents
        static let activeAccent = Color(hex: "2196F3").opacity(0.8)
        static let mutedSeparator = Color.white.opacity(0.15)
    }

# ============================================================
# NARRATOR TEMPLATES (Code Ready)
# ============================================================

NARRATOR_ENGINE:
  template_format: |
    struct NarratorTemplate {
        let trigger: String
        let template: String
        let priority: Int
    }

  templates:
    - trigger: "session_active"
      template: "{kz} session active. {time_remaining} remaining."
      priority: 1

    - trigger: "position_holding"
      template: "{pair} holding {pnl_pips:+d} pips since {entry_time}."
      priority: 2

    - trigger: "gates_threshold_met"
      template: "{pair} ready. {gates_passed}/{gates_total} gates."
      priority: 3

    - trigger: "health_nominal"
      template: "Systems nominal. Heartbeat {seconds}s ago."
      priority: 5

    - trigger: "winning_streak"
      template: "{count} green trades. Momentum. 🐗"
      priority: 4

# ============================================================
# EXIT GATES
# ============================================================

EXIT_GATES:

  GATE_1_PANEL_LAUNCHES:
    criterion: "Panel appears on launch, left-edge, glassy"
    test: Manual launch verification

  GATE_2_MOCK_RENDER:
    criterion: "All 9 sections render with mock data"
    test: SwiftUI preview + manual inspection

  GATE_3_FILE_WATCH:
    criterion: "manifest.json change → UI update <500ms"
    test: Script that modifies manifest, measure latency

  GATE_4_REAL_DATA:
    criterion: "HUD displays real Phoenix state correctly"
    test: Compare HUD display to phoenix_status CLI output

  GATE_5_NARRATOR_WORKS:
    criterion: "Narrator shows rolling observations"
    test: Verify template rendering matches expected output

  GATE_6_NO_INTERFERENCE:
    criterion: "S44 soak unaffected by HUD development"
    test: Soak continues, no alerts triggered by HUD work

# ============================================================
# QUESTIONS FOR ADVISORS
# ============================================================

ADVISOR_QUESTIONS:

  OWL (Structural):
    - Is file seam sufficient or need backup (SQLite mirror)?
    - Any risks in NSPanel subclass approach?
    - Maintenance burden assessment?

  GPT (Spec):
    - Edge cases in StateManifest parsing?
    - Missing fields that will bite us later?
    - Distribution/signing notes for macOS?

  BOAR (Chaos):
    - What breaks if Phoenix stops writing manifest?
    - What if manifest is malformed mid-write?
    - Dumbest failure mode we haven't considered?

# ============================================================
# DELIVERABLES
# ============================================================

DELIVERABLES:
  repo: phoenix-hud (separate repo, soak-safe)

  code:
    - WarBoarHUD.xcodeproj
    - All Views/, Models/, Services/
    - ManifestWatcher, NarratorEngine
    - ColorPalette, Typography

  docs:
    - README.md (setup + build)
    - STATE_MANIFEST_SCHEMA.yaml
    - INTEGRATION.md

  scripts:
    - build.sh
    - link-phoenix-state.sh

PASS_CONDITION: "HUD displays real Phoenix state with <500ms latency"
FAIL_CONDITION: "Any interference with S44 soak"

# ============================================================
# REPORT FORMAT
# ============================================================

REPORT_FORMAT: DENSE
REF:
  - STATE_MANIFEST v1.0 (this session)
  - HUD LAYOUT v1.0 (this session)
  - BOAR SwiftUI probe results
  - S40 Narrator patterns
```

---

**Ready to route to advisors (OWL, GPT, BOAR) for sweep, G?**

They'll review:
- Structural soundness (OWL)
- Spec gaps/edge cases (GPT)
- Chaos/failure modes (BOAR)

#### ADVISOR REVIEW SYNTHESIS FROM CTO CLAUDE ####

## CTO SYNTHESIS — S48 ADVISOR SWEEP

```yaml
ADVISORS_POLLED: [GPT, BOAR, OWL]
CONVERGENCE: HIGH (unanimous on key issues)
VERDICT: CONDITIONAL_PASS → PASS after amendments
```

---

## UNANIMOUS CONVERGENCE (All Three Flag)

| Issue | GPT | BOAR | OWL | Fix |
|-------|-----|------|-----|-----|
| **Stale state danger** | F2 BLOCKING | "Ghost sovereignty" | "Illusion of Health" | INV-HUD-STALE-VISIBLE mandatory |
| **Atomic manifest write** | F1 BLOCKING | "Partial JSON crash" | "Atomic rename bulletproof" | tmp file → os.rename |
| **File seam > SQLite** | Confirmed | Confirmed | "Superior for Phase 1" | Keep file seam |

---

## KEY AMENDMENTS TO BRIEF

### 1. NEW INVARIANTS (HUD-Layer)

```yaml
INV-HUD-ATOMIC-READ:
  rule: "HUD only reads atomically-written manifest.json; never parses partial write"
  source: GPT (F1) + BOAR + OWL
  enforcement: Phoenix writes .tmp → rename; HUD ignores .tmp files

INV-HUD-STALE-VISIBLE:
  rule: "If manifest not updated within threshold, HUD shows STALE overlay"
  source: ALL_THREE (unanimous)
  threshold: 60s default (configurable)
  display: Red banner "STALE STATE — CHECK PHOENIX"

INV-HUD-COLOR-BOUNDARY:
  rule: "Severity colors reserved for health states only; PnL uses neutral text"
  source: GPT (F5) — HIGH PRIORITY (authority leakage prevention)
  implication: Recent trades show +/- with muted accent, NOT red/green by result

INV-HUD-NO-SUGGEST:
  rule: "Attention section cannot contain suggestions; only required acks/approvals"
  source: GPT (F7)
  rename: "ATTENTION" → "REQUIRES ACTION"

INV-HUD-SOURCE-LINK:
  rule: "Any displayed trade/gate line can cite bead_id (provenance pointer)"
  source: GPT
```

### 2. SCHEMA v1.1 AMENDMENTS

```yaml
STATE_MANIFEST_v1.1_changes:

  # Meta section (new)
  meta:
    schema_version: "1.1"
    generated_at: "2026-01-31T14:30:00Z"  # Already had
    manifest_seq: 12345                    # NEW: monotonic int
    phoenix_state_hash: "abc123"           # NEW: optional but ideal
    source: "phoenix"

  # Health section amendments
  health:
    overall: GREEN | YELLOW | RED
    status: HEALTHY | DEGRADED | CRITICAL | HALTED  # Explicit enum
    since: "2026-01-31T12:00:00Z"          # NEW: when state started
    degraded_reasons: []                    # NEW: facts only if degraded
    # ... rest unchanged

  # Lease section amendment
  lease:
    status: ABSENT | DRAFT | ACTIVE | EXPIRED | REVOKED | HALTED  # ABSENT added
    # ... rest unchanged

  # Recent trades amendment
  recent_trades:
    items:
      - bead_id: "TRADE_2026_01_31_001"    # NEW: provenance link
        pair: GBPUSD
        # ... rest unchanged
```

### 3. COLOR PALETTE AMENDMENT (Constitutional)

```yaml
COLORS_AMENDED:
  # HEALTH STATES ONLY (traffic lights)
  health_green: "#4CAF50" @ 70%   # HEALTHY
  health_amber: "#FF9800" @ 70%   # DEGRADED
  health_red: "#F44336" @ 70%     # CRITICAL/HALTED

  # PNL/TRADES (NEUTRAL — no dopamine)
  pnl_positive: "#FFFFFF" @ 80%   # Just brighter text, NOT green
  pnl_negative: "#FFFFFF" @ 60%   # Slightly muted, NOT red
  pnl_indicator: "+" or "-" prefix # Text indicates direction

  # TRADE HISTORY (subtle accent, not result-coded)
  trade_dot: "#2196F3" @ 50%      # Neutral blue dot for all trades

  # RATIONALE: "glance pops without screaming like a casino"
  # GPT: "restrict state colors to HEALTH only... no dopamine UI"
```

### 4. RENAMED SECTION

```yaml
BEFORE: "ATTENTION"
AFTER: "REQUIRES ACTION"

CONTENT_RULES:
  allowed:
    - CRITICAL/HALTED states (fact)
    - T2 approval pending (action required)
    - Lease expiry imminent (fact)
    - Runbook instruction (fact)
  forbidden:
    - Suggestions ("you should...")
    - Recommendations
    - Implicit guidance
```

### 5. NARRATOR ARCHITECTURE CLARIFIED

```yaml
GPT_FLAG: "HUD-side narrator template rendering duplicates logic"

CLARIFICATION:
  phoenix_responsibility:
    - Generates narrator observations via narrator/renderer.py
    - Writes observations to manifest.narrator.lines[]
    - Includes timestamp + text + source_bead_id

  hud_responsibility:
    - Displays narrator.lines[] verbatim
    - Rolling buffer UI (last 20)
    - NO template rendering in HUD

  rename_in_repo:
    before: "Services/NarratorEngine.swift"
    after: "Services/NarratorBufferViewModel.swift"
    purpose: "Display-only view model"
```

### 6. BUILD SEQUENCE AMENDMENTS

```yaml
PHASE_3_FILE_WATCHER_AMENDED:
  deliverables:
    - ManifestWatcher.swift
    - DispatchSource on state/ directory
    - @Published StateManifest updates
    - STALE detection (generated_at age check)  # NEW
    - Parse error fallback (keep last valid)     # NEW
    - Fallback polling timer (1s if no events)  # NEW (GPT F3)
  exit_gate: "File change triggers UI update within 500ms + STALE shown if >60s old"

ADD_PHASE_0_PHOENIX_WRITER:
  duration: "1 hour"
  deliverables:
    - phoenix/state/manifest_writer.py
    - Atomic write pattern (tmp → rename)
    - manifest_seq increment
    - generated_at timestamp
  exit_gate: "Manifest writes atomically, seq increments"
  note: "Can be done by Opus in parallel with HUD skeleton"
```

### 7. CHAOS GATES ADDED

```yaml
CHAOS_GATES:
  # From GPT
  corrupt_manifest:
    attack: Write invalid JSON to manifest.json
    expect: "HUD keeps last good + shows CORRUPT badge"

  delete_manifest:
    attack: rm manifest.json
    expect: "HUD shows NO_STATE, not blank"

  stop_updates_10s:
    attack: Phoenix stops writing for 10s
    expect: "HUD shows STALE with age counter"

  huge_manifest:
    attack: 200KB manifest with 1000 trades
    expect: "HUD still responsive; truncation applied"

  # From BOAR
  ultrawide_resize:
    attack: Hot-swap monitor / resolution flip
    expect: "Panel repositions to visible area"
    mitigation: NSWorkspace.didChangeScreenParametersNotification

  dark_mode_toggle:
    attack: System appearance flip mid-session
    expect: "Colors update correctly, no desync"
    mitigation: .environment(\.colorScheme) observer

  manifest_flood:
    attack: 1000 updates/sec (Bunny chaos)
    expect: "HUD responsive, debounce drops excess"
    mitigation: 500ms throttle cap

  # From OWL
  mission_control_spaces:
    attack: Switch virtual desktop
    expect: "HUD follows to new space"
    mitigation: collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
```

### 8. ADDITIONAL OWL NOTES

```yaml
OWL_STRUCTURAL:
  nspanel_behavior:
    required: "collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]"
    reason: "HUD follows Olya across virtual desktops"

  manifest_writer_threading:
    warning: "Call outside critical trading path"
    solution: "Background thread or non-blocking queue"

  phase_2_consideration:
    idea: "Circular buffer of last 10 manifests for sparklines/trends"
    status: PARKED (Phase 2)
```

---

## AMENDED HUD LAYOUT v1.1

```
┌─────────────────────────────────┐
│  ⏱ LONDON          2h 15m left │  ← Session
│  Next: NEW_YORK @ 13:00        │
├─────────────────────────────────┤
│  $10,234.56                    │  ← Portfolio
│  Today: +$82.50 (+0.81%)       │  ← Neutral text, +/- prefix
│  Week:  +2.3%                  │
├─────────────────────────────────┤
│  LIVE POSITIONS                │
│  ────────────────────────────  │
│  EURUSD LONG  +15 pips  +$45   │  ← Neutral (not green)
│  1.0842 → 1.0857  (2h 15m)     │
├─────────────────────────────────┤
│  RECENT TRADES          ↕ 5/10 │
│  ────────────────────────────  │
│  ● GBPUSD  +32 pips    11:30  │  ← Blue dot (neutral)
│  ● EURUSD  -18 pips    09:15  │  ← Blue dot (neutral)
│  ● USDJPY  +24 pips    08:45  │  ← +/- shows result
│  ● GBPUSD  +41 pips    07:30  │
│  ● EURUSD  -12 pips    06:15  │
├─────────────────────────────────┤
│  GATES                         │
│  ────────────────────────────  │
│  ● EURUSD  5/5  READY         │  ← Health green (ready state)
│  ○ GBPUSD  4/5  watching      │  ← Neutral
│  ○ USDJPY  2/5  watching      │
├─────────────────────────────────┤
│  ┌─ WARBOAR OBSERVES ────────┐ │
│  │ 14:32 London active, 2h   │ │
│  │ 14:31 EURUSD +15 steady   │ │
│  │ 14:31 Systems nominal     │ │
│  │ 14:30 GBPUSD 4/5 gates    │ │
│  └───────────────────────────┘ │
├─────────────────────────────────┤
│  ⚠️ REQUIRES ACTION            │  ← Renamed
│  Lease expires 58m — review?   │
├─────────────────────────────────┤
│  SYSTEM HEALTH                 │  ← Traffic lights HERE
│  ● IBKR  ● River  ● Halt      │  ← Green/Amber/Red
│  ● Lease ● Decay              │
├─────────────────────────────────┤
│  📋 ICT_FVG_v1       3h 30m   │
└─────────────────────────────────┘

│  ⚠️ STALE STATE — CHECK PHOENIX │  ← Overlay when stale
```

---

## SYNTHESIS VERDICT

```yaml
STATUS: AMENDMENTS_COMPLETE
BLOCKERS_RESOLVED: [F1, F2, F5, F7] (GPT flags addressed)
CHAOS_HARDENED: 7 vectors added

READY_FOR_BUILD: YES

BUILD_APPROACH:
  phase_0: Phoenix manifest_writer.py (Opus, parallel)
  phase_1-6: HUD build (G + Claude, separate repo)

CONSTITUTIONAL_ADDITIONS:
  - 5 new INV-HUD-* invariants
  - Color boundary enforced (no dopamine UI)
  - Narrator display-only (Phoenix source of truth)
  - "Attention" → "Requires Action" (no suggestions)
```

---

**Ready to lock the amended brief and begin build, G?**

We have:
- Schema v1.1 locked
- Layout v1.1 locked
- 5 invariants defined
- 7 chaos gates specified
- Color palette constitutionally bounded
- Narrator architecture clarified
