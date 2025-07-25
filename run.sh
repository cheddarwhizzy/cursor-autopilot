#!/bin/bash

# Exit on error
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

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

# Get the directory of the script
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd "$SCRIPT_DIR" || exit 1

log "Script directory: $SCRIPT_DIR"

# --- Moved Termination Block Here ---
log "Terminating relevant applications before restart..."

# Check if windsurf is one of the platforms to run
if [[ " $platform_to_run " =~ " windsurf " ]]; then
    log "Terminating WindSurf (platform 'windsurf' is active)..."
    # Try multiple app names and methods
    killall -9 WindSurf 2>/dev/null || true
    killall -9 Windsurf 2>/dev/null || true
    killall -9 windsurf 2>/dev/null || true
    # Try with osascript quit (graceful)
    osascript -e 'tell application "WindSurf" to quit' 2>/dev/null || true
    # Wait a moment
    sleep 2
else
    log "Skipping WindSurf termination (platform 'windsurf' is not active)"
fi

# Check if cursor is one of the platforms to run
if [[ " $platform_to_run " =~ " cursor " ]]; then
    log "Terminating Cursor (platform 'cursor' is active)..."
    # Add commands to terminate Cursor here if needed
    # Example using killall:
    killall -9 Cursor 2>/dev/null || true
    # Example using osascript:
    osascript -e 'tell application "Cursor" to quit' 2>/dev/null || true
    sleep 2 # Wait for Cursor to close
    # log "(Cursor termination commands currently commented out)"
else
     log "Skipping Cursor termination (platform 'cursor' is not active)"
fi

log "Application termination attempts completed"
# --- End Moved Termination Block ---

# --- Launch Application Block ---
log "Launching applications based on active platforms..."

# Check if windsurf is one of the platforms to run
if [[ " $platform_to_run " =~ " windsurf " ]]; then
    log "Launching WindSurf (platform 'windsurf' is active)..."
    if [[ -n "$PROJECT_PATH_OVERRIDE" ]]; then
        # Launch WindSurf with project path
        log "Launching WindSurf with project path: '$PROJECT_PATH_OVERRIDE'"
        
        # Method 1: Using open command
        open -a WindSurf "$PROJECT_PATH_OVERRIDE" || true
        
        # Wait a moment for the app to launch
        sleep 3
        
        # Check if WindSurf is running
        if pgrep -i "[Ww]ind[Ss]urf" > /dev/null; then
            log "WindSurf started successfully with open command"
        else
            # Method 2: Try with AppleScript if open command failed
            log "Trying to launch WindSurf with AppleScript..."
            PROJECT_PATH_ESCAPED="${PROJECT_PATH_OVERRIDE//\"/\\\"}"
            APPLESCRIPT="tell application \"WindSurf\" to open \"$PROJECT_PATH_ESCAPED\""
            log "Running AppleScript: $APPLESCRIPT"
            osascript -e "$APPLESCRIPT" || true
            sleep 3
            
            # Check one more time
            if pgrep -i "[Ww]ind[Ss]urf" > /dev/null; then
                log "WindSurf started successfully with AppleScript"
            else
                log "Warning: Failed to start WindSurf with both methods"
            fi
        fi
    else
        log "Warning: No project path provided for WindSurf"
        open -a WindSurf || true
    fi
else
    log "Skipping WindSurf launch (platform 'windsurf' is not active)"
fi

# Check if cursor is one of the platforms to run
if [[ " $platform_to_run " =~ " cursor " ]]; then
    log "Launching Cursor (platform 'cursor' is active)..."
    if [[ -n "$PROJECT_PATH_OVERRIDE" ]]; then
        # Launch Cursor with project path
        log "Launching Cursor with project path: '$PROJECT_PATH_OVERRIDE'"
        
        # Method 1: Using open command
        open -a Cursor "$PROJECT_PATH_OVERRIDE" || true
        
        # Wait a moment for the app to launch
        sleep 3
        
        # Check if Cursor is running
        if pgrep -i "Cursor" > /dev/null; then
            log "Cursor started successfully with open command"
        else
            # Method 2: Try with AppleScript if open command failed
            log "Trying to launch Cursor with AppleScript..."
            PROJECT_PATH_ESCAPED="${PROJECT_PATH_OVERRIDE//\"/\\\"}"
            APPLESCRIPT="tell application \"Cursor\" to open \"$PROJECT_PATH_ESCAPED\""
            log "Running AppleScript: $APPLESCRIPT"
            osascript -e "$APPLESCRIPT" || true
            sleep 3
            
            # Check one more time
            if pgrep -i "Cursor" > /dev/null; then
                log "Cursor started successfully with AppleScript"
            else
                log "Warning: Failed to start Cursor with both methods"
            fi
        fi
    else
        log "Warning: No project path provided for Cursor"
        open -a Cursor || true
    fi
else
    log "Skipping Cursor launch (platform 'cursor' is not active)"
fi

log "Application launch attempts completed"
# --- End Launch Application Block ---

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
# if [[ -f "$SCRIPT_DIR/config.yaml" ]]; then
#     log "Loading platform information from config.yaml..."
#     # Show the first few lines of the config file for debugging
#     log "Config file (first 10 lines):"
#     head -n 10 "$SCRIPT_DIR/config.yaml"
    
#     # For cross-platform compatibility, check OS before launching app
#     if [[ "$OSTYPE" == "darwin"* ]]; then
#         # macOS
#         if grep -q "windsurf" "$SCRIPT_DIR/config.yaml"; then
#             # Prioritize command line project path override over config
#             log "About to decide which project path to use for launch"
#             log "PROJECT_PATH_OVERRIDE='$PROJECT_PATH_OVERRIDE'"
            
#             if [[ -n "$PROJECT_PATH_OVERRIDE" ]]; then
#                 PROJECT_PATH="$PROJECT_PATH_OVERRIDE"
#                 log "Using command line project path override: '$PROJECT_PATH'"
#             else
#                 # Improved way to extract project path from config
#                 # First find the windsurf section
#                 CONFIG_PROJECT_PATH=""
                
#                 # Read the config file and extract the project path
#                 SECTION_FOUND=false
#                 while IFS= read -r line; do
#                     # Check if we're in the windsurf section
#                     if [[ "$line" =~ [[:space:]]+"windsurf":[[:space:]]* ]]; then
#                         SECTION_FOUND=true
#                         log "Found windsurf section in config.yaml"
#                         continue
#                     fi
                    
#                     # Once in the windsurf section, look for project_path
#                     if [[ "$SECTION_FOUND" == "true" && "$line" =~ [[:space:]]+"project_path":[[:space:]]* ]]; then
#                         # Extract the value after the colon
#                         CONFIG_PROJECT_PATH=$(echo "$line" | sed 's/.*project_path:[[:space:]]*\(.*\)/\1/' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d "'" | tr -d '"')
#                         log "Extracted project_path from config.yaml: '$CONFIG_PROJECT_PATH'"
#                         break
#                     fi
#                 done < "$SCRIPT_DIR/config.yaml"
                
#                 # If project path not found yet, try with grep as fallback
#                 if [[ -z "$CONFIG_PROJECT_PATH" ]]; then
#                     log "Trying alternate method to find project path..."
#                     # Extract all platforms section
#                     PLATFORMS_SECTION=$(sed -n '/platforms:/,/general:/p' "$SCRIPT_DIR/config.yaml")
                    
#                     # Extract windsurf section
#                     WINDSURF_SECTION=$(echo "$PLATFORMS_SECTION" | sed -n '/windsurf:/,/cursor:/p')
#                     if [[ -z "$WINDSURF_SECTION" ]]; then
#                         # If cursor: not found after windsurf, try till end of platforms section
#                         WINDSURF_SECTION=$(echo "$PLATFORMS_SECTION" | sed -n '/windsurf:/,/general:/p')
#                     fi
                    
#                     # Extract project_path line
#                     PROJECT_PATH_LINE=$(echo "$WINDSURF_SECTION" | grep "project_path:")
#                     if [[ -n "$PROJECT_PATH_LINE" ]]; then
#                         CONFIG_PROJECT_PATH=$(echo "$PROJECT_PATH_LINE" | sed 's/.*project_path:[[:space:]]*\(.*\)/\1/' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d "'" | tr -d '"')
#                         log "Extracted project_path with grep method: '$CONFIG_PROJECT_PATH'"
#                     fi
#                 fi
                
#                 PROJECT_PATH="$CONFIG_PROJECT_PATH"
#                 log "Using config file project path: '$PROJECT_PATH'"
#             fi
            
#             if [[ -n "$PROJECT_PATH" ]]; then
#                 log "Launching WindSurf with project path: '$PROJECT_PATH'"
                
#                 # Expand path if it contains ~ or other shell variables
#                 UNEXPANDED_PATH="$PROJECT_PATH"
#                 PROJECT_PATH=$(eval echo "$PROJECT_PATH")
#                 if [[ "$UNEXPANDED_PATH" != "$PROJECT_PATH" ]]; then
#                     log "Expanded project path: '$UNEXPANDED_PATH' -> '$PROJECT_PATH'"
#                 fi
                
#                 # Make sure path exists
#                 if [[ ! -d "$PROJECT_PATH" ]]; then
#                     log "Warning: Project path does not exist: '$PROJECT_PATH'"
#                     log "Parent directory contents:"
#                     ls -la "$(dirname "$PROJECT_PATH")" || true
#                 else
#                     # Log the project path for debugging
#                     log "Project path for WindSurf: '$PROJECT_PATH' (exists: $(test -d "$PROJECT_PATH" && echo Yes || echo No))"
#                     log "Project path dir listing:"
#                     ls -la "$PROJECT_PATH" | head -10 || true
                    
#                     # Determine the platform to run
#                     platform_to_run=""
#                     if [[ -n "$PLATFORM_OVERRIDE" ]]; then
#                         platform_to_run="$PLATFORM_OVERRIDE"
#                         log "Using platform specified via --platform: $platform_to_run"
#                     else
#                         # Read the first active platform from config.yaml if CLI platform not specified
#                         platform_to_run=$(yq e '.platforms.active_platforms[0]' "$SCRIPT_DIR/config.yaml")
#                         # Check if yq returned null or empty string
#                         if [ -z "$platform_to_run" ] || [ "$platform_to_run" == "null" ]; then
#                             echo "Error: No active platforms specified in config.yaml and --platform not provided." >&2
#                             exit 1
#                         fi
#                         log "No --platform specified, using the first active platform from config: $platform_to_run"
#                     fi
                    
#                     # Kill existing WindSurf instances to ensure clean launch
#                     log "Terminating any existing WindSurf instances..."
#                     killall -9 WindSurf 2>/dev/null || true
#                     sleep 1
                    
#                     # Try multiple app name variants
#                     for APP_NAME in "WindSurf" "Windsurf" "windsurf"; do
#                         log "Trying to launch $APP_NAME with path: '$PROJECT_PATH'"
                        
#                         # Try to launch the application with explicit project path
#                         OPEN_CMD="open -a \"$APP_NAME\" \"$PROJECT_PATH\""
#                         log "Running command: $OPEN_CMD"
#                         open -a "$APP_NAME" "$PROJECT_PATH" 2>/dev/null
#                         OPEN_RESULT=$?
                        
#                         if [[ $OPEN_RESULT -eq 0 ]]; then
#                             log "Successfully launched $APP_NAME with open command"
#                             # Wait for the app to launch
#                             sleep 3
                            
#                             # Verify app is running
#                             if pgrep -i "$APP_NAME" > /dev/null; then
#                                 log "$APP_NAME is running"
#                                 break
#                             else
#                                 log "Warning: $APP_NAME failed to start despite successful open command"
#                             fi
#                         else
#                             log "Failed to launch $APP_NAME with open command (exit code: $OPEN_RESULT)"
#                         fi
#                     done
                    
#                     # Double-check that application is running
#                     if ! pgrep -i "[Ww]ind[Ss]urf" > /dev/null; then
#                         log "Warning: WindSurf application did not start with open command, trying direct AppleScript launch"
                        
#                         # Try with AppleScript as fallback (be specific about path)
#                         PROJECT_PATH_ESCAPED="${PROJECT_PATH//\"/\\\"}"
#                         APPLESCRIPT="tell application \"WindSurf\" to open \"$PROJECT_PATH_ESCAPED\""
#                         log "Running AppleScript: $APPLESCRIPT"
#                         osascript -e "$APPLESCRIPT" || true
#                         sleep 3
                        
#                         # Check one more time
#                         if pgrep -i "[Ww]ind[Ss]urf" > /dev/null; then
#                             log "WindSurf started successfully with AppleScript"
#                         else
#                             log "Warning: Failed to start WindSurf with both methods"
#                         fi
#                     fi
                    
#                     # Output project directory contents count for debugging
#                     if [[ -d "$PROJECT_PATH" ]]; then
#                         FILE_COUNT=$(find "$PROJECT_PATH" -type f | wc -l)
#                         DIR_COUNT=$(find "$PROJECT_PATH" -type d | wc -l)
#                         log "Project directory contains $FILE_COUNT files and $DIR_COUNT directories"
#                         log "Project directory contents (first level):"
#                         ls -la "$PROJECT_PATH" | head -n 20
#                     fi
#                 fi
#             else
#                 log "Warning: Could not find project_path for WindSurf in config.yaml"
#                 # Print config file for debugging
#                 log "Config file contents:"
#                 cat "$SCRIPT_DIR/config.yaml" | grep -A 20 "windsurf:"
#             fi
#         fi
#     elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
#         # Windows handling would go here
#         log "Windows launching not implemented yet"
#     elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
#         # Linux handling would go here
#         log "Linux launching not implemented yet"
#     fi
# fi

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
