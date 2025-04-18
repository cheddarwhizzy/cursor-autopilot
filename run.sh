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
# Extract PROJECT_PATH from config.json
export CONFIG_FILE="$(dirname "$0")/config.json"
if [ -f "$CONFIG_FILE" ]; then
  PROJECT_PATH=$(python3 -c 'import json,os; c=json.load(open(os.environ["CONFIG_FILE"])); print(os.path.expanduser(c["project_path"]))' CONFIG_FILE="$CONFIG_FILE")
else
  echo "Error: config.json not found. Set CONFIG_FILE environment variable to the path of your config.json file."
  exit 1
fi

# The initial prompt is now stored in initial_prompt.txt

# Parse flags for auto mode and send message behavior
auto_mode=0
send_message=true

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
  esac
done

export CURSOR_AUTOPILOT_AUTO_MODE=$auto_mode

# Update send_message in config.json
python3 -c '
import json
import os
config_file = os.environ["CONFIG_FILE"]
with open(config_file, "r") as f:
    config = json.load(f)
config["send_message"] = True if "'$send_message'" == "true" else False
with open(config_file, "w") as f:
    json.dump(config, f, indent=2)
'

# === STEP 1: OPEN FOLDER IN CURSOR ===
open -a "Cursor" "$PROJECT_PATH"

python3 generate_initial_prompt.py

# Ensure chat window is open using OpenAI Vision
python3 ensure_chat_window.py

# Send the initial prompt immediately after opening the chat window, starting a new chat
if [ -f "initial_prompt.txt" ]; then
  python3 -c 'import json,os; from actions.send_to_cursor import send_prompt; config=json.load(open(os.environ["CONFIG_FILE"])); send_prompt(open("initial_prompt.txt").read().strip(), new_chat=True, send_message=config.get("send_message", True))'
fi

# Start Slack bot and watcher together with combined logs
echo "Starting Slack bot and Cursor watcher... (auto mode: $auto_mode, send messages: $send_message)"
python3 run_both.py $auto_mode
