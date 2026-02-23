#!/bin/bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')
REASON=$(echo "$INPUT" | jq -r '.reason')
echo "HOOK_FIRED: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /tmp/gt4_hook_result.txt
echo "SESSION_ID: $SESSION_ID" >> /tmp/gt4_hook_result.txt
echo "REASON: $REASON" >> /tmp/gt4_hook_result.txt
