# Automation & AppleScript

## AppleScript Integration

The project uses AppleScript (osascript) to control Cursor, ensuring the chat window is always activated before sending prompts. This enables seamless automation for:
- Opening the chat window
- Sending code and messages
- Switching between manual and autonomous modes

## File Overview

- `run.sh` — Main entry script
- `run_both.py` — Runs Slack bot and watcher concurrently with unified logs
- `slack_bot.py` — Flask app for Slack bot
- `watcher.py` — Watches for inactivity in the project directory
- `actions/send_to_cursor.py` — Handles AppleScript automation for Cursor

## Usage Notes

- All automation (AppleScript, window management, etc.) requires macOS and will not work on Windows.
- You can run as many VMs as your hardware allows, each with its own Cursor Autopilot instance and configuration.

See [SETUP.md](./SETUP.md) for the main workflow.
