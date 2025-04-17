# Cursor Autopilot

This project provides automation for interacting with the Cursor editor and a Slack bot, enabling seamless workflow management and remote control via Slack commands.

## Features
- **Slack Bot**: A Flask-based bot that listens for commands and triggers actions in Cursor.
- **Watcher**: Monitors a specified project directory for inactivity and sends prompts to Cursor when appropriate.
- **Automation Scripts**: Includes scripts to launch both the Slack bot and watcher together, ensuring both logs are visible and processes are managed cleanly.
- **AppleScript Integration**: Uses AppleScript (osascript) to control Cursor, ensuring the chat window is always activated before sending prompts.

## Requirements
- Python 3.8+
- macOS (required for AppleScript integration)
- [Cursor](https://www.cursor.so/) editor installed
- Slack workspace (for bot integration)

### Python Version Management with Pyenv
To ensure consistent Python version across different machines, we recommend using Pyenv:

1. Install Pyenv:
```bash
brew install pyenv
```

2. Add Pyenv to your shell configuration:
```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
```

3. Install Python 3.13.2:
```bash
pyenv install 3.13.2
```

4. Set the local Python version:
```bash
pyenv local 3.13.2
```

5. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

## Getting Started

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd cursor-autopilot
```

### 2. Set Up the Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install flask
```

### 4. Configuration
Edit the `PROJECT_PATH` variable in `run.sh` to point to your target project directory.

### 5. Running the Project
To start both the Slack bot and the watcher with combined logs:
```bash
./run.sh
```

Alternatively, you can run the Python orchestrator directly:
```bash
python3 run_both.py
```

## Configuration

All major settings are controlled via `config.json` in the project root. Example:

```json
{
  "project_path": "~/cheddar/mushattention/mushattention",
  "task_readme_path": "@src/notifications/README.md",
  "platform": "cursor" // or "windsurf"
}
```

- `project_path`: Path to the project directory to watch.
- `task_readme_path`: The README file to track for marking feature completion.
- `platform`: Editor automation target. Use `cursor` (default) or `windsurf`.

## How to Run

1. **Clone and Install**
    ```bash
    git clone <your-repo-url>
    cd cursor-autopilot
    python3 -m venv venv
    source venv/bin/activate
    pip install flask openai pytesseract
    # (Optional) brew install tesseract
    ```

2. **Configure**
    - Edit `config.json` to match your environment and workflow.

3. **Start the App**
    - Use the provided script to launch everything:
    ```bash
    ./run.sh --auto
    ```
    The `--auto` flag enables autonomous mode, allowing the watcher to automatically send prompts and manage the workflow without manual intervention.
    
    This script will:
    - Open your project in Cursor
    - Generate `initial_prompt.txt` from your config
    - Ensure the chat window is open
    - Start both the Slack bot and watcher with unified logs

    You can pass additional flags to `./run.sh` if needed (see comments in the script for details).

4. **Slack Bot**
    - The Slack bot listens for commands (see below for usage).

5. **Watcher**
    - Monitors your project directory and the configured task README. When a feature is marked complete in the README, the next prompt will start a new chat.

## Slack Bot Usage
The Slack bot listens for commands such as:
- `code` — Switch to code mode
- `auto` — Switch to auto mode
- `send <your prompt>` — Send a prompt to Cursor
- `screenshot` — Capture a chat screenshot
- `status` — Get current mode

## AppleScript Automation
The integration ensures Cursor's chat window is always activated (using Command+L) before sending commands, even if the code window is focused.

## Testing the Slack Bot Locally

You can test the Slack bot's endpoints directly by sending POST requests to the running Flask server. Use the following `curl` commands to simulate Slack commands:

Replace `USER_NAME` with your desired username (optional).

### Enter Manual Mode (code)
```bash
curl -X POST http://localhost:5005/cursor -d 'text=code&user_name=USER_NAME'
```

### Enable Autonomous Coding (auto)
```bash
curl -X POST http://localhost:5005/cursor -d 'text=auto&user_name=USER_NAME'
```

### Send a Message to Cursor
```bash
curl -X POST http://localhost:5005/cursor -d 'text=send <your message here>&user_name=USER_NAME'
```

### Capture Chat Window Screenshot
```bash
curl -X POST http://localhost:5005/cursor -d 'text=screenshot&user_name=USER_NAME'
```

### Show Current Mode
```bash
curl -X POST http://localhost:5005/cursor -d 'text=status&user_name=USER_NAME'
```

These commands simulate the Slack slash commands:
- `/cursor code` — Enters manual mode (Cursor stops auto-run)
- `/cursor auto` — Enables autonomous coding
- `/cursor send <msg>` — Sends `<msg>` to Cursor IDE
- `/cursor screenshot` — Captures chat window and saves screenshot
- `/cursor status` — Shows current mode

You should see the corresponding responses in your terminal or as output from the Flask server.

## File Overview
- `run.sh` — Main entry script
- `run_both.py` — Runs Slack bot and watcher concurrently with unified logs
- `slack_bot.py` — Flask app for Slack bot
- `watcher.py` — Watches for inactivity in the project directory
- `actions/send_to_cursor.py` — Handles AppleScript automation for Cursor

## Usage Notes & Multi-Project Setup

This project is designed for macOS only (no Windows support currently). It works seamlessly on physical Macs and in virtual machines (VMs).

**How I use it:**
- I run macOS in virtual machines using Parallels (or any VM provider).
- Each VM runs this application for a different project/IDE/account.
- This allows me to have multiple projects, IDEs, and accounts running in parallel, each isolated in its own VM.
- This setup is ideal for managing several workspaces, keeping environments separate, and avoiding account conflicts.

**Note:**
- All automation (AppleScript, window management, etc.) requires macOS and will not work on Windows.
- You can run as many VMs as your hardware allows, each with its own Cursor Autopilot instance and configuration.

## License
MIT
