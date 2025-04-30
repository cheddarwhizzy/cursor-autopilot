# Cursor Autopilot

An autonomous development assistant that automatically implements features by following a structured task list, using Cursor or Windsurf as its interface.

## Quick Start

1.  **Install Dependencies**: `pip install -r requirements.txt`
2.  **Configure**: Edit `config.yaml` (set `project_path` and target `platforms`).
3.  **Create Task Files**: Ensure `tasks.md` and `context.md` exist in your project.
4.  **Run**: `./run.sh --platform cursor --debug` (replace `cursor` if needed)
    *   Use `--auto` for fully automatic mode.
    *   Override settings: `./run.sh --platform cursor --inactivity-delay 60`

For more detailed setup and configuration, see the [Full Documentation](#-documentation).

## Overview

Cursor Autopilot reads tasks from a task list (`tasks.md`), understands project context (`context.md`), and autonomously implements each feature step-by-step using the configured platform (Cursor or Windsurf). It monitors file changes to track progress and uses inactivity timers to continue its work.

## Features

- Autonomous feature implementation following a structured task list (`tasks.md`).
- Reads and understands project documentation and architecture (`context.md`).
- Automatically detects code changes and progress via file monitoring.
- Configurable automation behavior via `config.yaml`.
- Supports **Cursor** and **Windsurf** IDEs on **macOS**, **Windows**, and **Linux**.
- Cross-platform keystroke sending using `pyautogui`.
- Command-line overrides for `config.yaml` settings using `argparse`.
- Slack integration for remote control and notifications (via API endpoints).
- Optional OpenAI Vision integration for visual analysis.
- Detailed logging with color-coded output.

## Configuration (`config.yaml`)

The primary configuration is done via `config.yaml`. Key settings include:

- `platforms`: Configure settings specific to Cursor, Windsurf, etc.
  - `os_type`: (Informational) `osx`, `windows`, `linux`
  - `project_path`: **Required** path to the project being worked on.
  - `task_file_path`: Path to the task list (relative to `project_path`).
  - `keystrokes`: Sequences of keys to press for automation.
- `general`:
  - `active_platforms`: List of platforms to run (e.g., `["cursor"]`).
  - `inactivity_delay`: Seconds of inactivity before sending a continuation prompt.
  - `debug`: Enable verbose logging.
- `slack` / `openai`: Settings for integrations.

See the [Full Configuration Guide](./docs/configuration/yaml_config.md) for all options.

## Command-Line Arguments

You can override `config.yaml` settings using command-line flags:

- `--project-path /new/path`: Set project directory.
- `--platform cursor,windsurf`: Set active platforms (comma-separated).
- `--inactivity-delay 60`: Set inactivity delay to 60 seconds.
- `--send-message` / `--no-send-message`: Override message sending flag.
- `--debug`: Enable debug logging.

Run `python main.py --help` (or `./run.sh --help` after `run.sh` is updated) for a full list.

## Usage

```bash
# Run automatically with debug logs for Cursor
./run.sh --platform cursor --debug --auto

# Run manually for Windsurf, overriding inactivity delay
./run.sh --platform windsurf --inactivity-delay 90

# Run both platforms staggered (requires config setup)
./run.sh --platform cursor,windsurf 
```

(Note: `run.sh` needs to be updated to call the Python script that uses `argparse`)

## File Structure

- `config.yaml`: Main configuration.
- `tasks.md`: Feature implementation list.
- `context.md`: Project context and architecture.
- `architecture.md`: Technical design decisions.
- `watcher.py`: File monitoring and main loop.
- `actions/`: Modules for IDE interaction, etc.
- `api_documentation.md`: Details on Flask API endpoints.
- `docs/`: Folder for detailed documentation.

## Logging

Color-coded logs provide insights:
- Blue: Notice
- Green: Success
- Yellow: Warning
- Red: Error

Enable debug logging with `--debug`.

## License

MIT

---

## 📚 Documentation

- **Quick Start**: See [Quick Start](#quick-start) section above.
- **Configuration**: [YAML Config Guide](./docs/configuration/yaml_config.md)
- **API Docs**:
  - [Flask API](./api_documentation.md)
  - [Slack Endpoints](./docs/api/slack_endpoints.md)
- **Setup & Installation**: [Installation Guide](./docs/INSTALLATION.md), [Setup Guide](./docs/SETUP.md)
- **Core Concepts**: [Architecture](./architecture.md), [Automation](./docs/AUTOMATION.md)
- **Integrations**: [Slack Bot](./docs/SLACK_BOT.md)
- **Other Docs**: [Original Docs](./docs.md), [Context](./context.md)
