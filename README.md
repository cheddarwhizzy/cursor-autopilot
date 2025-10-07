# Cursor Autopilot

A powerful automation tool for Cursor and Windsurf IDEs that helps manage tasks and streamline development workflows.

## Quick Start

This repository contains two different approaches to Cursor automation:

### 🚀 [Cursor Agent Iteration](./cursor-agent-iteration/)
**New approach** - Agent-based iteration system with advanced automation capabilities
- [Quick Start Guide](./cursor-agent-iteration/docs/QUICK_START.md)
- [Examples](./cursor-agent-iteration/docs/EXAMPLES.md)
- [Full Documentation](./cursor-agent-iteration/docs/CURSOR_ITERATION_README.md)

### 🔧 [Cursor IDE Autopilot](./cursor-ide-autopilot/)
**Original approach** - File watcher and keystroke automation system
- [Quick Start Guide](./cursor-ide-autopilot/docs/quick_start.md)
- [Configuration Guide](./cursor-ide-autopilot/docs/configuration/yaml_configuration.md)
- [API Documentation](./cursor-ide-autopilot/docs/api/flask_configuration.md)

## Which Should I Use?

- **Cursor Agent Iteration**: For advanced AI-powered development workflows with agent-based task management
- **Cursor IDE Autopilot**: For traditional file watching and keystroke automation

Note: Use the Thinking mode with LLMs, you'll get better results.

## Project Structure

```
cursor-autopilot/
├── cursor-agent-iteration/     # New agent-based approach
│   ├── docs/                  # Agent iteration documentation
│   ├── bootstrap.sh           # Installation script
│   └── README.md              # Agent iteration guide
├── cursor-ide-autopilot/      # Original file watcher approach
│   ├── docs/                  # IDE autopilot documentation
│   ├── src/                   # Source code
│   ├── tests/                 # Test files
│   └── run.sh                 # Main script
└── README.md                  # This file
```