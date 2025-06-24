#!/bin/bash

# Script to monitor countdown messages from cursor-autopilot logs
# This is useful when running with --api flag to see countdown messages clearly

LOG_DIR="$(dirname "$0")/../logs"

echo "🕐 Watching for countdown messages in cursor-autopilot logs..."
echo "   Log directory: $LOG_DIR"
echo "   Press Ctrl+C to stop"
echo ""

# Find the most recent log file and follow it
LATEST_LOG=$(ls -t "$LOG_DIR"/autopilot_*.log 2>/dev/null | head -n1)

if [ -z "$LATEST_LOG" ]; then
    echo "❌ No log files found in $LOG_DIR"
    echo "   Make sure cursor-autopilot is running"
    exit 1
fi

echo "📁 Following log file: $(basename "$LATEST_LOG")"
echo ""

# Filter for countdown messages and format them nicely
tail -f "$LATEST_LOG" | grep --line-buffered -i "countdown:" | while read -r line; do
    # Extract just the countdown part for cleaner output
    if [[ $line =~ \[([^\]]+)\].*countdown:[[:space:]]*([0-9]+)[[:space:]]*seconds ]]; then
        platform="${BASH_REMATCH[1]}"
        seconds="${BASH_REMATCH[2]}"
        timestamp=$(date '+%H:%M:%S')
        printf "🕐 %s | %-20s | %3d seconds until next prompt\n" "$timestamp" "$platform" "$seconds"
    else
        # Fallback - just print the line with timestamp
        timestamp=$(date '+%H:%M:%S')
        echo "🕐 $timestamp | $line"
    fi
done 