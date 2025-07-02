# Cursor Autopilot

A powerful automation tool for Cursor and Windsurf IDEs that helps manage tasks and streamline development workflows.

## Quick Start

For a detailed quick start guide, see [Quick Start Guide](./docs/quick_start.md).

Basic usage:

Note: Use the Thinking mode with LLMs, you'll get better results.

## Running the Application

### Using the main script (recommended)

The main `run.sh` script provides a unified way to run the autopilot with various configuration options:

```bash
# Basic usage - uses all settings from config.yaml
./run.sh

# Run with a specific platform (comma-separated for multiple)
./run.sh --platform=cursor_meanscoop
./run.sh --platform=cursor_meanscoop,windsurf_mushattention

# Override project path
./run.sh --platform=cursor --project-path=/path/to/your/project

# Override task file and additional context paths
./run.sh --platform=cursor --task-file-path=MY_TASKS.md --additional-context-path=ARCHITECTURE.md

# Set custom prompts
./run.sh --platform=cursor --initial-prompt="Review the tasks and start working on them" --continuation-prompt="Continue with the next task"

# Set inactivity delay (in seconds)
./run.sh --platform=cursor --inactivity-delay=300

# Enable debug mode for more verbose output
./run.sh --debug

# Run in no-send mode (don't send keystrokes to the IDE)
./run.sh --no-send

# Run in auto mode
./run.sh --auto

# Combine multiple options
./run.sh --platform=cursor --project-path=/path/to/project --task-file-path=TASKS.md --continuation-prompt="Continue with the next task" --debug
```

### Command Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--platform` | Comma-separated list of platforms to run | `--platform=cursor_meanscoop,windsurf_mushattention` |
| `--project-path` | Override the project path from config | `--project-path=/path/to/project` |
| `--task-file-path` | Override the task file path | `--task-file-path=TASKS.md` |
| `--additional-context-path` | Override the additional context file path | `--additional-context-path=ARCHITECTURE.md` |
| `--initial-prompt` | Set a custom initial prompt | `--initial-prompt="Review the tasks and start working"` |
| `--continuation-prompt` | Set a custom continuation prompt | `--continuation-prompt="Continue with the next task"` |
| `--inactivity-delay` | Set the inactivity delay in seconds | `--inactivity-delay=300` |
| `--debug` | Enable debug logging | `--debug` |
| `--no-send` | Don't send keystrokes to the IDE | `--no-send` |
| `--auto` | Enable auto mode | `--auto` |
| `--api` | Start both watcher and configuration API server | `--api` |

### API Mode

When running with the `--api` flag, both the file watcher and a configuration API server are started:

```bash
# Run with API server for configuration management
./run.sh --api --platform=cursor_meanscoop

# In a separate terminal, watch countdown messages clearly
./scripts/watch_countdown.sh
```

**Note**: When running in API mode, countdown timer messages are prefixed with `"WATCHER |"` and might be less visible in the main terminal. Use the `watch_countdown.sh` script to monitor countdown messages clearly in a separate terminal.

### Configuration File

You can also configure these settings in the `config.yaml` file. Command line arguments will override the configuration file settings.

## Core Concepts

- **Task Management**: Track and automate development tasks
- **IDE Integration**: Seamless integration with Cursor and Windsurf
- **Automation**: Automated keystrokes and window management
- **Monitoring**: Real-time progress tracking and logging

## Features

- 🚀 Automated task execution
- 🔄 Cross-platform support
- 🔍 Real-time monitoring
- 📊 Progress tracking
- 🔐 Secure configuration
- 📝 Comprehensive logging

## Configuration 

See [Configuration Guide](./docs/configuration/yaml_configuration.md) for detailed configuration options.

Basic configuration in `config.yaml`:
```yaml
# Basic config.yaml structure expected by run.sh
platforms:
  windsurf:
    # Set the default project path (can be overridden with --project-path flag)
    project_path: "/path/to/your/default/project" # Or use "$(pwd)"
# general:
  # inactivity_delay: 300
  # send_message: true
  # debug: false
```

## Documentation

- [Quick Start Guide](./docs/quick_start.md)
- [Configuration Guide](./docs/configuration/yaml_configuration.md)
- [API Documentation](./docs/api/flask_configuration.md)
- [Automation Guide](./docs/automation/simultaneous_automation.md)
- [Vision Integration](./docs/vision/openai_vision.md)

## Project Structure

```
cursor-autopilot/
├── docs/                  # Documentation
│   ├── api/              # API documentation
│   ├── automation/       # Automation guides
│   ├── configuration/    # Configuration guides
│   └── vision/          # Vision integration docs
├── src/                  # Source code
├── tests/               # Test files
├── config.yaml          # Configuration file
├── tasks.md             # Task definitions
├── context.md           # Project context
└── run.sh              # Main script
```

## Debugging

To enable debug mode and get more detailed logs:

```bash
./run.sh --platform=cursor --debug
```

Check the script logs for detailed information during execution. The logs will show you which configuration values are being used and any warnings or errors that occur.

## Troubleshooting

If you experience issues with platforms not launching:

1. Try using the specialized launcher scripts mentioned above
2. Check the logs for specific error messages
3. Ensure the project paths in `config.yaml` are correct and accessible
4. Kill any existing instances of Cursor or Windsurf manually before running
5. Verify your window titles match what's in the config

## Configuration

### Platform Configuration

To set up multiple instances of platforms:

1. In `config.yaml`, define each platform with a unique name:

```yaml
platforms:
  cursor_meanscoop:
    type: "cursor"
    window_title: "Cursor - Mean Scoop"
    project_path: "/path/to/meanscoop/project"
    task_file_path: "TASKS.md"  # Relative to project_path
    additional_context_path: "ARCHITECTURE.md"  # Relative to project_path
    initialization_delay_seconds: 5  # Wait for IDE to be ready
    
  windsurf_mushattention:
    type: "windsurf"
    window_title: "WindSurf - Mushattention"
    project_path: "/path/to/mushattention/project"
    task_file_path: "TASKS.md"
    additional_context_path: "docs/ARCHITECTURE.md"
    initialization_delay_seconds: 8
```

2. Specify which platforms should be active by default:

```yaml
general:
  active_platforms: ["cursor_meanscoop", "windsurf_mushattention"]
  inactivity_delay: 300  # Default inactivity delay in seconds
  regular_keystroke_interval: 30  # Default interval for regular keystrokes (seconds)
  debug: false  # Enable debug logging
  send_message: true  # Enable sending messages to the IDE
  use_gitignore: true  # Respect .gitignore files
```

### Regular Keystrokes

The system supports sending regular keystrokes at configurable intervals. This is useful for platforms like Windsurf that require periodic interaction to continue processing (e.g., using `option+enter` to continue with AI assistance).

```yaml
# Global default interval (can be overridden per platform)
general:
  regular_keystroke_interval: 30  # Seconds between regular keystrokes

# Platform-specific configuration
platforms:
  windsurf_meanscoop:
    regular_keystroke_interval: 30  # Override global default for this platform
    regular_keystrokes:
      - keys: "option+enter"  # Windsurf continue hotkey
        delay_ms: 100
```

**Key Features:**
- **Configurable Interval**: Set how often regular keystrokes are sent (5-300 seconds)
- **Platform-Specific**: Each platform can have its own interval and keystrokes
- **Independent of Inactivity**: Regular keystrokes are sent regardless of file activity
- **Windsurf Optimized**: Specifically designed for Windsurf's `option+enter` continue functionality

**Configuration Options:**
- `regular_keystroke_interval`: Time in seconds between keystroke sends (global default: 30)
- `regular_keystrokes`: Array of keystroke objects to send at each interval
- Only platforms with `regular_keystrokes` defined will have regular keystrokes sent

### Prompt Configuration