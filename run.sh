#!/bin/bash

# Exit on error
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a process is running
is_process_running() {
    pgrep -f "$1" >/dev/null
}

# Function to kill existing processes
kill_existing_processes() {
    if [ "$CURSOR_AUTOPILOT_NO_KILL_EXISTING" != "true" ]; then
        log "Checking for existing processes..."
        if is_process_running "python.*cursor-autopilot"; then
            log "Killing existing processes..."
            pkill -f "python.*cursor-autopilot"
            sleep 2
        fi
    fi
}

# Function to start a platform
start_platform() {
    local platform=$1
    local project_path=$2
    
    case "$platform" in
        "cursor")
            log "Starting Cursor..."
            # Check if application is already running
            if ! pgrep -x "Cursor" > /dev/null; then
                # Different ways to attempt opening the app
                if [ -d "/Applications/Cursor.app" ]; then
                    open -a "Cursor" "$project_path"
                elif [ -d "/Applications/cursor.app" ]; then
                    open -a "cursor" "$project_path"
                else
                    # Try different variations
                    open -a "Cursor" "$project_path" 2>/dev/null || \
                    open -a "cursor" "$project_path" 2>/dev/null || \
                    open "$project_path"
                fi
            else
                log "Cursor is already running, activating..."
                osascript -e 'tell application "Cursor" to activate'
            fi
            ;;
        "windsurf")
            log "Starting Windsurf..."
            # Check if application is already running
            if ! pgrep -x "Windsurf" > /dev/null && ! pgrep -x "WindSurf" > /dev/null; then
                # Different ways to attempt opening the app
                if [ -d "/Applications/Windsurf.app" ]; then
                    open -a "Windsurf" "$project_path"
                elif [ -d "/Applications/WindSurf.app" ]; then
                    open -a "WindSurf" "$project_path"
                else
                    # Try different variations
                    open -a "Windsurf" "$project_path" 2>/dev/null || \
                    open -a "WindSurf" "$project_path" 2>/dev/null || \
                    open -a "windsurf" "$project_path" 2>/dev/null || \
                    open "$project_path"
                fi
            else
                log "Windsurf is already running, activating..."
                osascript -e 'tell application "Windsurf" to activate' 2>/dev/null || \
                osascript -e 'tell application "WindSurf" to activate' 2>/dev/null
            fi
            ;;
        *)
            log "Error: Unknown platform: $platform"
            exit 1
            ;;
    esac
}

# Check for required commands
for cmd in python3 pip pyenv; do
    if ! command_exists "$cmd"; then
        log "Error: $cmd is required but not installed"
        exit 1
    fi
done

# Check if pyenv is installed
if ! command_exists pyenv; then
    log "Error: pyenv is required but not installed"
    exit 1
fi

# Set Python version
PYTHON_VERSION="3.11.0"
log "Setting Python version to $PYTHON_VERSION..."
pyenv install -s "$PYTHON_VERSION"
pyenv global "$PYTHON_VERSION"

# Create and activate virtual environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

log "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install required packages
log "Installing required packages..."
pip install -r requirements.txt -q

# Install additional packages that might be missing
log "Installing additional dependencies..."
pip install pyautogui pyyaml openai requests -q

# Load configuration
log "Loading configuration..."
python3 -m src.cli "$@"
if [ $? -ne 0 ]; then
    log "Error: Failed to load configuration"
    exit 1
fi

# Debug logging for environment variables
if [ "$CURSOR_AUTOPILOT_DEBUG" = "true" ]; then
    log "DEBUG: Environment variables after CLI:"
    log "DEBUG: CURSOR_AUTOPILOT_PLATFORM='$CURSOR_AUTOPILOT_PLATFORM'"
    log "DEBUG: CURSOR_AUTOPILOT_PROJECT_PATH='$CURSOR_AUTOPILOT_PROJECT_PATH'"
    log "DEBUG: CURSOR_AUTOPILOT_INACTIVITY_DELAY='$CURSOR_AUTOPILOT_INACTIVITY_DELAY'"
    log "DEBUG: CURSOR_AUTOPILOT_DEBUG='$CURSOR_AUTOPILOT_DEBUG'"
fi

# Check if project path is set
if [ -z "$CURSOR_AUTOPILOT_PROJECT_PATH" ]; then
    log "Error: Project path not set"
    # Add fallback for CLI argument
    for arg in "$@"; do
        if [[ $arg == --project-path=* ]]; then
            CURSOR_AUTOPILOT_PROJECT_PATH="${arg#*=}"
            log "Using project path from CLI argument: $CURSOR_AUTOPILOT_PROJECT_PATH"
            break
        elif [[ $prev_arg == "--project-path" ]]; then
            CURSOR_AUTOPILOT_PROJECT_PATH="$arg"
            log "Using project path from CLI argument: $CURSOR_AUTOPILOT_PROJECT_PATH"
            break
        fi
        prev_arg="$arg"
    done
    
    # Still not set?
    if [ -z "$CURSOR_AUTOPILOT_PROJECT_PATH" ]; then
        exit 1
    fi
fi

# Check if platform is set
if [ -z "$CURSOR_AUTOPILOT_PLATFORM" ]; then
    log "Error: Platform not set"
    # Add fallback for CLI argument
    for arg in "$@"; do
        if [[ $arg == --platform=* ]]; then
            CURSOR_AUTOPILOT_PLATFORM="${arg#*=}"
            log "Using platform from CLI argument: $CURSOR_AUTOPILOT_PLATFORM"
            break
        elif [[ $prev_arg == "--platform" ]]; then
            CURSOR_AUTOPILOT_PLATFORM="$arg"
            log "Using platform from CLI argument: $CURSOR_AUTOPILOT_PLATFORM"
            break
        fi
        prev_arg="$arg"
    done
    
    # Still not set?
    if [ -z "$CURSOR_AUTOPILOT_PLATFORM" ]; then
        exit 1
    fi
fi

# Set environment variables if needed
if [ -z "$CURSOR_AUTOPILOT_INACTIVITY_DELAY" ]; then
    CURSOR_AUTOPILOT_INACTIVITY_DELAY=125
fi

if [ "$CURSOR_AUTOPILOT_DEBUG" != "true" ]; then
    CURSOR_AUTOPILOT_DEBUG=true
fi

# Fix variables to export for main script
export CURSOR_AUTOPILOT_PROJECT_PATH
export CURSOR_AUTOPILOT_PLATFORM
export CURSOR_AUTOPILOT_INACTIVITY_DELAY
export CURSOR_AUTOPILOT_DEBUG

# Kill existing processes
kill_existing_processes

# Start each platform
IFS=',' read -ra PLATFORMS <<< "$CURSOR_AUTOPILOT_PLATFORM"
for platform in "${PLATFORMS[@]}"; do
    log "Starting platform: $platform with project path: $CURSOR_AUTOPILOT_PROJECT_PATH"
    start_platform "$platform" "$CURSOR_AUTOPILOT_PROJECT_PATH"
done

# Start the watcher script
log "Starting watcher script..."
# Debug environment variables
log "Environment variables for watcher:"
log "CURSOR_AUTOPILOT_PLATFORM=$CURSOR_AUTOPILOT_PLATFORM"
log "CURSOR_AUTOPILOT_PROJECT_PATH=$CURSOR_AUTOPILOT_PROJECT_PATH"
log "CURSOR_AUTOPILOT_INACTIVITY_DELAY=$CURSOR_AUTOPILOT_INACTIVITY_DELAY"
log "CURSOR_AUTOPILOT_DEBUG=$CURSOR_AUTOPILOT_DEBUG"

# Use existing config.yaml as base
CONFIG_FILE="config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    log "Warning: $CONFIG_FILE not found. Creating a minimal config file."
    # Create a minimal config file
    cat > "$CONFIG_FILE" << EOL
platforms:
  windsurf:
    os_type: osx
    window_title: WindSurf
    project_path: $CURSOR_AUTOPILOT_PROJECT_PATH
    initialization:
      - keys: "command+l"
        delay_ms: 100
    options:
      inactivity_prompt: "Continue working on the task. Here's what I've done so far..."
      
inactivity_delay: $CURSOR_AUTOPILOT_INACTIVITY_DELAY
debug: $CURSOR_AUTOPILOT_DEBUG
EOL
else
    log "Using existing $CONFIG_FILE as base configuration"
fi

# Run the watcher script with command line arguments as overrides
cd "$(dirname "$0")"
log "Running watcher script from $(pwd)..."

CLI_ARGS=""
if [ -n "$CURSOR_AUTOPILOT_PLATFORM" ]; then
    CLI_ARGS="$CLI_ARGS --platform $CURSOR_AUTOPILOT_PLATFORM"
fi
if [ -n "$CURSOR_AUTOPILOT_PROJECT_PATH" ]; then
    CLI_ARGS="$CLI_ARGS --project-path $CURSOR_AUTOPILOT_PROJECT_PATH"
fi
if [ -n "$CURSOR_AUTOPILOT_INACTIVITY_DELAY" ]; then
    CLI_ARGS="$CLI_ARGS --inactivity-delay $CURSOR_AUTOPILOT_INACTIVITY_DELAY"
fi
if [ "$CURSOR_AUTOPILOT_DEBUG" = "true" ]; then
    CLI_ARGS="$CLI_ARGS --debug"
fi

log "Running with CLI arguments: $CLI_ARGS"
if python3 -m src.cli $CLI_ARGS; then
    if python3 -m src.watcher; then
        log "Watcher script completed successfully"
    else
        error_code=$?
        log "Error: Watcher script failed with exit code $error_code"
        exit $error_code
    fi
else
    error_code=$?
    log "Error: CLI script failed with exit code $error_code"
    exit $error_code
fi

# Deactivate virtual environment
log "Deactivating virtual environment..."
deactivate
