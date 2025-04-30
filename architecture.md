# Project Architecture & Design Decisions

This document outlines the architectural choices and design decisions for the Cursor Autopilot project.

## Core Architecture

The system follows a modular design primarily written in Python. Key components include:

- **Watcher (`watcher.py`)**: Monitors the project directory for changes and triggers actions based on inactivity or file modifications.
- **Configuration (`config.yaml`)**: Centralized YAML file for all settings.
- **Actions (`actions/`)**: Modules responsible for interacting with IDEs (Cursor/Windsurf) and external services (Slack, OpenAI).
- **State Management (`state.py`)**: Handles the current operational mode (auto/manual).
- **CLI Handling**: Manages command-line arguments for configuration overrides.

## Cross-Platform Keystroke Support

**Goal**: Ensure keystroke automation works reliably on macOS, Windows, and Linux.

**Library**: `pyautogui`
  - **Reasoning**: `pyautogui` is a well-maintained, cross-platform library for GUI automation, including sending keyboard inputs.

**Implementation Plan**:
1.  **Add Dependency**: Include `pyautogui` in `requirements.txt`.
2.  **Keystroke Sending Module**: Modify the existing keystroke sending logic (likely in `actions/send_to_cursor.py` or a similar module) to use `pyautogui.hotkey()` or `pyautogui.press()`.
3.  **Platform Detection**: Use Python's `platform.system()` to detect the current operating system (e.g., 'Darwin' for macOS, 'Windows', 'Linux').
4.  **Key Mapping**: Implement a mapping mechanism. When a keystroke sequence is loaded from `config.yaml` (e.g., `command+shift+p`):
    - If the detected OS is Windows or Linux, replace `command` with `ctrl`.
    - Pass the mapped keys to `pyautogui.hotkey()`.
    - Example mapping function:
      ```python
      import platform
      import pyautogui

      def send_cross_platform_hotkey(keys_string: str):
          os_name = platform.system().lower()
          key_parts = keys_string.split('+')
          
          mapped_keys = []
          for key in key_parts:
              if key == 'command':
                  if os_name == 'windows' or os_name == 'linux':
                      mapped_keys.append('ctrl')
                  else: # macOS
                      mapped_keys.append('command') # Or potentially 'cmd' depending on pyautogui specifics
              else:
                  mapped_keys.append(key)
          
          pyautogui.hotkey(*mapped_keys)
      ```
5.  **Configuration**: The `config.yaml` will continue to use generic keys like `command`. The `os_type` field within each platform's configuration will primarily be for documentation and potential future OS-specific logic, but the core mapping will rely on `platform.system()`.
6.  **Testing**: Thoroughly test the key combinations defined in `config.yaml` on macOS, a Windows VM/machine, and a Linux VM/machine.

## Command-Line Argument Overrides

**Goal**: Allow users to override settings from `config.yaml` via CLI flags for flexibility.

**Library**: Python's built-in `argparse` module.
  - **Reasoning**: `argparse` is the standard, robust way to handle command-line arguments in Python. It avoids complex shell scripting for parsing.

**Implementation Plan**:
1.  **Argument Parsing Logic**: Integrate `argparse` into the main entry point script (e.g., a new `main.py` or within `watcher.py` if it becomes the main executable).
2.  **Define Arguments**: Define arguments corresponding to the overridable settings in `config.yaml`. Use descriptive names.
    ```python
    import argparse

    parser = argparse.ArgumentParser(description='Cursor Autopilot')
    parser.add_argument('--project-path', type=str, 
                        help='Override project path from config.yaml')
    parser.add_argument('--platform', type=str, 
                        help='Override active platforms (comma-separated, e.g., \"cursor,windsurf\")')
    parser.add_argument('--debug', action='store_true', 
                        help='Enable debug logging')
    parser.add_argument('--inactivity-delay', type=int, 
                        help='Override inactivity delay in seconds from config.yaml')
    parser.add_argument('--send-message', dest='send_message', action='store_true', 
                        help='Force sending messages to the IDE')
    parser.add_argument('--no-send-message', dest='send_message', action='store_false',
                         help='Force disabling sending messages to the IDE')
    parser.set_defaults(send_message=None) # Default based on config file
    # ... add other arguments as needed ...

    args = parser.parse_args()
    ```
3.  **Loading Order**: 
    - First, load the base configuration from `config.yaml`.
    - Then, parse the command-line arguments using `parser.parse_args()`.
    - Iterate through the parsed arguments (`vars(args)`). If an argument's value is not `None` (or the default for boolean flags), update the corresponding key in the loaded configuration dictionary. Special handling for `platform` to split the comma-separated string into a list.
4.  **Update `run.sh`**: Modify `run.sh` to simply execute the main Python script, passing along all shell arguments: `python main.py "$@"`.
5.  **Help Message**: `argparse` automatically generates a helpful message when the user runs the script with `-h` or `--help`.

## Future Considerations
- **Error Handling**: Enhance error handling for `pyautogui` failures (e.g., if GUI access is restricted).
- **Dependency Management**: Ensure cross-platform dependencies for `pyautogui` are documented (e.g., `python3-tk`, `python3-dev`, `libxtst-dev` on Linux).
- **Configuration Schema Validation**: Implement more robust schema validation for `config.yaml` using libraries like `PyYAML` with `jsonschema` or `pydantic`. 