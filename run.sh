#!/bin/bash

# Check if pyenv is installed
if ! command -v pyenv >/dev/null 2>&1; then
    echo "pyenv is required but not found."
    echo "Would you like to install it now with 'brew install pyenv'?"
    read -p "Press [Enter] to install or Ctrl+C to cancel..."
    if command -v brew >/dev/null 2>&1; then
        brew install pyenv
        if ! command -v pyenv >/dev/null 2>&1; then
            echo "pyenv installation failed. Please install it manually and re-run this script."
            exit 1
        fi
    else
        echo "Homebrew is not installed. Please install Homebrew first: https://brew.sh/"
        exit 1
    fi
fi

# Set Python version using pyenv
echo "Setting Python version to 3.13.2..."
pyenv local 3.13.2

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Verify Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
if [[ ! "$PYTHON_VERSION" =~ ^3\.13\. ]]; then
    echo "Error: Virtual environment is not using Python 3.13+ (current version: $PYTHON_VERSION)"
    echo "Please delete the venv directory and run this script again"
    exit 1
fi

# Install required packages
echo "Installing required Python packages..."
pip install -r requirements.txt 2>&1 > /dev/null

# Check for tesseract-ocr (needed for pytesseract)
if ! command -v tesseract >/dev/null 2>&1; then
  echo "Warning: tesseract-ocr is not installed. Please install it with 'brew install tesseract' for OCR support."
fi

# === CONFIGURATION ===
# Extract PROJECT_PATH and PLATFORM from config.json
export CONFIG_FILE="$(dirname "$0")/config.json"
if [ -f "$CONFIG_FILE" ]; then
  CONFIG_VALUES=$(python3 -c 'import json,os; c=json.load(open(os.environ["CONFIG_FILE"])); print(os.path.expanduser(c["project_path"]) + "\t" + c["platform"])' CONFIG_FILE="$CONFIG_FILE")
  PROJECT_PATH=$(echo "$CONFIG_VALUES" | cut -f1)
  PLATFORM=$(echo "$CONFIG_VALUES" | cut -f2)
else
  echo "Error: config.json not found. Set CONFIG_FILE environment variable to the path of your config.json file."
  exit 1
fi

# The initial prompt is now stored in initial_prompt.txt

# Default values
AUTO_MODE=0
DEBUG_MODE=0
JSON_MODE=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto)
            AUTO_MODE=1
            shift
            ;;
        --debug)
            DEBUG_MODE=1
            shift
            ;;
        --json)
            JSON_MODE=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set environment variables
export CURSOR_AUTOPILOT_AUTO=$AUTO_MODE
export CURSOR_AUTOPILOT_DEBUG=$DEBUG_MODE
export CURSOR_AUTOPILOT_JSON=$JSON_MODE

# Ensure config.json exists and has required fields
if [ ! -f "config.json" ]; then
    echo "Creating default config.json..."
    cat > config.json << EOF
{
  "project_path": "$(pwd)",
  "task_file_path": "tasks.md",
  "additional_context_path": "context.md",
  "initial_delay": 10,
  "send_message": true,
  "platform": "cursor",
  "use_vision_api": false,
  "debug": $DEBUG_MODE,
  "inactivity_delay": 120
}
EOF
fi

# Update config.json with current settings
python3 -c "
import json
with open('config.json', 'r') as f:
    config = json.load(f)
config['debug'] = $DEBUG_MODE
config['inactivity_delay'] = 120
with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)
"

# === STEP 1: KILL EXISTING APPLICATION IF RUNNING ===
if [ "$PLATFORM" = "windsurf" ]; then
  pkill -f "Windsurf" || true
  APP_NAME="Windsurf"
else
  pkill -f "Cursor" || true
  APP_NAME="Cursor"
fi

# === STEP 2: OPEN FOLDER IN APPROPRIATE APPLICATION ===
open -a "$APP_NAME" "$PROJECT_PATH"

python3 generate_initial_prompt.py

# Ensure chat window is open using OpenAI Vision
python3 ensure_chat_window.py "$PLATFORM"

# Send the initial prompt immediately after opening the chat window, starting a new chat
if [ -f "initial_prompt.txt" ]; then
  python3 -c 'import json,os; from actions.send_to_cursor import send_prompt; config=json.load(open(os.environ["CONFIG_FILE"])); send_prompt(open("initial_prompt.txt").read().strip(), platform=config.get("platform", "cursor"), new_chat=True, send_message=config.get("send_message", True))'
fi

# Start Slack bot and watcher together with combined logs
echo "Starting Slack bot and Cursor watcher... (auto mode: $AUTO_MODE, send messages: true)"
python3 run_both.py
