#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$DIR/cron.log"

echo "Running At: $(date)" >> "$LOG" 2>&1
cd "$DIR" || { echo "Failed to cd to project dir" >> "$LOG"; exit 1; }
"$DIR/venv/bin/python" "$DIR/run_briefing.py" >> "$LOG" 2>&1
echo "Finished At: $(date)" >> "$LOG" 2>&1

