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
  debug: false  # Enable debug logging
  send_message: true  # Enable sending messages to the IDE
  use_gitignore: true  # Respect .gitignore files
```

### Prompt Configuration

You can configure prompts in the config file or override them via command line:

```yaml
general:
  # Default initial prompt (used when no file is specified)
  initial_prompt: |
    Review the tasks in {task_file_path} and additional context in {additional_context_path}.
    Start working on the first task.
    
  # Default continuation prompt (used when no file is specified)
  inactivity_prompt: |
    Continue with the next task from {task_file_path}.
    Focus on completing one task at a time.

# Platform-specific prompt overrides
platforms:
  cursor_meanscoop:
    # Path to a file containing the initial prompt (relative to project_path)
    initial_prompt_file_path: "prompts/initial_prompt.txt"
    
    # Path to a file containing the continuation prompt (relative to project_path)
    continuation_prompt_file_path: "prompts/continuation_prompt.txt"
```

### Environment Variables

You can also use environment variables to override configuration:

```bash
export CURSOR_AUTOPILOT_PROJECT_PATH="/path/to/project"
export CURSOR_AUTOPILOT_PLATFORM="cursor_meanscoop"
./run.sh
```

Environment variables take precedence over config file settings but are overridden by command line arguments.

## License

MIT License - See [LICENSE](./LICENSE) for details.

### File Monitoring

The system monitors file changes to reset inactivity timers. Key behaviors:

- **Important Files**: Certain files always trigger activity regardless of gitignore patterns:
  - `tasks.md`, `todo.md`, `readme.md`, `architecture.md`
  - `continuation_prompt.txt`, `initial_prompt.txt`
- **Gitignore Patterns**: Other files respect `.gitignore` patterns when `use_gitignore: true`
- **Activity Reset**: Any change to non-ignored files resets the platform's inactivity timer

This ensures that task files and other critical project files always trigger activity updates, even in projects with broad gitignore patterns like `*`.
