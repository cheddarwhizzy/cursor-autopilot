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
# Extract PROJECT_PATH and PLATFORM from config.yaml
export CONFIG_FILE="$(dirname "$0")/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
  CONFIG_VALUES=$(python3 -c 'import yaml,os; c=yaml.safe_load(open(os.environ["CONFIG_FILE"])); p=c["platforms"][list(c["platforms"].keys())[0]]; print(os.path.expanduser(p["project_path"]) + "\t" + list(c["platforms"].keys())[0])' CONFIG_FILE="$CONFIG_FILE")
  PROJECT_PATH=$(echo "$CONFIG_VALUES" | cut -f1)
  PLATFORM=$(echo "$CONFIG_VALUES" | cut -f2)
else
  echo "Error: config.yaml not found. Set CONFIG_FILE environment variable to the path of your config.yaml file."
  exit 1
fi

# The initial prompt is now stored in initial_prompt.txt

# Parse flags for auto mode and send message behavior
auto_mode=0
send_message=true
debug_mode=false

for arg in "$@"; do
  case $arg in
    --auto)
      auto_mode=1
      ;;
    --no-auto)
      auto_mode=0
      ;;
    --no-send)
      send_message=false
      ;;
    --send)
      send_message=true
      ;;
    --debug)
      debug_mode=true
      ;;
  esac
done

export CURSOR_AUTOPILOT_AUTO_MODE=$auto_mode
export CURSOR_AUTOPILOT_DEBUG=$debug_mode

# Update send_message in config.yaml only if PLATFORM is set
if [ -n "$PLATFORM" ]; then
python3 -c '
import yaml
import os
config_file = os.environ["CONFIG_FILE"]
platform = os.environ["PLATFORM"]
with open(config_file, "r") as f:
    config = yaml.safe_load(f)
config["platforms"][platform]["options"]["enable_auto_mode"] = True if "'$send_message'" == "true" else False
config["platforms"][platform]["options"]["debug"] = True if "'$debug_mode'" == "true" else False
config["platforms"][platform]["options"]["inactivity_delay"] = config["platforms"][platform]["options"].get("inactivity_delay", 120)  # Default to 120 seconds if not set
with open(config_file, "w") as f:
    yaml.dump(config, f, indent=2)
'
fi

# === STEP 1: KILL EXISTING APPLICATION IF RUNNING ===
if [ "$PLATFORM" = "windsurf" ]; then
  pkill -f "Windsurf" || true
  APP_NAME="Windsurf"
else
  pkill -f "Cursor" || true
  APP_NAME="Cursor"
fi

# === STEP 2: OPEN FOLDER IN APPROPRIATE APPLICATION ===
if [ "$PLATFORM" = "cursor" ]; then
  if command -v cursor >/dev/null 2>&1; then
    echo "Detected cursor CLI, opening project with cursor CLI..."
    cursor "$PROJECT_PATH"
  else
    echo "Opening project in Cursor using AppleScript..."
    osascript <<EOF
      tell application "Cursor"
        activate
        open POSIX file "$PROJECT_PATH"
      end tell
EOF
  fi
else
  echo "Opening project with open -a $APP_NAME ..."
  open -a "$APP_NAME" "$PROJECT_PATH"
fi

python3 generate_initial_prompt.py

# Ensure chat window is open using OpenAI Vision
python3 ensure_chat_window.py "$PLATFORM"

# Send the initial prompt immediately after opening the chat window, starting a new chat
if [ -f "initial_prompt.txt" ]; then
  python3 -c 'import yaml,os; from actions.send_to_cursor import send_prompt; config=yaml.safe_load(open(os.environ["CONFIG_FILE"])); platform=os.environ.get("PLATFORM", "cursor"); p=config["platforms"][platform]; send_prompt(open("initial_prompt.txt").read().strip(), platform=platform, new_chat=True, send_message=p["options"].get("enable_auto_mode", True))'
fi

# Start Slack bot and watcher together with combined logs
echo "Starting Slack bot and Cursor watcher... (auto mode: $auto_mode, send messages: $send_message)"
python3 run_both.py $auto_mode "$PLATFORM"
