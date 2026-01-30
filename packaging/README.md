# Phoenix Packaging — S41 Track D

Creates distributable macOS DMG from Phoenix.

## Quick Start

```bash
# From phoenix root
cd packaging
./build_dmg.sh
```

Output: `dist/Phoenix-0.41.0.dmg`

## Prerequisites

```bash
# Install build dependencies
pip install py2app rumps

# Optional: prettier DMG (recommended)
brew install create-dmg
```

## What Gets Packaged

- Menu bar widget (main entry point)
- All Phoenix modules (governance, brokers, cso, etc.)
- Narrator templates (jinja2)
- CSO knowledge base (conditions.yaml)
- Schemas (beads, orientation)

## What's Excluded

- Test suites (pytest, etc.)
- Development tools (mypy, ruff)
- Pre-commit hooks
- tkinter/turtle (unused GUI)

## Installation

1. Open `dist/Phoenix-0.41.0.dmg`
2. Drag `Phoenix.app` to Applications
3. Launch from Applications

The app runs as a menu bar item (no dock icon).

## Configuration

First run requires:
- IBKR credentials (for paper mode)
- Telegram bot token (optional, for alerts)

Set via environment or config file.

## Verification

To verify the packaged app:

```bash
# Check app structure
ls -la dist/Phoenix.app/Contents/

# Run app from terminal (see logs)
dist/Phoenix.app/Contents/MacOS/Phoenix
```

## Notes

- **Paper Mode**: IBKR runs in paper mode by default
- **No Network Required**: App is self-contained post-install
- **SLM Integration**: Phase 2 will add Unsloth distillation

## Troubleshooting

### "App is damaged" error
The app is unsigned. To allow:
```bash
xattr -cr dist/Phoenix.app
```

### Missing modules
If app fails with import errors, verify packages in `setup_app.py`

### Build fails
Check py2app version compatibility:
```bash
pip install --upgrade py2app
```

---

*S41 Track D: DMG Packaging (Current Phoenix)*
*SLM guard dog integration comes in Phase 2*
