# Olya Knowledge Intake

Drop knowledge capture files here for processing into CSO.

## Purpose

This directory receives raw methodology knowledge from Olya's capture sessions.
Opus transforms these into machine-readable specifications in `cso/knowledge/`.

## Format

- **File types:** Markdown (`.md`) or YAML (`.yaml`)
- **Structure:** Any structure is fine — Opus will parse
- **Content:** Trading concepts, rules, heuristics, examples

## Naming Convention

```
{date}_{topic}.md
```

Examples:
- `20260123_htf_context.md`
- `20260124_entry_triggers.yaml`
- `20260125_position_sizing.md`

## Workflow

1. **Olya** (via Claude): Creates knowledge file in this directory
2. **Opus** (via Cursor): Detects new file, transforms to spec
3. **Result**: Structured spec lands in `phoenix/cso/knowledge/`
4. **Archive**: Original moved to `intake/processed/`

## What to Include

- ICT concepts and definitions
- Decision rules (IF/THEN)
- Priority hierarchies
- Timing windows
- Valid/invalid conditions
- Examples (with price levels if possible)

## What NOT to Include

- Trade logs (those go to boardroom/beads)
- Screenshots (describe visually instead)
- Opinions without rules ("I feel like...")

## Example Entry

```markdown
# Kill Zone Priority

LOKZ (London Open KZ) is highest priority for entries because:
1. Bank flow concentrated 03:00-04:00 NY
2. Asian range defined, manipulation visible
3. News typically after LOKZ

Priority: LOKZ > NYKZ > Asia KZ

Valid entry: KZ + sweep + FVG + displacement
Invalid: Entry BEFORE KZ confirmation
```

## Questions?

Tag Opus in chat: "process this intake file"

---

*Phoenix CSO — Capturing Olya's methodology for machine execution*
