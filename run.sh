#!/bin/bash

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi



# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required packages
echo "Installing required Python packages..."
pip install flask openai pytesseract

# Check for tesseract-ocr (needed for pytesseract)
if ! command -v tesseract >/dev/null 2>&1; then
  echo "Warning: tesseract-ocr is not installed. Please install it with 'brew install tesseract' for OCR support."
fi

# === CONFIGURATION ===
PROJECT_PATH="$HOME/cheddar/mushattention/mushattention"
# The initial prompt is now stored in initial_prompt.txt

# Parse flags for auto mode
auto_mode=0
for arg in "$@"; do
  case $arg in
    --auto)
      auto_mode=1
      ;;
    --no-auto)
      auto_mode=0
      ;;
  esac
done
export CURSOR_AUTOPILOT_AUTO_MODE=$auto_mode

# === STEP 1: OPEN FOLDER IN CURSOR ===
open -a "Cursor" "$PROJECT_PATH"

python3 generate_initial_prompt.py

# Ensure chat window is open using OpenAI Vision
python3 ensure_chat_window.py

# Start Slack bot and watcher together with combined logs
echo "Starting Slack bot and Cursor watcher... (auto mode: $auto_mode)"
python3 run_both.py $auto_mode
