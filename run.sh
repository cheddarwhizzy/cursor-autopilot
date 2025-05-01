#!/bin/bash

# Exit on error
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Get the directory of the script
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd "$SCRIPT_DIR" || exit 1

log "Script directory: $SCRIPT_DIR"

# Kill applications at startup (added)
log "Terminating applications before restart..."
# Try multiple app names and methods
killall -9 WindSurf 2>/dev/null || true
killall -9 Windsurf 2>/dev/null || true
killall -9 windsurf 2>/dev/null || true
# Try with osascript quit (graceful)
osascript -e 'tell application "WindSurf" to quit' 2>/dev/null || true
# Wait a moment
sleep 2
log "Application termination attempts completed"

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
# Optionally add pyautogui here if needed for cross-platform
# pip install pyautogui -q 

# Launch the application based on config.yaml
if [[ -f "$SCRIPT_DIR/config.yaml" ]]; then
    log "Loading platform information from config.yaml..."
    
    # For cross-platform compatibility, check OS before launching app
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if grep -q "windsurf" "$SCRIPT_DIR/config.yaml"; then
            # Extract project path from config
            PROJECT_PATH=$(grep -A 3 "project_path" "$SCRIPT_DIR/config.yaml" | grep -v "project_path:" | head -n 1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d "'" | tr -d '"' | cut -d: -f2 | sed 's/^[[:space:]]*//')
            
            if [[ -n "$PROJECT_PATH" ]]; then
                log "Launching WindSurf with project path: $PROJECT_PATH"
                # Try to launch the application
                open -a "WindSurf" "$PROJECT_PATH" &
                # Wait for the app to launch
                sleep 3
            else
                log "Warning: Could not find project_path for WindSurf in config.yaml"
            fi
        fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows handling would go here
        log "Windows launching not implemented yet"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux handling would go here
        log "Linux launching not implemented yet"
    fi
fi

log "Starting Cursor Autopilot..."

# --- Execute Python Entry Point --- 
# The Python script (e.g., src/cli.py or src/watcher.py) is now responsible 
# for loading config.yaml, parsing CLI args with argparse, and overriding.

# Determine the Python entry point - Assuming it's src/watcher.py based on previous edits
# If you created a dedicated cli.py, change this.
PYTHON_ENTRY_POINT="src/watcher.py" 
# PYTHON_ENTRY_POINT="src/cli.py" # <<< --- Use this if you have a separate cli entrypoint

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

log "Executing: python3 -m src.watcher $*"
# Execute as a module to fix import paths
python3 -m src.watcher $*

EXIT_CODE=$?
log "Python script finished with exit code $EXIT_CODE"

# Deactivate virtual environment
log "Deactivating virtual environment..."
deactivate

exit $EXIT_CODE
