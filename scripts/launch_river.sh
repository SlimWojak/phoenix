#!/bin/bash
# River Streamer Launch Script — invoked by launchd (com.a8ra.river)
# Streams IBKR 1m bars to daily parquet files.
# Auto-restarts on crash via launchd KeepAlive.

cd ~/phoenix || exit 1

export RIVER_ROOT="${RIVER_ROOT:-$HOME/phoenix-river}"
export PYTHONUNBUFFERED=1

# Use venv python if available, else fall back to pyenv shim
if [ -f .venv/bin/python3 ]; then
    exec .venv/bin/python3 -m river.streamer "$@"
else
    exec python3 -m river.streamer "$@"
fi
