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

# Initialize variables for argument parsing
PROJECT_PATH_OVERRIDE=""
PLATFORM_OVERRIDE=""
TASK_FILE_PATH_OVERRIDE=""
ADDITIONAL_CONTEXT_PATH_OVERRIDE=""
CONTINUATION_PROMPT_OVERRIDE=""
INITIAL_PROMPT_OVERRIDE=""
INACTIVITY_DELAY_OVERRIDE=""
AUTO="false"
DEBUG="false"
NO_SEND="false"

log "Raw arguments: $@"

# Process all arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform=*)
            PLATFORM_OVERRIDE="${1#*=}"
            log "Found --platform= format: $1"
            ;;
        --platform)
            shift
            PLATFORM_OVERRIDE="$1"
            log "Found --platform with value: $PLATFORM_OVERRIDE"
            ;;
        --project-path=*)
            PROJECT_PATH_OVERRIDE="${1#*=}"
            log "Found --project-path= format: $1"
            ;;
        --project-path)
            shift
            PROJECT_PATH_OVERRIDE="$1"
            log "Found --project-path with value: $PROJECT_PATH_OVERRIDE"
            ;;
        --task-file-path=*)
            TASK_FILE_PATH_OVERRIDE="${1#*=}"
            ;;
        --task-file-path)
            shift
            TASK_FILE_PATH_OVERRIDE="$1"
            ;;
        --additional-context-path=*)
            ADDITIONAL_CONTEXT_PATH_OVERRIDE="${1#*=}"
            ;;
        --additional-context-path)
            shift
            ADDITIONAL_CONTEXT_PATH_OVERRIDE="$1"
            ;;
        --continuation-prompt=*)
            CONTINUATION_PROMPT_OVERRIDE="${1#*=}"
            ;;
        --continuation-prompt)
            shift
            CONTINUATION_PROMPT_OVERRIDE="$1"
            ;;
        --initial-prompt=*)
            INITIAL_PROMPT_OVERRIDE="${1#*=}"
            ;;
        --initial-prompt)
            shift
            INITIAL_PROMPT_OVERRIDE="$1"
            ;;
        --inactivity-delay=*)
            INACTIVITY_DELAY_OVERRIDE="${1#*=}"
            ;;
        --inactivity-delay)
            shift
            INACTIVITY_DELAY_OVERRIDE="$1"
            ;;
        --auto)
            AUTO="true"
            ;;
        --debug)
            DEBUG="true"
            ;;
        --no-send)
            NO_SEND="true"
            ;;
        *)
            log "Unknown argument: $1"
            ;;
    esac
    shift
done

# Log all extracted values
log "Project path override: '$PROJECT_PATH_OVERRIDE'"
log "Platform override: '$PLATFORM_OVERRIDE'"
log "Task file path override: '$TASK_FILE_PATH_OVERRIDE'"
log "Additional context path override: '$ADDITIONAL_CONTEXT_PATH_OVERRIDE'"
log "Continuation prompt override: '$CONTINUATION_PROMPT_OVERRIDE'"
log "Initial prompt override: '$INITIAL_PROMPT_OVERRIDE'"
log "Inactivity delay override: '$INACTIVITY_DELAY_OVERRIDE'"
log "Auto mode: $AUTO"
log "Debug mode: $DEBUG"
log "No-send mode: $NO_SEND"

# Set default platform if not specified
if [[ -z "$PLATFORM_OVERRIDE" ]]; then
    log "No platform specified, defaulting to 'cursor'"
    PLATFORM_OVERRIDE="cursor"
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
    
    # Get platform type and config
    PLATFORM_TYPE=$(yq ".platforms.$platform.type" config.yaml)
    
    # Get project path - use override if provided, otherwise from config
    if [ -n "$PROJECT_PATH_OVERRIDE" ]; then
        PROJECT_PATH="$PROJECT_PATH_OVERRIDE"
        log "Using project path from command line: $PROJECT_PATH"
    else
        PROJECT_PATH=$(yq ".platforms.$platform.project_path" config.yaml)
        log "Using project path from config: $PROJECT_PATH"
    fi
    
    # Get task file path - use override if provided, otherwise from config
    if [ -n "$TASK_FILE_PATH_OVERRIDE" ]; then
        TASK_FILE="$TASK_FILE_PATH_OVERRIDE"
        log "Using task file from command line: $TASK_FILE"
    else
        TASK_FILE=$(yq -r ".platforms.$platform.task_file_path" config.yaml 2>/dev/null || echo "tasks.md")
        log "Using task file from config: $TASK_FILE"
    fi
    
    # Build the launch command
    LAUNCH_CMD="PYTHONPATH=. python3 -m src.watcher --platform $platform"
    
    # Add project path if available
    if [ -n "$PROJECT_PATH" ] && [ "$PROJECT_PATH" != "null" ]; then
        LAUNCH_CMD+=" --project-path \"$PROJECT_PATH\""
    fi
    
    # Add task file path if available
    if [ -n "$TASK_FILE" ] && [ "$TASK_FILE" != "null" ]; then
        LAUNCH_CMD+=" --task-file-path \"$TASK_FILE\""
    fi
    
    # Add initial prompt if provided
    if [ -n "$INITIAL_PROMPT_OVERRIDE" ]; then
        LAUNCH_CMD+=" --initial-prompt \"$INITIAL_PROMPT_OVERRIDE\""
    fi
    
    # Add continuation prompt if provided
    if [ -n "$CONTINUATION_PROMPT_OVERRIDE" ]; then
        LAUNCH_CMD+=" --continuation-prompt \"$CONTINUATION_PROMPT_OVERRIDE\""
    fi
    
    # Add debug flag if set
    if [ "$DEBUG" = "true" ]; then
        LAUNCH_CMD+=" --debug"
    fi
    
    log "Launching platform with command: $LAUNCH_CMD"
    
    # For Cursor, use our dedicated launcher script
    if [ "$platform" = "cursor" ]; then
        log "Launching Cursor using dedicated launcher..."
        
        # Export PYTHONPATH to include the project directory
        export PYTHONPATH="/Volumes/My Shared Files/Home/cheddar/cheddarwhizzy/cursor-autopilot:$PYTHONPATH"
        
        # Use the run_cursor.sh script to launch Cursor
        # Launch it but always consider it successful since it works in iTerm
        ./run_cursor.sh --platform cursor --project-path "$PROJECT_PATH" &
        log "Cursor launch initiated, assuming success"  
        platform_exit_code=0
    else
        # For other platforms, use the standard launcher
        log "Launching $platform using standard launcher..."
        eval $LAUNCH_CMD &
        platform_exit_code=$?
        
        # Store the PID
        PLATFORM_PID=$!
        log "Launched platform $platform with PID $PLATFORM_PID"
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

# Build command line arguments for the Python script
PYTHON_ARGS=()

# Add platform argument if specified
if [ -n "$PLATFORM_OVERRIDE" ]; then
    PYTHON_ARGS+=("--platform" "$PLATFORM_OVERRIDE")
fi

# Add project path argument if specified
if [ -n "$PROJECT_PATH_OVERRIDE" ]; then
    PYTHON_ARGS+=("--project-path" "$PROJECT_PATH_OVERRIDE")
fi

# Add task file path argument if specified
if [ -n "$TASK_FILE_PATH_OVERRIDE" ]; then
    PYTHON_ARGS+=("--task-file-path" "$TASK_FILE_PATH_OVERRIDE")
fi

# Add additional context path argument if specified
if [ -n "$ADDITIONAL_CONTEXT_PATH_OVERRIDE" ]; then
    PYTHON_ARGS+=("--additional-context-path" "$ADDITIONAL_CONTEXT_PATH_OVERRIDE")
fi

# Add continuation prompt argument if specified
if [ -n "$CONTINUATION_PROMPT_OVERRIDE" ]; then
    PYTHON_ARGS+=("--continuation-prompt" "$CONTINUATION_PROMPT_OVERRIDE")
fi

# Add initial prompt argument if specified
if [ -n "$INITIAL_PROMPT_OVERRIDE" ]; then
    PYTHON_ARGS+=("--initial-prompt" "$INITIAL_PROMPT_OVERRIDE")
fi

# Add inactivity delay argument if specified
if [ -n "$INACTIVITY_DELAY_OVERRIDE" ]; then
    PYTHON_ARGS+=("--inactivity-delay" "$INACTIVITY_DELAY_OVERRIDE")
fi

# Add debug flag if set
if [ "$DEBUG" = "true" ]; then
    PYTHON_ARGS+=("--debug")
fi

# Add no-send flag if set
if [ "$NO_SEND" = "true" ]; then
    PYTHON_ARGS+=("--no-send")
fi

# Add auto flag if set
if [ "$AUTO" = "true" ]; then
    PYTHON_ARGS+=("--auto")
fi

# Determine the Python entry point
PYTHON_ENTRY_POINT="src/watcher.py"

if [ ! -f "$PYTHON_ENTRY_POINT" ]; then
    # Fallback if watcher.py was deleted/renamed incorrectly
    if [ -f "watcher.py" ]; then
        PYTHON_ENTRY_POINT="watcher.py"
        log "Warning: $SCRIPT_DIR/src/watcher.py not found, falling back to $SCRIPT_DIR/watcher.py"
    else
        log "Running: python $PYTHON_ENTRY_POINT ${PYTHON_ARGS[*]}"
        python "$PYTHON_ENTRY_POINT" "${PYTHON_ARGS[@]}"
        exit 1
    fi
fi

# Pass all arguments, along with project path override if provided
log "Python execution section - Preparing to execute the Python script"
log "PROJECT_PATH_OVERRIDE='$PROJECT_PATH_OVERRIDE'"
log "Original arguments: $*"

# Build the command to execute
PYTHON_CMD="python3 -m src.watcher"

# Build the full command with proper array handling for spaces in paths
FULL_CMD="/opt/homebrew/bin/gtimeout 60s python3 -m src.watcher"

# Only add arguments if we have any
if [[ ${#PYTHON_ARGS[@]} -gt 0 ]]; then
    # Convert PYTHON_ARGS array to properly quoted string format that preserves spaces
    for arg in "${PYTHON_ARGS[@]}"; do
        FULL_CMD+="$(printf " %q" "$arg")"
    done
fi

log "Full command to execute: $FULL_CMD"

# Execute the command with a 60-second timeout
eval "$FULL_CMD" || {
    log "Command timed out after 60 seconds"
    exit 1
}

EXIT_CODE=$?
log "Python script finished with exit code $EXIT_CODE"

# Deactivate virtual environment
log "Deactivating virtual environment..."
deactivate

exit $EXIT_CODE
