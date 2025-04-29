# Configuration Guide (YAML)

All major settings are now controlled via `config.yaml` in the project root.

## Example `config.yaml`

```yaml
platforms:
  cursor:
    os_type: osx  # or 'windows' or 'linux'
    initialization:
      - keys: "command+shift+p"
        delay_ms: 100
    keystrokes:
      - keys: "command+l"
        delay_ms: 100
    options:
      enable_auto_mode: true
      continuation_prompt: "Continue?"
      initial_prompt: "Start session"
      timeout_seconds: 30
  windsurf:
    os_type: osx  # or 'windows' or 'linux'
    initialization:
      - keys: "command+shift+p"
        delay_ms: 100
    keystrokes:
      - keys: "command+l"
        delay_ms: 100
    options:
      enable_auto_mode: false
      continuation_prompt: "Continue?"
      initial_prompt: "Start session"
      timeout_seconds: 30

general:
  project_path: "/path/to/your/project"
  task_file_path: "tasks.md"
  additional_context_path: "context.md"
  initial_delay: 10
  send_message: true
  use_vision_api: false
  debug: true
  inactivity_delay: 120
  initial_prompt_file_path: "path/to/initial_prompt.txt"
  continuation_prompt_file_path: "path/to/continuation_prompt.txt"
```

## Configuration Options

- `platforms`: Map of platform names (`cursor`, `windsurf`) to platform-specific config. Set `os_type` to `osx`, `windows`, or `linux` as appropriate. Use the correct key syntax for each OS.
- `initialization`: List of keystrokes (with delays) to send when initializing the platform.
- `keystrokes`: List of keystrokes (with delays) for automation.
- `options`: Platform-specific options (e.g., auto mode, prompts, timeouts).
- `general`: Global settings for project path, context, delays, debug, etc.

## Migration Instructions

1. Copy the above example as `config.yaml` in your project root.
2. Remove or archive your old `config.json`.
3. Update your codebase to load configuration from YAML (using a library like `pyyaml`).
4. Adjust your automation logic to use the new config structure.

## Notes
- For Windows or Linux support, set `os_type` and use the appropriate key combinations (e.g., `ctrl+shift+p` for Windows/Linux).
- You can add more platforms or options as needed.
- All keystrokes should be listed in the order they are to be sent, with optional delays between them.

See [tasks.md](../tasks.md) for feature requirements and implementation progress.
