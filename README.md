# Cursor Autopilot

A powerful automation tool for Cursor and Windsurf IDEs that helps manage tasks and streamline development workflows.

## Quick Start

For a detailed quick start guide, see [Quick Start Guide](./docs/quick_start.md).

Basic usage:

Note: Use the Thinking mode with LLMs, you'll get better results.

## Running the Application

There are multiple ways to run this application:

### Using the main script (recommended)

```bash
./run.sh
```

### Using the specialized launcher script

This is useful for troubleshooting or when you want to launch just a specific platform:

```bash
# Launch all platforms defined in the config.yaml
./run_launch.sh

# Launch a specific platform
./run_launch.sh --platform=cursor_meanscoop
./run_launch.sh --platform=windsurf_mushattention
```

### Using the dedicated Cursor launcher

For cases where only Cursor needs to be launched:

```bash
PYTHONPATH=. ./launch_cursor_only.py
```

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

# Enable debug mode:
# ```bash
# ./run.sh --platform cursor --debug # Note: --debug flag is not currently parsed by run.sh
# ```

Check the script logs for detailed information during execution.

## Troubleshooting

If you experience issues with platforms not launching:

1. Try using the specialized launcher scripts mentioned above
2. Check the logs for specific error messages
3. Ensure the project paths in `config.yaml` are correct and accessible
4. Kill any existing instances of Cursor or Windsurf manually before running
5. Verify your window titles match what's in the config

## Configuration

To set up multiple instances of platforms:

1. In `config.yaml`, define each platform with a unique name:

```yaml
platforms:
  cursor_meanscoop:
    type: "cursor"
    window_title: "Cursor - Mean Scoop"
    project_path: "/path/to/meanscoop/project"
    # other settings...
    
  windsurf_mushattention:
    type: "windsurf"
    window_title: "WindSurf - Mushattention"
    project_path: "/path/to/mushattention/project"
    # other settings...
```

2. Specify which platforms should be active:

```yaml
general:
  active_platforms: ["cursor_meanscoop", "windsurf_mushattention"]
```

## License

MIT License - See [LICENSE](./LICENSE) for details.
