# Cursor Autopilot Repository Structure

## Overview
Cursor Autopilot is a tool that automates interactions with the Cursor IDE, providing features like automated prompting, file watching, and Slack integration.

## Core Components

### Main Application Files
- `src/watcher.py`: Core application logic for watching files and managing prompts
  - Contains the `CursorAutopilot` class that orchestrates the entire application
  - Handles initialization, prompt sending, and the main event loop
  - **Potential Cleanup**: Consider splitting into smaller modules for better maintainability

- `src/cli.py`: Command-line interface implementation
  - Handles argument parsing and command execution
  - **Potential Cleanup**: Could be merged with `watcher.py` since they're tightly coupled

- `src/run_both.py`: Launches both the watcher and Slack bot
  - **Potential Cleanup**: Could be simplified or moved to a more appropriate location

### Platform Interaction
- `src/actions/keystrokes.py`: Handles keyboard input simulation
  - Provides functions for sending keystrokes and text
  - **Potential Cleanup**: Consider merging with `send_to_cursor.py`

- `src/actions/send_to_cursor.py`: Manages interaction with Cursor/Windsurf
  - Handles window activation, screenshot capture, and prompt sending
  - **Potential Cleanup**: Could be split into separate modules for window management and prompt sending

- `src/automation/window.py`: Window management utilities
  - Platform-specific window activation and management
  - **Potential Cleanup**: Consider moving to `actions` directory

### File Handling
- `src/file_handling/watcher.py`: File system monitoring
  - Watches for file changes and triggers appropriate actions
  - **Potential Cleanup**: Could be simplified and better integrated with main watcher

- `src/file_handling/filters.py`: File filtering logic
  - Handles file inclusion/exclusion rules
  - **Potential Cleanup**: Could be merged with watcher.py

### Configuration
- `src/config/loader.py`: Configuration management
  - Loads and validates configuration from YAML files
  - **Potential Cleanup**: Consider adding schema validation

- `config.yaml`: Main configuration file
  - Contains platform settings, paths, and behavior configuration
  - **Potential Cleanup**: Could be split into multiple config files for different components

### Platform Management
- `src/platforms/manager.py`: Platform state management
  - Tracks platform states and manages prompt timing
  - **Potential Cleanup**: Could be simplified and better integrated with watcher

### Utilities
- `src/utils/colored_logging.py`: Logging configuration
  - Sets up colored console output for logs
  - **Potential Cleanup**: Consider using a standard logging library

- `src/state.py`: Global state management
  - Manages application-wide state
  - **Potential Cleanup**: Could be expanded to handle more state management

### Integration
- `src/slack_bot.py`: Slack integration
  - Handles Slack commands and interactions
  - **Potential Cleanup**: Could be moved to a dedicated integrations directory

### Prompt Management
- `src/generate_initial_prompt.py`: Initial prompt generation
  - Creates and manages initial prompts
  - **Potential Cleanup**: Could be merged with prompt sending logic

- `src/ensure_chat_window.py`: Chat window management
  - Ensures chat window is open and ready
  - **Potential Cleanup**: Could be merged with window management

## Scripts and Tools
- `run.sh`: Main execution script
  - Handles environment setup and application launch
  - **Potential Cleanup**: Could be simplified and better organized

## Testing
- `tests/`: Test directory
  - Contains unit tests for various components
  - **Potential Cleanup**: Could be better organized by component

## Documentation
- `README.md`: Main documentation
- `api_documentation.md`: API documentation
- `architecture.md`: System architecture documentation
- `docs/`: Additional documentation

## Potential Major Cleanup Areas

1. **Code Organization**
   - Consolidate duplicate functionality between `keystrokes.py` and `send_to_cursor.py`
   - Merge related files in the `actions` directory
   - Create a dedicated integrations directory for Slack and other integrations

2. **Configuration Management**
   - Split configuration into component-specific files
   - Add configuration validation
   - Implement configuration versioning

3. **State Management**
   - Implement a more robust state management system
   - Reduce global state usage
   - Add state persistence

4. **Testing**
   - Increase test coverage
   - Add integration tests
   - Implement automated testing

5. **Documentation**
   - Add inline code documentation
   - Create component-specific documentation
   - Add setup and troubleshooting guides

6. **Error Handling**
   - Implement consistent error handling
   - Add error recovery mechanisms
   - Improve error reporting

7. **Logging**
   - Standardize logging across components
   - Add log rotation
   - Implement structured logging

## Next Steps
1. Create a detailed cleanup plan
2. Prioritize cleanup tasks
3. Implement changes incrementally
4. Add tests for new/modified code
5. Update documentation as changes are made 