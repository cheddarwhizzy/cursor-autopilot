#!/bin/bash

# Exit on error
set -e

# Cleanup function to kill watcher processes on Ctrl+C
cleanup() {
    echo "Caught interrupt. Killing any running watcher processes..."
    pkill -f "python3 -m src.watcher" || true
    exit 1
}

trap cleanup SIGINT

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
RUN_API="false"

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
        --api)
            RUN_API="true"
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
log "Run API server: $RUN_API"

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

# The watcher will handle platform launching, so we skip the separate launch phase

# --- Start the watcher to handle platform launching, prompts and monitoring ---
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
if [ "$RUN_API" = "true" ]; then
    PYTHON_ENTRY_POINT="src/run_both.py"
    log "API mode enabled - will start both watcher and configuration API server"
else
    PYTHON_ENTRY_POINT="src/watcher.py"
    log "Watcher-only mode - will start file watcher only"
fi

if [ ! -f "$PYTHON_ENTRY_POINT" ]; then
    log "Error: Python entry point not found: $PYTHON_ENTRY_POINT"
    exit 1
fi

# Pass all arguments, along with project path override if provided
log "Python execution section - Preparing to execute the Python script"
log "PROJECT_PATH_OVERRIDE='$PROJECT_PATH_OVERRIDE'"
log "Original arguments: $*"

# Build the command to execute
if [ "$RUN_API" = "true" ]; then
    # When running both API and watcher, use run_both.py and pass arguments
    FULL_CMD="python3 src/run_both.py"
    
    # Add arguments if we have any (run_both.py will forward them to the watcher)
    if [[ ${#PYTHON_ARGS[@]} -gt 0 ]]; then
        # Convert PYTHON_ARGS array to properly quoted string format that preserves spaces
        for arg in "${PYTHON_ARGS[@]}"; do
            FULL_CMD+="$(printf " %q" "$arg")"
        done
    fi
    log "Running both API server and watcher..."
else
    # When running watcher only, use the module approach with arguments
    FULL_CMD="python3 -m src.watcher"
    
    # Only add arguments if we have any
    if [[ ${#PYTHON_ARGS[@]} -gt 0 ]]; then
        # Convert PYTHON_ARGS array to properly quoted string format that preserves spaces
        for arg in "${PYTHON_ARGS[@]}"; do
            FULL_CMD+="$(printf " %q" "$arg")"
        done
    fi
    log "Running watcher only..."
fi

log "Full command to execute: $FULL_CMD"

# Create logs directory if it doesn't exist
mkdir -p logs

# Generate log filename with timestamp
LOG_FILE="logs/autopilot_$(date '+%Y%m%d_%H%M%S').log"

log "Logging output to: $LOG_FILE"

# Execute the command without timeout (watcher runs indefinitely)
# Use tee to write to both stdout and log file
# Note: When running in API mode (--api flag), countdown messages are prefixed with "WATCHER |"
# To see only countdown messages, you can use: tail -f logs/autopilot_*.log | grep "countdown"
eval "$FULL_CMD" 2>&1 | tee "$LOG_FILE" || {
    log "Watcher process failed"
    exit 1
}

EXIT_CODE=$?
log "Python script finished with exit code $EXIT_CODE"

# Deactivate virtual environment
log "Deactivating virtual environment..."
deactivate

exit $EXIT_CODE
