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
    # Show the first few lines of the config file for debugging
    log "Config file (first 10 lines):"
    head -n 10 "$SCRIPT_DIR/config.yaml"
    
    # For cross-platform compatibility, check OS before launching app
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if grep -q "windsurf" "$SCRIPT_DIR/config.yaml"; then
            # Improved way to extract project path from config
            # First find the windsurf section
            PROJECT_PATH=""
            
            # Read the config file and extract the project path
            SECTION_FOUND=false
            while IFS= read -r line; do
                # Check if we're in the windsurf section
                if [[ "$line" =~ [[:space:]]+"windsurf":[[:space:]]* ]]; then
                    SECTION_FOUND=true
                    continue
                fi
                
                # Once in the windsurf section, look for project_path
                if [[ "$SECTION_FOUND" == "true" && "$line" =~ [[:space:]]+"project_path":[[:space:]]* ]]; then
                    # Extract the value after the colon
                    PROJECT_PATH=$(echo "$line" | sed 's/.*project_path:[[:space:]]*\(.*\)/\1/' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d "'" | tr -d '"')
                    break
                fi
            done < "$SCRIPT_DIR/config.yaml"
            
            # If project path not found yet, try with grep as fallback
            if [[ -z "$PROJECT_PATH" ]]; then
                log "Trying alternate method to find project path..."
                # Extract all platforms section
                PLATFORMS_SECTION=$(sed -n '/platforms:/,/general:/p' "$SCRIPT_DIR/config.yaml")
                
                # Extract windsurf section
                WINDSURF_SECTION=$(echo "$PLATFORMS_SECTION" | sed -n '/windsurf:/,/cursor:/p')
                if [[ -z "$WINDSURF_SECTION" ]]; then
                    # If cursor: not found after windsurf, try till end of platforms section
                    WINDSURF_SECTION=$(echo "$PLATFORMS_SECTION" | sed -n '/windsurf:/,/general:/p')
                fi
                
                # Extract project_path line
                PROJECT_PATH_LINE=$(echo "$WINDSURF_SECTION" | grep "project_path:")
                if [[ -n "$PROJECT_PATH_LINE" ]]; then
                    PROJECT_PATH=$(echo "$PROJECT_PATH_LINE" | sed 's/.*project_path:[[:space:]]*\(.*\)/\1/' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d "'" | tr -d '"')
                fi
            fi
            
            if [[ -n "$PROJECT_PATH" ]]; then
                log "Launching WindSurf with project path: $PROJECT_PATH"
                
                # Expand path if it contains ~ or other shell variables
                PROJECT_PATH=$(eval echo "$PROJECT_PATH")
                
                # Make sure path exists
                if [[ ! -d "$PROJECT_PATH" ]]; then
                    log "Warning: Project path does not exist: $PROJECT_PATH"
                    ls -la "$(dirname "$PROJECT_PATH")" || true
                else
                    # Try multiple app name variants
                    for APP_NAME in "WindSurf" "Windsurf" "windsurf"; do
                        log "Trying to launch $APP_NAME with path: $PROJECT_PATH"
                        # Kill any existing instances first (just to be sure)
                        killall -9 "$APP_NAME" 2>/dev/null || true
                        
                        # Try to launch the application
                        open -a "$APP_NAME" "$PROJECT_PATH" 2>/dev/null
                        if [[ $? -eq 0 ]]; then
                            log "Successfully launched $APP_NAME"
                            # Wait for the app to launch
                            sleep 3
                            
                            # Verify app is running
                            if pgrep -i "$APP_NAME" > /dev/null; then
                                log "$APP_NAME is running"
                                break
                            else
                                log "Warning: $APP_NAME failed to start"
                            fi
                        else
                            log "Failed to launch $APP_NAME"
                        fi
                    done
                    
                    # Double-check that application is running
                    if ! pgrep -i "[Ww]ind[Ss]urf" > /dev/null; then
                        log "Warning: WindSurf application did not start, trying direct AppleScript launch"
                        osascript -e "tell application \"WindSurf\" to open \"$PROJECT_PATH\"" || true
                        sleep 3
                    fi
                    
                    # Output project directory contents count for debugging
                    if [[ -d "$PROJECT_PATH" ]]; then
                        FILE_COUNT=$(find "$PROJECT_PATH" -type f | wc -l)
                        DIR_COUNT=$(find "$PROJECT_PATH" -type d | wc -l)
                        log "Project directory contains $FILE_COUNT files and $DIR_COUNT directories"
                        log "Project directory contents (first level):"
                        ls -la "$PROJECT_PATH" | head -n 20
                    fi
                fi
            else
                log "Warning: Could not find project_path for WindSurf in config.yaml"
                # Print config file for debugging
                log "Config file contents:"
                cat "$SCRIPT_DIR/config.yaml" | grep -A 20 "windsurf:"
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
