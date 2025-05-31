#!/bin/bash

# Exit on error
set -e

# Get the directory of the script
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd "$SCRIPT_DIR" || exit 1

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Script directory: $SCRIPT_DIR"

# Check if venv exists and activate it
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    log "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    log "Ensuring required packages are installed..."
    pip install -r requirements.txt
else
    log "Activating existing virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

# Parse arguments
PLATFORM=""

for arg in "$@"; do
    if [[ "$arg" == "--platform="* ]]; then
        PLATFORM="${arg#--platform=}"
        log "Platform specified via arg: $PLATFORM"
    fi
done

# Run the appropriate launcher
if [[ "$PLATFORM" == "cursor_meanscoop" ]]; then
    log "Launching cursor_meanscoop platform..."
    PYTHONPATH=. ./launch_cursor_only.py
elif [[ "$PLATFORM" == "windsurf_mushattention" ]]; then
    log "Launching windsurf_mushattention platform..."
    PYTHONPATH=. python3 -c "from src.actions.send_to_cursor import launch_platform; launch_platform('windsurf_mushattention', 'windsurf', '/Users/cheddarwhizzy/cheddar/mushattention/mushattention')"
elif [[ -z "$PLATFORM" ]]; then
    # If no platform specified, launch both platforms from config
    log "No specific platform specified, checking config.yaml..."
    # First check if yq is installed
    if ! command -v yq &> /dev/null; then
        log "yq tool not found, installing with brew..."
        brew install yq
    fi
    
    # Read active platforms from config
    ACTIVE_PLATFORMS=$(yq '.general.active_platforms[]' config.yaml)
    log "Found active platforms in config: $ACTIVE_PLATFORMS"
    
    # Launch each platform
    for platform in $ACTIVE_PLATFORMS; do
        log "Launching platform: $platform"
        
        # Get platform type
        PLATFORM_TYPE=$(yq ".platforms.$platform.type" config.yaml)
        
        # Use specialized launcher for cursor platforms
        if [[ "$PLATFORM_TYPE" == "cursor" ]]; then
            log "Using specialized launcher for Cursor platform: $platform"
            PYTHONPATH=. ./launch_cursor_only.py
            platform_exit_code=$?
        elif [[ "$PLATFORM_TYPE" == "windsurf" ]]; then
            log "Using specialized launcher for WindSurf platform: $platform"
            PYTHONPATH=. ./launch_windsurf_only.py
            platform_exit_code=$?
        else
            # Use direct approach for unknown platform types
            log "Using generic launcher for platform: $platform (type: $PLATFORM_TYPE)"
            PYTHONPATH=. python3 -c "
import yaml
import os

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Get platform config directly from config file
platform_config = config.get('platforms', {}).get('$platform')
if not platform_config:
    print(f'Platform $platform not found in config')
    exit(1)

# Get platform type and project path
platform_type = platform_config.get('type', '$platform')
project_path = platform_config.get('project_path')

if not project_path:
    print(f'No project path defined for platform: $platform')
    exit(1)

# Expand user directory
project_path = os.path.expanduser(project_path)
if not os.path.exists(project_path):
    print(f'Project path does not exist: {project_path}')
    exit(1)

# Launch platform
print(f'Launching platform $platform (type: {platform_type}) with project path: {project_path}')
from src.actions.send_to_cursor import launch_platform
success = launch_platform('$platform', platform_type, project_path)

if success:
    print(f'Successfully launched $platform')
else:
    print(f'Failed to launch $platform')
    exit(1)
"
            platform_exit_code=$?
        fi
        
        # Check exit code
        if [ $platform_exit_code -ne 0 ]; then
            log "Platform $platform launch failed with exit code $platform_exit_code"
        else
            log "Platform $platform launch initiated successfully"
        fi
        
        # Give a pause between launching multiple platforms
        sleep 5
    done
else
    log "Invalid platform: $PLATFORM"
    log "Please specify a valid platform with --platform=<platform_name>"
    exit 1
fi

log "Launch script completed successfully" 