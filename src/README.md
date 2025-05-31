# Cursor Autopilot Code Structure

This directory contains the refactored code for the Cursor Autopilot tool. The code has been organized into modules for better maintainability.

## Directory Structure

- `src/` - Main source directory
  - `watcher.py` - Main entry point for the application
  - `config/` - Configuration handling
    - `loader.py` - Handles loading and validating config
  - `platforms/` - Platform management
    - `manager.py` - Handles platform state and operations
  - `file_handling/` - File watching and filtering
    - `watcher.py` - Watchdog event handlers
    - `filters.py` - File filtering based on gitignore, etc.
  - `automation/` - UI automation
    - `window.py` - Window activation
  - `actions/` - Action handlers
    - `keystrokes.py` - Keystroke handling
    - `send_to_cursor.py` - Sending prompts to Cursor
    - `openai_vision.py` - OpenAI vision integration
  - `utils/` - Utility functions
    - `colored_logging.py` - Enhanced logging setup

## Running the Application

The application entry point is `src/watcher.py`. Run it with:

```bash
python src/watcher.py [options]
```

### Command Line Options

- `--auto` - Enable auto mode
- `--debug` - Enable debug logging
- `--no-send` - Disable sending messages
- `--project-path PATH` - Override project path from config
- `--inactivity-delay SECONDS` - Override inactivity delay in seconds
- `--platform PLATFORM[,PLATFORM...]` - Override platform(s) to use, comma-separated

## Architecture Overview

The application follows these main steps:

1. Parse command line arguments
2. Load configuration from config.yaml
3. Initialize platforms based on configuration
4. Set up file watchers for each platform
5. Send initial prompts if needed
6. Enter main loop to monitor inactivity and send prompts

## Code Structure Improvements

The code has been refactored to:

1. Separate concerns into logical modules
2. Use object-oriented design with proper class encapsulation
3. Improve error handling and logging
4. Fix indentation errors in the original code
5. Make the code more maintainable and testable

## Contributing

When adding new features or fixing bugs:

1. Keep the modular structure
2. Add appropriate logging
3. Handle errors gracefully
4. Follow the existing patterns for configuration handling
5. Update this documentation as needed 