# YAML Configuration Guide

## Overview

The Cursor Autopilot uses a YAML configuration file (`config.yaml`) to manage all settings. This guide explains the configuration options and their usage.

## Basic Configuration

```yaml
# config.yaml
project_path: "/path/to/project"
platform: "cursor"  # or "windsurf"
inactivity_delay: 300
send_message: true
debug: false
```

## Platform Configuration

### Cursor
```yaml
platforms:
  cursor:
    os_type: "osx"  # or "windows", "linux"
    project_path: "/path/to/project"
    task_file_path: "tasks.md"
    keystrokes:
      - "command+p"
      - "enter"
    options:
      enable_auto_mode: true
      inactivity_delay: 300
```

### Windsurf
```yaml
platforms:
  windsurf:
    os_type: "osx"  # or "windows"
    project_path: "/path/to/project"
    task_file_path: "tasks.md"
    keystrokes:
      - "ctrl+p"
      - "enter"
    options:
      enable_auto_mode: true
      inactivity_delay: 300
```

## General Settings

```yaml
general:
  active_platforms: ["cursor"]  # or ["windsurf"] or ["cursor", "windsurf"]
  inactivity_delay: 300
  debug: false
  task_file_path: "tasks.md"
  context_file_path: "context.md"
```

## Integration Settings

### Slack
```yaml
slack:
  webhook_url: "https://hooks.slack.com/services/..."
  channel: "#general"
  username: "Cursor Autopilot"
  icon_emoji: ":robot_face:"
```

### OpenAI Vision
```yaml
openai:
  api_key: "sk-..."
  model: "gpt-4-vision-preview"
  max_tokens: 300
  temperature: 0.7
```

## Command Line Overrides

All settings in `config.yaml` can be overridden using command-line arguments:

```bash
./run.sh --platform cursor --project-path /new/path --inactivity-delay 60
```

## Validation Rules

1. Required Fields:
   - `project_path`: Must be an existing directory
   - `platform`: Must be "cursor" or "windsurf"

2. Field Types:
   - `project_path`: String (absolute path)
   - `platform`: String (comma-separated list)
   - `inactivity_delay`: Integer (positive)
   - `send_message`: Boolean
   - `debug`: Boolean

3. Platform-Specific Requirements:
   - Cursor: Works on macOS, Windows, Linux
   - Windsurf: Works on macOS, Windows

## Examples

### Basic Setup
```yaml
project_path: "/Users/me/my_project"
platform: "cursor"
inactivity_delay: 300
send_message: true
debug: false
```

### Multiple Platforms
```yaml
project_path: "/Users/me/my_project"
platform: "cursor,windsurf"
inactivity_delay: 300
send_message: true
debug: false
```

### With Integrations
```yaml
project_path: "/Users/me/my_project"
platform: "cursor"
inactivity_delay: 300
send_message: true
debug: false

slack:
  webhook_url: "https://hooks.slack.com/services/..."
  channel: "#general"

openai:
  api_key: "sk-..."
  model: "gpt-4-vision-preview"
```

## Troubleshooting

1. **Invalid Configuration**
   - Check YAML syntax
   - Verify required fields
   - Ensure paths exist
   - Check platform compatibility

2. **Platform Issues**
   - Verify IDE installation
   - Check permissions
   - Test keystrokes manually

3. **Integration Problems**
   - Verify API keys
   - Check network connectivity
   - Review rate limits

## Best Practices

1. **Configuration Management**
   - Use version control
   - Keep sensitive data in environment variables
   - Document changes
   - Test configuration changes

2. **Performance**
   - Set appropriate inactivity delays
   - Monitor resource usage
   - Use debug mode for troubleshooting

3. **Security**
   - Never commit API keys
   - Use environment variables
   - Regular security audits
   - Monitor access logs 