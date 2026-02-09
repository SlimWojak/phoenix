# Ground Tests — Mission Control v0.2

Validates Claude Code native capabilities before building Mission Control scaffold.

## Must Pass
- GT-1: MEMORY.md persistence
- GT-4: Hooks (on-session-end)

## Should Pass
- GT-2: --resume
- GT-5: --headless

## Nice to Pass
- GT-3: mcp-memory-keeper MCP integration
- GT-6: Native subagents

## Execution
1. Opus in Cursor runs prep (Tasks A-D)
2. G runs tests in Claude Code CLI (GT-1 through GT-6)
3. Results recorded in RESULTS.yaml
