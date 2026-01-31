# WARBOAR HUD — CANONICAL SPECIFICATION v1.1

```yaml
PROJECT: WarBoarHUD
VERSION: 1.1
STATUS: LOCKED_FOR_BUILD
DATE: 2026-01-31
```

---

## 1. OVERVIEW

WarBoar HUD is a read-only SwiftUI vertical panel that displays Phoenix trading system state. It reads `manifest.json` via file seam and renders a glanceable surface for operators (Olya + G) on ultrawide monitors.

**Core Principles:**
- HUD is a projection, not a participant
- Phoenix is the brain; HUD is the glanceable surface
- If HUD crashes, Phoenix doesn't flinch
- "Claude Desktop level professionalism"

---

## 2. INVARIANTS

```yaml
INV-HUD-READ-ONLY:
  rule: "HUD never writes to Phoenix state/"
  enforcement: No write APIs exist in HUD

INV-HUD-PROJECTION:
  rule: "HUD is projection, not participant"
  enforcement: HUD makes zero decisions

INV-HUD-INDEPENDENCE:
  rule: "Phoenix runs without HUD"
  enforcement: No Phoenix dependencies on HUD

INV-HUD-CRASH-ISOLATION:
  rule: "HUD crash doesn't affect Phoenix"
  enforcement: Separate process, no IPC

INV-HUD-ATOMIC-READ:
  rule: "HUD only reads atomically-written manifest.json"
  enforcement: Phoenix writes .tmp → rename; HUD ignores .tmp files

INV-HUD-STALE-VISIBLE:
  rule: "If manifest not updated within 60s, show STALE overlay"
  enforcement: Red banner "STALE STATE — CHECK PHOENIX"

INV-HUD-COLOR-BOUNDARY:
  rule: "Severity colors (green/amber/red) reserved for HEALTH states only"
  enforcement: PnL uses neutral text; trade dots are neutral blue

INV-HUD-NO-SUGGEST:
  rule: "REQUIRES ACTION section cannot contain suggestions"
  enforcement: Only facts and required acknowledgments

INV-HUD-SOURCE-LINK:
  rule: "Trade/gate lines can cite bead_id for provenance"
  enforcement: bead_id included in manifest schema
```

---

## 3. TECHNOLOGY STACK

```yaml
language: Swift 5.9+
ui_framework: SwiftUI
window_framework: AppKit (NSPanel)
minimum_macos: 14.0 (Sonoma)
dependencies: NONE (zero external dependencies)

panel_config:
  class: NSPanel subclass
  isFloatingPanel: true
  level: .floating
  hidesOnDeactivate: false
  isMovableByWindowBackground: true
  styleMask: [.borderless, .nonactivatingPanel]
  titlebarAppearsTransparent: true
  collectionBehavior: [.canJoinAllSpaces, .fullScreenAuxiliary]

vibrancy:
  view: NSVisualEffectView
  material: .ultraThinMaterial
  blendingMode: .behindWindow

file_watching:
  primary: DispatchSourceFileSystemObject
  fallback: Timer (1s polling if no events)
  target: phoenix/state/manifest.json
  debounce: 100ms
  throttle_cap: 500ms

icons: SF Symbols (.hierarchical rendering)
```

---

## 4. STATE MANIFEST SCHEMA v1.1

```json
{
  "meta": {
    "schema_version": "1.1",
    "generated_at": "2026-01-31T14:30:00Z",
    "manifest_seq": 12345,
    "phoenix_state_hash": "abc123",
    "source": "phoenix"
  },

  "session": {
    "kz": "LONDON",
    "active": true,
    "time_remaining": "2h 15m",
    "next_session": "NEW_YORK",
    "next_start": "13:00"
  },

  "portfolio": {
    "balance": 10234.56,
    "currency": "USD",
    "today_pnl": 82.50,
    "today_pct": 0.81,
    "week_pct": 2.3
  },

  "live_positions": [
    {
      "pair": "EURUSD",
      "direction": "LONG",
      "entry_price": 1.0842,
      "current_price": 1.0857,
      "pnl_pips": 15,
      "pnl_dollars": 45.00,
      "duration": "2h 15m",
      "bead_id": "TRADE_2026_01_31_001"
    }
  ],

  "recent_trades": {
    "items": [
      {
        "bead_id": "TRADE_2026_01_31_002",
        "pair": "GBPUSD",
        "result_pips": 32,
        "close_time": "11:30"
      }
    ],
    "total_count": 10
  },

  "gates_summary": [
    {
      "pair": "EURUSD",
      "passed": 5,
      "total": 5,
      "status": "READY"
    },
    {
      "pair": "GBPUSD",
      "passed": 4,
      "total": 5,
      "status": "WATCHING"
    }
  ],

  "narrator": {
    "lines": [
      {
        "timestamp": "14:32",
        "text": "London active, 2h remaining.",
        "source_bead_id": null
      }
    ],
    "buffer_size": 20
  },

  "requires_action": [
    {
      "type": "LEASE_EXPIRY",
      "message": "Lease expires 58m — review?",
      "severity": "WARNING",
      "action_required": true
    }
  ],

  "health": {
    "overall": "GREEN",
    "status": "HEALTHY",
    "since": "2026-01-31T12:00:00Z",
    "degraded_reasons": [],
    "components": {
      "ibkr": "GREEN",
      "river": "GREEN",
      "halt_state": "GREEN",
      "lease": "GREEN",
      "decay": "GREEN"
    },
    "heartbeat_age_seconds": 5
  },

  "lease": {
    "status": "ACTIVE",
    "strategy": "ICT_FVG_v1",
    "time_remaining": "3h 30m",
    "expires_at": "2026-01-31T18:00:00Z"
  }
}
```

**Lease Status Enum:** `ABSENT | DRAFT | ACTIVE | EXPIRED | REVOKED | HALTED`

**Health Status Enum:** `HEALTHY | DEGRADED | CRITICAL | HALTED`

**Health Overall Enum:** `GREEN | YELLOW | RED`

---

## 5. HUD LAYOUT v1.1

```
┌─────────────────────────────────┐
│  ⏱ LONDON          2h 15m left │  ← Session
│  Next: NEW_YORK @ 13:00        │
├─────────────────────────────────┤
│  $10,234.56                    │  ← Portfolio
│  Today: +$82.50 (+0.81%)       │     (neutral text, +/- prefix)
│  Week:  +2.3%                  │
├─────────────────────────────────┤
│  LIVE POSITIONS                │
│  ────────────────────────────  │
│  EURUSD LONG  +15 pips  +$45   │  ← Neutral (NOT green)
│  1.0842 → 1.0857  (2h 15m)     │
├─────────────────────────────────┤
│  RECENT TRADES          ↕ 5/10 │
│  ────────────────────────────  │
│  ● GBPUSD  +32 pips    11:30  │  ← Blue dot (neutral)
│  ● EURUSD  -18 pips    09:15  │     +/- shows result
│  ● USDJPY  +24 pips    08:45  │
│  ● GBPUSD  +41 pips    07:30  │
│  ● EURUSD  -12 pips    06:15  │
├─────────────────────────────────┤
│  GATES                         │
│  ────────────────────────────  │
│  ● EURUSD  5/5  READY         │  ← Health green (ready state)
│  ○ GBPUSD  4/5  watching      │     Neutral for non-ready
│  ○ USDJPY  2/5  watching      │
├─────────────────────────────────┤
│  ┌─ WARBOAR OBSERVES ────────┐ │
│  │ 14:32 London active, 2h   │ │  ← Display-only
│  │ 14:31 EURUSD +15 steady   │ │     (Phoenix generates text)
│  │ 14:31 Systems nominal     │ │
│  │ 14:30 GBPUSD 4/5 gates    │ │
│  └───────────────────────────┘ │
├─────────────────────────────────┤
│  ⚠️ REQUIRES ACTION            │  ← Facts/acks only
│  Lease expires 58m — review?   │     NO suggestions
├─────────────────────────────────┤
│  SYSTEM HEALTH                 │  ← Traffic lights HERE
│  ● IBKR  ● River  ● Halt      │     (only place for severity colors)
│  ● Lease ● Decay              │
├─────────────────────────────────┤
│  📋 ICT_FVG_v1       3h 30m   │  ← Lease
└─────────────────────────────────┘

STALE OVERLAY (when manifest > 60s old):
┌─────────────────────────────────┐
│  ⚠️ STALE STATE — CHECK PHOENIX │
│     Last update: 73s ago        │
└─────────────────────────────────┘
```

**9 Sections:**
1. Session — Killzone name, time remaining, next session
2. Portfolio — Balance, daily/weekly PnL (neutral text)
3. Live Positions — Open trades with pips/dollars (neutral text)
4. Recent Trades — Scrollable list with blue dots (5 visible)
5. Gates — Entry conditions per pair (READY uses health green)
6. Narrator — Rolling observations from Phoenix (display-only)
7. Requires Action — Facts and required acks (no suggestions)
8. System Health — Traffic light indicators (ONLY colored section)
9. Lease — Active strategy and time remaining

---

## 6. COLOR PALETTE

```swift
extension Color {
    // ═══════════════════════════════════════════════════════════
    // HEALTH STATES ONLY — Traffic light colors
    // ═══════════════════════════════════════════════════════════
    static let healthGreen = Color(hex: "4CAF50").opacity(0.7)   // HEALTHY
    static let healthAmber = Color(hex: "FF9800").opacity(0.7)   // DEGRADED
    static let healthRed = Color(hex: "F44336").opacity(0.7)     // CRITICAL/HALTED

    // ═══════════════════════════════════════════════════════════
    // PNL/TRADES — Neutral (no dopamine colors)
    // ═══════════════════════════════════════════════════════════
    static let pnlPositive = Color.white.opacity(0.8)   // Brighter, NOT green
    static let pnlNegative = Color.white.opacity(0.6)   // Muted, NOT red
    // Direction indicated by +/- prefix only

    // ═══════════════════════════════════════════════════════════
    // TRADE HISTORY — Neutral accent
    // ═══════════════════════════════════════════════════════════
    static let tradeDot = Color(hex: "2196F3").opacity(0.5)  // Blue for all

    // ═══════════════════════════════════════════════════════════
    // TEXT HIERARCHY
    // ═══════════════════════════════════════════════════════════
    static let primaryText = Color.white.opacity(0.9)
    static let secondaryText = Color.white.opacity(0.6)
    static let tertiaryText = Color.white.opacity(0.4)

    // ═══════════════════════════════════════════════════════════
    // ACCENTS
    // ═══════════════════════════════════════════════════════════
    static let activeAccent = Color(hex: "2196F3").opacity(0.8)
    static let mutedSeparator = Color.white.opacity(0.15)
    static let staleBanner = Color(hex: "F44336").opacity(0.9)
}
```

**Constitutional Boundary:** Severity colors (green/amber/red) are ONLY for health indicators. PnL and trade results use neutral text with +/- prefixes. This prevents "dopamine casino UI" and maintains authority.

---

## 7. NARRATOR ARCHITECTURE

```yaml
SOURCE_OF_TRUTH: Phoenix (narrator/renderer.py)

Phoenix Responsibility:
  - Generates observations via narrator templates
  - Writes narrator.lines[] to manifest.json
  - Each line includes: timestamp, text, source_bead_id

HUD Responsibility:
  - Displays narrator.lines[] VERBATIM
  - Maintains rolling buffer UI (last 20 lines)
  - NO template rendering in HUD
  - NO text generation in HUD

File Rename:
  BEFORE: Services/NarratorEngine.swift
  AFTER: Services/NarratorBufferViewModel.swift

Purpose: Display-only view model that presents Phoenix-generated text
```

---

## 8. INTEGRATION SEAM

```yaml
PATTERN: FILE_SEAM (proven)

Phoenix Writes:
  path: phoenix/state/manifest.json
  method: Atomic (write .tmp → os.rename)
  frequency: Every state change (debounced 100ms)
  heartbeat: Every 30s minimum

HUD Reads:
  method: DispatchSourceFileSystemObject (primary)
  fallback: Timer-based polling every 1s
  path: Symlinked from phoenix/state/
  action: Parse → Update @Published StateManifest

Error Handling:
  parse_error: Keep last valid manifest + show CORRUPT badge
  file_missing: Show NO_STATE indicator
  stale_manifest: Show STALE overlay after 60s

Symlink Setup:
  command: ln -s ~/phoenix/state ~/phoenix-hud/state
```

---

## 9. CHAOS GATES

| Gate | Attack Vector | Expected Behavior |
|------|---------------|-------------------|
| `corrupt_manifest` | Write invalid JSON | Keep last good + CORRUPT badge |
| `delete_manifest` | rm manifest.json | Show NO_STATE, not blank |
| `stop_updates_10s` | Phoenix stops writing | Show STALE with age counter |
| `huge_manifest` | 200KB with 1000 trades | Responsive; truncation applied |
| `ultrawide_resize` | Hot-swap monitor | Panel repositions to visible area |
| `dark_mode_toggle` | System appearance flip | Colors update correctly |
| `manifest_flood` | 1000 updates/sec | Debounce drops excess, 500ms cap |

**Mitigations:**
- `ultrawide_resize`: NSWorkspace.didChangeScreenParametersNotification
- `dark_mode_toggle`: .environment(\.colorScheme) observer
- `manifest_flood`: 500ms throttle cap on UI updates

---

## 10. REPOSITORY STRUCTURE

```
phoenix-hud/
├── README.md                        # Setup + build instructions
├── CANONICAL_SPEC.md                # This document
├── .gitignore                       # Xcode ignores
├── .cursorrules                     # Opus session patterns
│
├── WarBoarHUD/                      # Xcode project root
│   ├── WarBoarHUD.xcodeproj
│   │
│   ├── App/
│   │   ├── WarBoarHUDApp.swift      # Entry point
│   │   └── AppDelegate.swift        # NSPanel setup
│   │
│   ├── Panel/
│   │   ├── HUDPanel.swift           # NSPanel subclass
│   │   ├── PanelController.swift    # Window management
│   │   └── PanelPosition.swift      # Edge pinning logic
│   │
│   ├── Views/
│   │   ├── HUDContentView.swift     # Main container
│   │   ├── SessionSection.swift
│   │   ├── PortfolioSection.swift
│   │   ├── PositionsSection.swift
│   │   ├── RecentTradesSection.swift
│   │   ├── GatesSection.swift
│   │   ├── NarratorSection.swift
│   │   ├── RequiresActionSection.swift   # Renamed from Attention
│   │   ├── HealthSection.swift
│   │   ├── LeaseSection.swift
│   │   └── StaleOverlay.swift            # Stale state display
│   │
│   ├── Models/
│   │   ├── StateManifest.swift      # Codable root struct
│   │   ├── ManifestMeta.swift
│   │   ├── Session.swift
│   │   ├── Portfolio.swift
│   │   ├── Position.swift
│   │   ├── Trade.swift
│   │   ├── GateSummary.swift
│   │   ├── NarratorLine.swift
│   │   ├── ActionItem.swift
│   │   ├── Health.swift
│   │   └── Lease.swift
│   │
│   ├── Services/
│   │   ├── ManifestWatcher.swift            # File system observer
│   │   ├── ManifestParser.swift             # JSON → StateManifest
│   │   └── NarratorBufferViewModel.swift    # Display-only (renamed)
│   │
│   ├── Styles/
│   │   ├── ColorPalette.swift       # Constitutional colors
│   │   ├── Typography.swift         # SF Pro hierarchy
│   │   └── ViewModifiers.swift      # Reusable styles
│   │
│   ├── Resources/
│   │   └── Assets.xcassets
│   │
│   └── Preview Content/
│       └── MockManifest.json        # SwiftUI preview data
│
├── Tests/
│   ├── ManifestParserTests.swift
│   ├── StaleDetectionTests.swift
│   └── ColorPaletteTests.swift
│
├── scripts/
│   ├── build.sh                     # One-command build
│   └── link-phoenix-state.sh        # Symlink helper
│
└── docs/
    ├── STATE_MANIFEST_SCHEMA.yaml   # JSON schema definition
    └── INTEGRATION.md               # Phoenix seam documentation
```

---

## 11. BUILD SEQUENCE

### PHASE 0: Phoenix Manifest Writer (Parallel Track)
```yaml
scope: phoenix/state/manifest_writer.py
deliverables:
  - Atomic write pattern (tmp → os.rename)
  - manifest_seq increment
  - generated_at timestamp
  - Schema v1.1 compliance
exit_gate: "Manifest writes atomically, seq increments correctly"
```

### PHASE 1: Skeleton
```yaml
scope: Project setup + floating panel
deliverables:
  - Xcode project created
  - NSPanel subclass with correct behaviors
  - Panel appears left-edge on launch
  - Vibrancy background applied
  - Empty HUDContentView renders
  - collectionBehavior for virtual desktops
exit_gate: "Panel launches, floats, has glassy background, follows spaces"
```

### PHASE 2: Models
```yaml
scope: Data structures from schema
deliverables:
  - StateManifest.swift (Codable from schema v1.1)
  - All child model structs (11 models)
  - MockManifest.json for previews
exit_gate: "MockManifest parses without error"
```

### PHASE 3: File Watcher
```yaml
scope: Manifest observation + stale detection
deliverables:
  - ManifestWatcher.swift (DispatchSource)
  - @Published StateManifest updates
  - STALE detection (generated_at age check)
  - Parse error fallback (keep last valid)
  - Fallback polling timer (1s if no events)
  - 500ms throttle cap
exit_gate: "File change triggers UI update within 500ms + STALE shown if >60s old"
```

### PHASE 4: Sections
```yaml
scope: All 9 section views + stale overlay
deliverables:
  - 10 view files (9 sections + StaleOverlay)
  - Typography hierarchy applied
  - Color palette enforced (constitutional boundary)
  - SF Symbols integrated
exit_gate: "All sections render with mock data, colors correct"
```

### PHASE 5: Narrator Buffer
```yaml
scope: Display-only narrator view model
deliverables:
  - NarratorBufferViewModel.swift
  - Rolling buffer display (last 20)
  - Timestamp formatting
exit_gate: "Narrator shows Phoenix-generated observations"
```

### PHASE 6: Integration
```yaml
scope: End-to-end data flow
deliverables:
  - Symlink to Phoenix state/
  - Real manifest.json consumption
  - Chaos gate verification
exit_gate: "HUD shows real Phoenix state with <500ms latency"
```

---

## 12. MVP SCOPE

**In Scope:**
- Left-edge pinned vertical panel
- All 9 sections from layout v1.1
- File watcher on state/manifest.json
- Constitutional color palette
- SF Symbols for icons
- Display-only narrator
- Traffic light health display
- Scrollable recent trades (5 visible)
- Stale state overlay
- Parse error resilience

**Out of Scope (Phase 2+):**
- PATH_C LLM observer
- Sound/haptics (OINK)
- Settings/preferences panel
- Multiple monitor support
- Resize/reposition memory
- Menu bar companion icon

---

## 13. EXIT GATES

| Gate | Criterion | Test Method |
|------|-----------|-------------|
| GATE_1 | Panel launches left-edge with glassy background | Manual launch |
| GATE_2 | All 9 sections render with mock data | SwiftUI preview |
| GATE_3 | manifest.json change → UI update <500ms | Automated script |
| GATE_4 | HUD displays real Phoenix state | Compare to CLI |
| GATE_5 | Narrator shows rolling observations | Visual inspection |
| GATE_6 | Stale overlay appears after 60s | Stop Phoenix writes |
| GATE_7 | S44 soak unaffected by HUD | Monitor alerts |

---

## 14. PASS/FAIL CONDITIONS

```yaml
PASS_CONDITION: "HUD displays real Phoenix state with <500ms latency"
FAIL_CONDITION: "Any interference with S44 soak"
```

---

*OINK OINK. 🐗🔥*
