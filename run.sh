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
echo "Installing required packages..."
pip install flask

# === CONFIGURATION ===
PROJECT_PATH="$HOME/cheddar/mushattention/mushattention"
PROMPT="
You are working in a pre-existing TypeScript application. 
Before implementing any feature, **always reference and update `file-structure.md`**.

It contains documentation on existing components, API routes, utility files, and their responsibilities. 
Do not create a file if it already exists — search `file-structure.md` first.

Use the @src/notifications/README.md as your task list. Implement each feature one by one, and after each one:
- Update `file-structure.md` to reflect any new files or components.
- Write tests for the feature.
- Test it end to end.
- Mark the feature as completed inside @src/notifications/README.md.

If a file doesn't exist, document it before creating it."


# === STEP 1: OPEN FOLDER IN CURSOR ===
open -a "Cursor" "$PROJECT_PATH"

# Start Slack bot and watcher together with combined logs
echo "Starting Slack bot and Cursor watcher..."
python3 run_both.py
