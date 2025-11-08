#!/bin/bash

LOG=/project/root/path/cron.log

echo "Running At: $(date)" >> "$LOG" 2>&1

cd /project/root/path || { echo "Failed to cd to project dir" >> "$LOG"; exit 1; }

/project/root/path/venv/bin/python /project/root/path/run_briefing.py >> "$LOG" 2>&1

echo "Finished At: $(date)" >> "$LOG" 2>&1
