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

# Parse arguments
PROJECT_PATH_OVERRIDE=""
PLATFORM_OVERRIDE=""
log "Raw arguments: $@"
for i in "$@"; do
    log "Processing argument: $i"
done

# First, check for --project-path=VALUE format
for arg in "$@"; do
    if [[ "$arg" == "--project-path="* ]]; then
        log "Found --project-path= format: $arg"
        PROJECT_PATH_OVERRIDE="${arg#--project-path=}"
        log "Extracted project path (equals format): '$PROJECT_PATH_OVERRIDE'"
        break
    fi
done

# If not found in first format, check for --project-path VALUE format
if [[ -z "$PROJECT_PATH_OVERRIDE" ]]; then
    log "Checking for --project-path VALUE format"
    for ((i=1; i<=$#; i++)); do
        if [[ "${!i}" == "--project-path" ]]; then
            log "Found --project-path at position $i, checking next argument"
            NEXT_IDX=$((i+1))
            if [[ $NEXT_IDX -le $# ]]; then
                NEXT_ARG="${!NEXT_IDX}"
                if [[ "$NEXT_ARG" != --* ]]; then
                    PROJECT_PATH_OVERRIDE="$NEXT_ARG"
                    log "Extracted project path (space format): '$PROJECT_PATH_OVERRIDE'"
                else
                    log "Next argument is a flag, not a value: $NEXT_ARG"
                fi
            else
                log "No value after --project-path"
            fi
            break
        fi
    done
fi

# First, check for --platform=VALUE format
for arg in "$@"; do
    if [[ "$arg" == "--platform="* ]]; then
        log "Found --platform= format: $arg"
        PLATFORM_OVERRIDE="${arg#--platform=}"
        log "Extracted platform (equals format): '$PLATFORM_OVERRIDE'"
        break
    fi
done

# If not found in first format, check for --platform VALUE format
if [[ -z "$PLATFORM_OVERRIDE" ]]; then
    log "Checking for --platform VALUE format"
    for ((i=1; i<=$#; i++)); do
        if [[ "${!i}" == "--platform" ]]; then
            log "Found --platform at position $i, checking next argument"
            NEXT_IDX=$((i+1))
            if [[ $NEXT_IDX -le $# ]]; then
                NEXT_ARG="${!NEXT_IDX}"
                if [[ "$NEXT_ARG" != --* ]]; then
                    PLATFORM_OVERRIDE="$NEXT_ARG"
                    log "Extracted platform (space format): '$PLATFORM_OVERRIDE'"
                else
                    log "Next argument is a flag, not a value: $NEXT_ARG"
                fi
            else
                log "No value after --platform"
            fi
            break
        fi
    done
fi

if [[ -n "$PROJECT_PATH_OVERRIDE" ]]; then
    log "Final project path override: '$PROJECT_PATH_OVERRIDE'"
else
    log "No project path override detected in arguments"
fi

if [[ -n "$PLATFORM_OVERRIDE" ]]; then
    log "Final platform override: '$PLATFORM_OVERRIDE'"
else
    log "No platform override detected in arguments"
fi

# Determine the platform to run
platform_to_run=""
if [ -n "$PLATFORM_OVERRIDE" ]; then
    # Handle comma-separated list if provided via CLI
    IFS=',' read -r -a cli_platforms <<< "$PLATFORM_OVERRIDE"
    # Trim whitespace from platform names
    platform_to_run_array=()
    for p in "${cli_platforms[@]}"; do
        trimmed_p=$(echo "$p" | xargs) # xargs trims leading/trailing whitespace
        if [[ -n "$trimmed_p" ]]; then
             platform_to_run_array+=("$trimmed_p")
        fi       
    done
    # Convert array back to space-separated string for easier checking later
    platform_to_run="${platform_to_run_array[@]}"
    log "Using platform(s) specified via --platform: $platform_to_run"
else
    # Read the *list* of active platforms from config.yaml if CLI platform not specified
    # Use yq to extract the list as JSON, then jq to format as space-separated string
    active_platforms_str=$(yq e -o=json '.general.active_platforms' "$SCRIPT_DIR/config.yaml" | jq -r '.[]' | paste -sd ' ' -)
    # Check if yq/jq returned null or empty string
    if [ -z "$active_platforms_str" ] || [ "$active_platforms_str" == "null" ]; then
        echo "Error: No active platforms specified in config.yaml (general.active_platforms) and --platform not provided." >&2
        exit 1
    fi
    platform_to_run="$active_platforms_str"
    log "No --platform specified, using active platforms from config: $platform_to_run"
fi

# --- Moved Termination Block Here ---
log "Terminating relevant applications before restart..."

# Check if windsurf is one of the platforms to run
if echo " $platform_to_run " | grep -q "windsurf"; then
    log "Terminating WindSurf (windsurf platform is active)..."
    # Try multiple app names and methods
    killall -9 WindSurf 2>/dev/null || true
    killall -9 Windsurf 2>/dev/null || true
    killall -9 windsurf 2>/dev/null || true
    # Try with osascript quit (graceful)
    osascript -e 'tell application "WindSurf" to quit' 2>/dev/null || true
    # Wait a moment
    sleep 2
else
    log "Skipping WindSurf termination (windsurf platform is not active)"
fi

# Check if cursor is one of the platforms to run
if echo " $platform_to_run " | grep -q "cursor"; then
    log "Terminating Cursor (cursor platform is active)..."
    killall -9 Cursor 2>/dev/null || true
    osascript -e 'tell application "Cursor" to quit' 2>/dev/null || true
    sleep 2 # Wait for Cursor to close
else
     log "Skipping Cursor termination (cursor platform is not active)"
fi

log "Application termination attempts completed"
# --- End Moved Termination Block ---

# Always delete the initial prompt sent file to ensure initial prompt is sent
rm -f "$SCRIPT_DIR/.initial_prompt_sent"

# Check if pyenv is installed and set version
if command -v pyenv &> /dev/null; then
    PYTHON_VERSION="3.11.0"
    if pyenv versions --bare | grep -q "^${PYTHON_VERSION}$"; then
        log "Setting Python version to $PYTHON_VERSION using pyenv..."
        # Setting local might be safer than global if needed
        # pyenv local $PYTHON_VERSION 
        # Setting global for now as per original script
        pyenv global $PYTHON_VERSION
    else
        log "Warning: Python version $PYTHON_VERSION not installed via pyenv. Attempting to install..."
        pyenv install -s "$PYTHON_VERSION"
        pyenv global "$PYTHON_VERSION"
    fi
else
    log "Warning: pyenv not found. Using system default python3."
fi

# Create and activate virtual environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

log "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install/Update required packages quietly
log "Ensuring required packages are installed..."
pip install -r requirements.txt -q

# --- First launch platforms using specialized launchers ---
log "Starting platforms launch phase..."

# Read active platforms from config if not overridden
if [ -z "$PLATFORM_OVERRIDE" ]; then
    # First check if yq is installed
    if ! command -v yq &> /dev/null; then
        log "yq tool not found, installing with brew..."
        brew install yq
    fi
    
    # Read active platforms from config
    ACTIVE_PLATFORMS=$(yq '.general.active_platforms[]' config.yaml)
    log "Found active platforms in config: $ACTIVE_PLATFORMS"
else
    ACTIVE_PLATFORMS="$PLATFORM_OVERRIDE"
    log "Using override platforms: $ACTIVE_PLATFORMS"
fi

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
import sys

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Get platform config directly from config file
platform_config = config.get('platforms', {}).get('$platform')
if not platform_config:
    print(f'Platform $platform not found in config')
    sys.exit(1)

# Get platform type and project path
platform_type = platform_config.get('type', '$platform')
project_path = platform_config.get('project_path')

if not project_path:
    print(f'No project path defined for platform: $platform')
    sys.exit(1)

# Expand user directory
project_path = os.path.expanduser(project_path)
if not os.path.exists(project_path):
    print(f'Project path does not exist: {project_path}')
    sys.exit(1)

# Launch platform
print(f'Launching platform $platform (type: {platform_type}) with project path: {project_path}')
from src.actions.send_to_cursor import launch_platform
success = launch_platform('$platform', platform_type, project_path)

if success:
    print(f'Successfully launched $platform')
    sys.exit(0)
else:
    print(f'Failed to launch $platform')
    sys.exit(1)
"
        platform_exit_code=$?
    fi
    
    # Check exit code
    if [ $platform_exit_code -ne 0 ]; then
        log "Platform $platform launch failed with exit code $platform_exit_code"
        exit $platform_exit_code
    else
        log "Platform $platform launch initiated successfully"
    fi
    
    # Give a pause between launching multiple platforms
    log "Waiting 5 seconds before continuing..."
    sleep 5
done

# --- Now start the watcher to handle prompts and monitoring ---
log "Starting Cursor Autopilot watcher..."

# Determine the Python entry point
PYTHON_ENTRY_POINT="src/watcher.py"

if [ ! -f "$PYTHON_ENTRY_POINT" ]; then
    # Fallback if watcher.py was deleted/renamed incorrectly
    if [ -f "watcher.py" ]; then
        PYTHON_ENTRY_POINT="watcher.py"
        log "Warning: $SCRIPT_DIR/src/watcher.py not found, falling back to $SCRIPT_DIR/watcher.py"
    else
         log "Error: Python entry point $SCRIPT_DIR/$PYTHON_ENTRY_POINT not found."
         exit 1
    fi
fi

# Pass all arguments, along with project path override if provided
log "Python execution section - Preparing to execute the Python script"
log "PROJECT_PATH_OVERRIDE='$PROJECT_PATH_OVERRIDE'"
log "Original arguments: $*"

if [[ -n "$PROJECT_PATH_OVERRIDE" ]]; then
    # Check if --project-path is already in arguments
    if echo "$*" | grep -q -- "--project-path"; then
        # Already included, pass as is
        log "Project path already in arguments, passing as is"
        log "Executing: python3 -m src.watcher $*"
        python3 -m src.watcher $*
    else
        # Add project path override to arguments
        log "Adding project path to arguments"
        log "Executing: python3 -m src.watcher --project-path \"$PROJECT_PATH_OVERRIDE\" $*"
        python3 -m src.watcher --project-path "$PROJECT_PATH_OVERRIDE" $*
    fi
else
    log "No project path override to add to Python arguments"
    log "Executing: python3 -m src.watcher $*"
    python3 -m src.watcher $*
fi

EXIT_CODE=$?
log "Python script finished with exit code $EXIT_CODE"

# Deactivate virtual environment
log "Deactivating virtual environment..."
deactivate

exit $EXIT_CODE
