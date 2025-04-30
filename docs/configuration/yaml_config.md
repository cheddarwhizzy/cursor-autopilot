# YAML Configuration Guide

## Overview

The Cursor Autopilot system uses a YAML-based configuration file (`config.yaml`) to control all aspects of automation, including platform-specific settings, keystroke mappings, and integration configurations.

## Configuration Schema

### Top-Level Structure

```yaml
platforms:
  # Platform-specific configurations
  cursor:
    # Cursor IDE settings
  windsurf:
    # Windsurf IDE settings

general:
  # Global settings

slack:
  # Slack integration settings

openai:
  # OpenAI integration settings
```

### Platform Configuration

Each platform (cursor, windsurf) supports the following configuration options:

```yaml
platforms:
  cursor:
    os_type: osx  # or 'windows' or 'linux'
    project_path: "/path/to/project"
    task_file_path: "tasks.md"
    additional_context_path: "context.md"
    initialization:
      - keys: "command+shift+p"  # Platform-specific keystrokes
        delay_ms: 100
    keystrokes:
      - keys: "command+l"
        delay_ms: 100
    options:
      enable_auto_mode: true
      continuation_prompt: "Continue?"
      initial_prompt: "Start session"
      timeout_seconds: 30
      vision_conditions:
        - file_type: "*.py"
          action: "save"
          question: "Does this code need any improvements?"
          success_keystrokes:
            - keys: "command+shift+p"
              delay_ms: 100
            - keys: "cursor-autopilot:improve"
              delay_ms: 100
          failure_keystrokes:
            - keys: "command+s"
              delay_ms: 100
```

#### Required Fields

- `os_type`: Operating system type (osx, windows, linux)
- `project_path`: Absolute path to the project directory
- `task_file_path`: Path to the task file relative to project_path
- `additional_context_path`: Path to additional context file relative to project_path
- `initialization`: List of keystrokes to initialize the platform
- `keystrokes`: List of keystrokes for automation
- `options`: Platform-specific options

### General Configuration

Global settings that apply to all platforms:

```yaml
general:
  active_platforms: ["cursor"]  # List of platforms to activate
  staggered: false  # Whether to stagger platform activation
  stagger_delay: 90  # Delay between platform activations (seconds)
  initial_delay: 10  # Initial delay before starting automation (seconds)
  send_message: true  # Whether to send messages to the IDE
  use_vision_api: false  # Whether to enable OpenAI Vision
  debug: true  # Enable debug logging
  inactivity_delay: 120  # Delay before sending inactivity prompt (seconds)
```

### Slack Integration

Configuration for Slack integration:

```yaml
slack:
  enabled: true
  bot_token: ""  # Slack bot token
  app_token: ""  # Slack app token
  channels:
    - name: "automation"
      id: ""  # Channel ID
  commands:
    - name: "enable_auto"
      description: "Enable automatic mode"
    - name: "disable_auto"
      description: "Disable automatic mode"
    - name: "screenshot"
      description: "Take a screenshot of the IDE"
    - name: "set_timeout"
      description: "Set the timeout for continuation prompts"
    - name: "set_prompt"
      description: "Set the continuation or initial prompt"
```

### OpenAI Vision Integration

Configuration for OpenAI Vision integration:

```yaml
openai:
  vision:
    enabled: false
    api_key: ""  # OpenAI API key
    model: "gpt-4-vision-preview"
    max_tokens: 300
    temperature: 0.7
    conditions:
      - file_type: "*.py"
        action: "save"
        question: "Does this code need any improvements?"
      - file_type: "*.md"
        action: "save"
        question: "Is this documentation clear and complete?"
```

## Validation Rules

1. **Platform Configuration**
   - `os_type` must be one of: osx, windows, linux
   - `project_path` must exist and be accessible
   - All required fields must be present
   - Keystroke configurations must include both `keys` and `delay_ms`
   - `delay_ms` must be a positive integer

2. **General Configuration**
   - `active_platforms` must be a list of valid platform names
   - All delay values must be positive integers
   - Boolean values must be true or false

3. **Slack Configuration**
   - If `enabled` is true, `bot_token` and `app_token` must be provided
   - Channel IDs must be valid Slack channel IDs
   - Command names must be unique

4. **OpenAI Configuration**
   - If `enabled` is true, `api_key` must be provided
   - `model` must be a valid OpenAI model name
   - `max_tokens` must be a positive integer
   - `temperature` must be between 0 and 1

## Platform-Specific Keystrokes

### macOS (osx)
- Use `command` for the Command key
- Use `shift` for the Shift key
- Use `option` for the Option key
- Use `control` for the Control key

Example: `command+shift+p`

### Windows
- Use `ctrl` for the Control key
- Use `shift` for the Shift key
- Use `alt` for the Alt key
- Use `win` for the Windows key

Example: `ctrl+shift+p`

### Linux
- Use `ctrl` for the Control key
- Use `shift` for the Shift key
- Use `alt` for the Alt key
- Use `super` for the Super key

Example: `ctrl+shift+p`

## Examples

### Basic Configuration
```yaml
platforms:
  cursor:
    os_type: osx
    project_path: "/Users/username/projects/my-project"
    task_file_path: "tasks.md"
    initialization:
      - keys: "command+shift+p"
        delay_ms: 100
    options:
      enable_auto_mode: true
      timeout_seconds: 30

general:
  active_platforms: ["cursor"]
  debug: true
```

### Multi-Platform Configuration
```yaml
platforms:
  cursor:
    os_type: osx
    project_path: "/Users/username/projects/my-project"
    initialization:
      - keys: "command+shift+p"
        delay_ms: 100
    options:
      enable_auto_mode: true

  windsurf:
    os_type: windows
    project_path: "C:\\Users\\username\\projects\\my-project"
    initialization:
      - keys: "ctrl+shift+p"
        delay_ms: 100
    options:
      enable_auto_mode: true

general:
  active_platforms: ["cursor", "windsurf"]
  staggered: true
  stagger_delay: 90
```

### Vision Integration
```yaml
platforms:
  cursor:
    os_type: osx
    options:
      vision_conditions:
        - file_type: "*.py"
          action: "save"
          question: "Does this code need any improvements?"
          success_keystrokes:
            - keys: "command+shift+p"
              delay_ms: 100
            - keys: "cursor-autopilot:improve"
              delay_ms: 100
          failure_keystrokes:
            - keys: "command+s"
              delay_ms: 100

openai:
  vision:
    enabled: true
    api_key: "your-api-key"
    model: "gpt-4-vision-preview"
```

## Troubleshooting

### Common Issues

1. **Invalid Keystrokes**
   - Ensure keystrokes match the platform's `os_type`
   - Check for typos in key names
   - Verify delay values are positive integers

2. **Path Issues**
   - Use absolute paths for `project_path`
   - Ensure paths exist and are accessible
   - Use forward slashes (/) for paths, even on Windows

3. **Integration Failures**
   - Verify API keys and tokens are correct
   - Check network connectivity
   - Ensure required services are running

4. **Platform Activation**
   - Verify platform names in `active_platforms`
   - Check platform-specific configurations
   - Ensure staggered activation settings are correct

### Debugging

1. Enable debug mode:
   ```yaml
   general:
     debug: true
   ```

2. Check logs for:
   - Configuration loading errors
   - Platform activation issues
   - Integration failures
   - Keystroke execution problems

3. Verify configuration:
   - Use a YAML validator
   - Check for syntax errors
   - Verify all required fields are present

## Best Practices

1. **Configuration Organization**
   - Group related settings together
   - Use comments to document complex configurations
   - Keep sensitive information (API keys) in environment variables

2. **Platform Configuration**
   - Use platform-specific paths and keystrokes
   - Test configurations on each target platform
   - Document platform-specific requirements

3. **Integration Settings**
   - Use environment variables for sensitive data
   - Enable features gradually
   - Monitor integration performance

4. **Maintenance**
   - Regularly review and update configurations
   - Document changes and their impact
   - Test configurations after updates 