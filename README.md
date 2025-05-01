# Cursor Autopilot

A powerful automation tool for Cursor and Windsurf IDEs that helps manage tasks and streamline development workflows.

## Quick Start

For a detailed quick start guide, see [Quick Start Guide](./docs/quick_start.md).

Basic usage:
```bash
./run.sh --platform cursor
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
project_path: "$(pwd)"
platform: "cursor"
inactivity_delay: 300
send_message: true
debug: false
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

Enable debug mode:
```bash
./run.sh --platform cursor --debug
```

## License

MIT License - See [LICENSE](./LICENSE) for details.
