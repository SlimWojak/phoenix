# WarBoar HUD

A read-only SwiftUI panel that displays Phoenix trading system state.

```
🐗 OINK OINK
```

## Overview

WarBoar HUD is a floating macOS panel that:
- Reads `manifest.json` from Phoenix via file seam
- Displays 9 sections: Session, Portfolio, Positions, Trades, Gates, Narrator, Requires Action, Health, Lease
- Uses vibrancy for a professional, glassy appearance
- Pins to left screen edge for always-visible monitoring

**HUD is a projection, not a participant.** Phoenix runs independently.

## Requirements

- macOS 14.0 (Sonoma) or later
- Xcode 15.0+
- Swift 5.9+

## Build

```bash
# One-command build
./scripts/build.sh

# Or manually
cd WarBoarHUD
xcodebuild -scheme WarBoarHUD -configuration Debug build
```

## Run

```bash
# Link Phoenix state directory first
./scripts/link-phoenix-state.sh

# Launch
open WarBoarHUD/build/Debug/WarBoarHUD.app
```

Or open `WarBoarHUD/WarBoarHUD.xcodeproj` in Xcode and run.

## Phoenix Integration

HUD reads from Phoenix via file seam:

```
Phoenix writes → ~/phoenix/state/manifest.json
HUD reads     → ~/phoenix-hud/state/manifest.json (symlink)
```

Create symlink:
```bash
./scripts/link-phoenix-state.sh
```

## Project Structure

```
phoenix-hud/
├── README.md
├── CANONICAL_SPEC.md      # Full specification
├── WarBoarHUD/            # Xcode project
│   ├── App/               # Entry point + AppDelegate
│   ├── Panel/             # NSPanel + positioning
│   ├── Views/             # SwiftUI sections
│   ├── Models/            # Codable data structures
│   ├── Services/          # File watcher, parser
│   └── Styles/            # Colors, typography
├── scripts/               # Build helpers
└── docs/                  # Integration docs
```

## Key Invariants

- **INV-HUD-READ-ONLY**: HUD never writes to Phoenix state
- **INV-HUD-CRASH-ISOLATION**: HUD crash doesn't affect Phoenix
- **INV-HUD-STALE-VISIBLE**: Shows warning if manifest >60s old
- **INV-HUD-COLOR-BOUNDARY**: Severity colors for health only

See `CANONICAL_SPEC.md` for complete specification.

## License

Internal WarBoar project.
