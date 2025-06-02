#!/bin/bash

# Exit on error
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log "Script directory: $SCRIPT_DIR"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-path)
            PROJECT_PATH="$2"
            shift 2
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

log "Platform: ${PLATFORM:-not specified}"
log "Project path: ${PROJECT_PATH:-not specified}"

# Export PYTHONPATH to include the project directory
export PYTHONPATH="/Volumes/My Shared Files/Home/cheddar/cheddarwhizzy/cursor-autopilot:$PYTHONPATH"

# If platform is cursor or not specified, use our launcher
if [[ "$PLATFORM" == "cursor" || -z "$PLATFORM" ]]; then
    log "Launching Cursor..."
    log "PYTHONPATH: $PYTHONPATH"
    
    # Prepare command with project path if specified
    if [[ -n "$PROJECT_PATH" ]]; then
        log "Passing project path to launch script: $PROJECT_PATH"
        python3 launch_cursor_only.py "$PROJECT_PATH"
    else
        log "No project path specified, using config default"
        python3 launch_cursor_only.py
    fi
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log "Successfully launched Cursor"
        exit 0
    else
        log "Failed to launch Cursor"
        exit 1
    fi
else
    log "Unsupported platform: $PLATFORM"
    exit 1
fi
