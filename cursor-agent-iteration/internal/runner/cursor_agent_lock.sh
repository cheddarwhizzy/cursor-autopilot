#!/usr/bin/env bash
# Wrapper script for cursor-agent with file locking to prevent concurrent access issues

set -euo pipefail

# Lock file for cursor-agent to prevent race conditions on CLI config
LOCK_FILE="$HOME/.cursor/cursor-agent.lock"
LOCK_FD=200

# Create directory if it doesn't exist
mkdir -p "$(dirname "$LOCK_FILE")"

# Function to acquire lock
acquire_lock() {
    local timeout=60  # Wait up to 60 seconds for lock
    local elapsed=0
    local wait_time=0.1
    
    # Try to acquire lock with timeout
    while [ $elapsed -lt $timeout ]; do
        if mkdir "$LOCK_FILE" 2>/dev/null; then
            # Lock acquired
            return 0
        fi
        
        # Wait a bit
        sleep $wait_time
        elapsed=$(echo "$elapsed + $wait_time" | bc)
    done
    
    # Timeout - force remove stale lock
    echo "Warning: Lock timeout, removing stale lock" >&2
    rm -rf "$LOCK_FILE"
    
    # Try one more time
    if mkdir "$LOCK_FILE" 2>/dev/null; then
        return 0
    fi
    
    return 1
}

# Function to release lock
release_lock() {
    rm -rf "$LOCK_FILE"
}

# Trap to ensure lock is released on exit
trap release_lock EXIT INT TERM

# Acquire lock before running cursor-agent
if ! acquire_lock; then
    echo "Error: Could not acquire lock for cursor-agent" >&2
    exit 1
fi

# Run cursor-agent with all arguments
cursor-agent "$@"

