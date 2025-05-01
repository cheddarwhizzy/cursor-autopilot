# YAML Configuration Guide

## Overview
This document describes the YAML configuration format used by the automation system. The configuration file (`config.yaml`) controls various aspects of the automation behavior, including keystrokes, delays, and platform-specific settings.

## Configuration Schema

### Basic Structure
```yaml
# Global settings
project_path: "/path/to/project"
platform: "cursor|windsurf"  # or both
debug: true|false
inactivity_delay: 300  # seconds

# Platform-specific settings
platforms:
  cursor:
    initialization_keystrokes:
      - "command+k"
      - "enter"
    inactivity_keystrokes:
      - "command+k"
      - "enter"
    timeout: 300  # seconds

  windsurf:
    initialization_keystrokes:
      - "ctrl+k"
      - "enter"
    inactivity_keystrokes:
      - "ctrl+k"
      - "enter"
    timeout: 300  # seconds

# OpenAI Vision settings
vision:
  enabled: true
  conditions:
    - file_type: "*.py"
      action: "save"
    - file_type: "*.js"
      action: "save"
  api_key: "your-api-key"  # Optional, can be set via environment variable

# Slack integration
slack:
  enabled: true
  webhook_url: "your-webhook-url"  # Optional, can be set via environment variable
  channels:
    - "general"
    - "automation"
```

## Platform-Specific Configuration

### macOS
- Use `command` for modifier keys
- Example keystrokes:
  ```yaml
  keystrokes:
    - "command+k"
    - "command+shift+k"
    - "command+option+k"
  ```

### Windows
- Use `ctrl` for modifier keys
- Example keystrokes:
  ```yaml
  keystrokes:
    - "ctrl+k"
    - "ctrl+shift+k"
    - "ctrl+alt+k"
  ```

### Linux
- Use `ctrl` for modifier keys
- Example keystrokes:
  ```yaml
  keystrokes:
    - "ctrl+k"
    - "ctrl+shift+k"
    - "ctrl+alt+k"
  ```

## Validation Rules

### Required Fields
- `project_path`: Must be a valid directory path
- `platform`: Must be one of: "cursor", "windsurf", or both
- `inactivity_delay`: Must be a positive integer

### Optional Fields
- `debug`: Boolean (default: false)
- `vision.enabled`: Boolean (default: false)
- `slack.enabled`: Boolean (default: false)

### Platform-Specific Requirements
- Each platform must have:
  - `initialization_keystrokes`
  - `inactivity_keystrokes`
  - `timeout` (in seconds)

## Troubleshooting

### Common Issues

1. **Keystrokes not working**
   - Verify platform-specific key mappings
   - Check for conflicting keyboard shortcuts
   - Ensure proper permissions for keyboard input

2. **Inactivity detection issues**
   - Verify `inactivity_delay` value
   - Check system permissions
   - Ensure no conflicting automation tools

3. **Platform switching problems**
   - Verify platform names in configuration
   - Check application window titles
   - Ensure applications are running

### Error Messages

- `Invalid platform specified`: Check platform name in configuration
- `Project path does not exist`: Verify project path is correct
- `Invalid keystroke format`: Check keystroke syntax
- `Missing required field`: Add missing configuration field

## Examples

### Basic Configuration
```yaml
project_path: "/Users/username/projects/my-project"
platform: "cursor"
debug: false
inactivity_delay: 300

platforms:
  cursor:
    initialization_keystrokes:
      - "command+k"
      - "enter"
    inactivity_keystrokes:
      - "command+k"
      - "enter"
    timeout: 300
```

### Multi-Platform Configuration
```yaml
project_path: "/Users/username/projects/my-project"
platform: "cursor,windsurf"
debug: true
inactivity_delay: 300

platforms:
  cursor:
    initialization_keystrokes:
      - "command+k"
      - "enter"
    inactivity_keystrokes:
      - "command+k"
      - "enter"
    timeout: 300

  windsurf:
    initialization_keystrokes:
      - "ctrl+k"
      - "enter"
    inactivity_keystrokes:
      - "ctrl+k"
      - "enter"
    timeout: 300
```

### Advanced Configuration with Vision
```yaml
project_path: "/Users/username/projects/my-project"
platform: "cursor"
debug: false
inactivity_delay: 300

platforms:
  cursor:
    initialization_keystrokes:
      - "command+k"
      - "enter"
    inactivity_keystrokes:
      - "command+k"
      - "enter"
    timeout: 300

vision:
  enabled: true
  conditions:
    - file_type: "*.py"
      action: "save"
    - file_type: "*.js"
      action: "save"
  api_key: "your-api-key"

slack:
  enabled: true
  webhook_url: "your-webhook-url"
  channels:
    - "general"
    - "automation"
``` 