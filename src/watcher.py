#!/usr/bin/env python3.13
import sys
import time
import os
import hashlib
import json
from datetime import datetime
from src.actions.send_to_cursor import (
    send_prompt,
    launch_platform,
    activate_platform_window,
)
from src.state import get_mode
from src.generate_initial_prompt import DEFAULT_CONTINUATION_PROMPT
import logging
from src.utils.colored_logging import setup_colored_logging
import argparse
from typing import Dict, List, Optional, Tuple

# Import from modules
from src.utils.colored_logging import setup_colored_logging
from src.config.loader import ConfigManager
from src.platforms.manager import PlatformManager
from src.file_handling.watcher import FileWatcherManager
from src.file_handling.filters import FileFilter

# Initialize parser
def parse_args():
    parser = argparse.ArgumentParser(description='Cursor Autopilot Watcher')
    parser.add_argument('--auto', action='store_true', help='Enable auto mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--no-send', action='store_true', help='Disable sending messages')
    parser.add_argument('--project-path', type=str, help='Override project path from config')
    parser.add_argument('--inactivity-delay', type=int, help='Override inactivity delay in seconds')
    parser.add_argument('--platform', type=str, help='Override platform to use (comma separated for multiple)')
    parser.add_argument('--task-file-path', type=str, help='Override task file path from config')
    parser.add_argument('--additional-context-path', type=str, help='Override additional context path from config')
    parser.add_argument('--continuation-prompt', type=str, help='Override continuation prompt text')
    parser.add_argument('--initial-prompt', type=str, help='Override initial prompt text')
    
    return parser.parse_args()

# Import existing prompt generation logic
from src.generate_initial_prompt import (
    read_prompt_from_file,
    DEFAULT_INITIAL_PROMPT,
    DEFAULT_CONTINUATION_PROMPT
)

# Import platform interaction modules
from src.actions.keystrokes import send_keystroke, send_keystroke_string
from src.automation.window import activate_window
from src.actions.openai_vision import check_vision_conditions

# Path for the initial prompt flag file
INITIAL_PROMPT_SENT_FILE = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".initial_prompt_sent")
)

class CursorAutopilot:
    """
    Main class for Cursor Autopilot functionality
    """
    def __init__(self, args):
        self.args = args

        # Configure logging
        setup_colored_logging(debug=args.debug or True)  # Always enable debug logging for now
        self.logger = logging.getLogger('watcher')
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug("CursorAutopilot initialization started")

        # Initialize managers
        self.config_manager = ConfigManager()
        self.platform_manager = PlatformManager(self.config_manager)

        # Initialize trackers
        self.initial_prompt_sent = False  # Will be set in initialize()
        self.file_filter = None

        # Log command line arguments
        self._log_command_line_args()

    def _log_command_line_args(self):
        """Log all command line arguments"""
        if self.args.project_path:
            self.logger.info(f"Command line project path override: {self.args.project_path}")
        if self.args.auto:
            self.logger.info("Auto mode enabled")
        if self.args.no_send:
            self.logger.info("Message sending disabled")
        if self.args.inactivity_delay:
            self.logger.info(f"Inactivity delay override: {self.args.inactivity_delay} seconds")
        if self.args.platform:
            self.logger.info(f"Platform override: {self.args.platform}")

    def initialize(self) -> bool:
        """
        Initialize the application: load config, set up platforms, etc.
        Returns True if successful, False otherwise
        """
        # Load configuration
        if not self.config_manager.load_config(self.args):
            self.logger.error("Failed to load initial configuration. Exiting.")
            return False

        # Initialize platform state
        if not self.platform_manager.initialize_platforms(self.args):
            self.logger.error("Failed to initialize platforms. Exiting.")
            return False

        # Initialize file filter
        self.file_filter = FileFilter(
            self.config_manager.exclude_dirs,
            self.config_manager.exclude_files,
            self.config_manager.gitignore_patterns,
            self.config_manager.use_gitignore,
        )

        # Check for initial prompt sent file in both workspace root and project directory
        workspace_flag = os.path.exists(INITIAL_PROMPT_SENT_FILE)
        project_flag = False

        # Check in project directory for each platform
        for platform_name in self.platform_manager.platform_names:
            platform_state = self.platform_manager.get_platform_state(platform_name)
            project_path = platform_state.get("project_path")
            if project_path:
                project_flag_path = os.path.join(project_path, ".initial_prompt_sent")
                if os.path.exists(project_flag_path):
                    project_flag = True
                    self.logger.debug(
                        f"Found .initial_prompt_sent in project directory: {project_flag_path}"
                    )
                    break

        self.initial_prompt_sent = workspace_flag or project_flag
        self.logger.debug(
            f"Initial prompt sent file exists: {self.initial_prompt_sent} (workspace: {workspace_flag}, project: {project_flag})"
        )

        return True

    def _process_file_events(self) -> None:
        """
        Process file events from all platform event queues and update activity timers
        """
        for platform_name in self.platform_manager.platform_names:
            platform_state = self.platform_manager.get_platform_state(platform_name)
            event_queue = platform_state.get("event_queue")
            
            if not event_queue:
                continue
                
            events_processed = 0
            # Process all pending events
            while not event_queue.empty():
                try:
                    event = event_queue.get_nowait()
                    events_processed += 1
                    
                    # Get relative path for logging
                    project_path = platform_state.get("project_path", "")
                    try:
                        rel_path = os.path.relpath(event.src_path, project_path)
                    except (ValueError, AttributeError):
                        rel_path = str(event.src_path)
                    
                    self.logger.debug(f"[{platform_name}] File activity detected: {event.event_type} - {rel_path}")
                    
                    # Update activity timer - this resets the inactivity countdown
                    self.platform_manager.update_activity(platform_name)
                    
                except Exception as e:
                    self.logger.error(f"Error processing file event for {platform_name}: {e}")
                    break
            
            if events_processed > 0:
                self.logger.info(f"[{platform_name}] Processed {events_processed} file events - activity timer reset")

    def send_prompt(self, platform_to_prompt: dict = None) -> None:
        """
        Send either initial or continuation prompt to platforms
        Args:
            platform_to_prompt: Optional dict containing platform info for continuation prompt
        """
        self.logger.debug(f"send_prompt called with platform_to_prompt={platform_to_prompt}")
        if platform_to_prompt:
            # Continuation prompt for specific platform
            platform_name = platform_to_prompt["name"]
            state = platform_to_prompt["state"]
            platform_config = platform_to_prompt["config"]
            platforms_to_process = [(platform_name, state, platform_config)]
            self.logger.info(
                f"Sending continuation prompt to platform '{platform_name}'"
            )
        else:
            # Initial prompts for all platforms
            self.logger.debug(f"self.initial_prompt_sent={self.initial_prompt_sent}")
            if self.initial_prompt_sent:
                self.logger.info("Initial prompt file found. Skipping initial prompts.")
                return
            self.logger.info("Sending initial prompts to all platforms...")
            platforms_to_process = [
                (
                    name,
                    self.platform_manager.get_platform_state(name),
                    self.config_manager.get_platform_config(name),
                )
                for name in self.platform_manager.platform_names
            ]

        for platform_name, state, platform_config in platforms_to_process:
            self.logger.debug(f"Processing platform: {platform_name}, state: {state}, config: {platform_config}")
            # Get initialization delay
            initialization_delay = platform_config.get(
                "initialization_delay_seconds", 8
            )
            self.logger.info(
                f"[{platform_name}] Waiting {initialization_delay} seconds for initialization..."
            )
            time.sleep(initialization_delay)

            # Send initialization keystrokes
            initialization = platform_config.get("initialization", [])
            if initialization and not self.args.no_send:
                self.logger.info(f"[{platform_name}] Sending initialization keystrokes...")
                for keystroke in initialization:
                    keys = keystroke.get("keys", "")
                    delay_ms = keystroke.get("delay_ms", 0)
                    if keys:
                        self.logger.debug(f"[{platform_name}] Sending init key: {keys}")
                        if delay_ms > 0:
                            time.sleep(delay_ms / 1000.0)
                        send_keystroke(keys, platform_name)

            # Get paths for prompt generation
            prompt_file = state.get(
                "initial_prompt_file_path"
                if not platform_to_prompt
                else "continuation_prompt_file_path"
            )
            task_file = state.get("task_file_path")
            context_file = platform_config.get("additional_context_path")

            project_path = state.get("project_path")
            prompt_file = (
                os.path.join(project_path, prompt_file) if prompt_file else None
            )
            context_file = (
                os.path.join(project_path, context_file) if context_file else None
            )
            task_file = os.path.join(project_path, task_file) if task_file else None

            # Get appropriate prompt template
            general_config = self.config_manager.config.get("general", {})
            if not platform_to_prompt:
                # Initial prompt
                if hasattr(self.args, 'initial_prompt') and self.args.initial_prompt:
                    # Use command line override if provided
                    prompt_template = self.args.initial_prompt
                    self.logger.info("Using initial prompt from command line argument")
                else:
                    # Otherwise use the one from config file or default
                    default_template = general_config.get(
                        "initial_prompt", DEFAULT_INITIAL_PROMPT
                    )
                    prompt_template = read_prompt_from_file(prompt_file) or default_template
            else:
                # Continuation prompt
                if hasattr(self.args, 'continuation_prompt') and self.args.continuation_prompt:
                    # Use command line override if provided
                    prompt_template = self.args.continuation_prompt
                    self.logger.info("Using continuation prompt from command line argument")
                else:
                    # Otherwise use the one from config file or default
                    default_template = general_config.get(
                        "inactivity_prompt", DEFAULT_CONTINUATION_PROMPT
                    )
                    prompt_template = read_prompt_from_file(prompt_file) or default_template

            self.logger.debug(f"Prompt template for {platform_name}: {prompt_template}")

            # Format the prompt
            try:
                # Check if we're using overrides for task file and context file
                platform_state = self.platform_manager.get_platform_state(platform_name)
                # Use overridden paths if available, otherwise use the ones from the template
                task_file_to_use = platform_state.get("task_file_path") or task_file
                context_file_to_use = platform_state.get("additional_context_path") or context_file
                # Check if files exist and log warnings if they don't
                if task_file_to_use and not os.path.exists(task_file_to_use):
                    self.logger.warning(
                        f"[{platform_name}] Task file not found: {task_file_to_use}"
                    )
                    task_file_to_use = ""
                if context_file_to_use and not os.path.exists(context_file_to_use):
                    self.logger.warning(
                        f"[{platform_name}] Context file not found: {context_file_to_use}"
                    )
                    context_file_to_use = ""
                # Format the prompt with the appropriate file paths
                prompt_content = prompt_template.format(
                    task_file_path=task_file_to_use or "",
                    additional_context_path=context_file_to_use or "",
                )
                self.logger.debug(f"Formatted prompt content for {platform_name}: {prompt_content}")
            except KeyError as e:
                self.logger.error(
                    f"[{platform_name}] Error formatting prompt template (missing key {e}). Using raw template."
                )
                prompt_content = prompt_template

            # Send the prompt if not in no-send mode
            if not self.args.no_send:
                self.logger.debug(f"About to activate platform window for {platform_name}")
                activation_success = activate_platform_window(platform_name, state)
                if not activation_success:
                    self.logger.warning(
                        f"Failed to activate platform window for {platform_name}, but continuing to send prompt"
                    )
                else:
                    self.logger.debug(f"Successfully activated platform window for {platform_name}")
                
                # Add a small delay regardless of activation success
                time.sleep(1.0)
                
                self.logger.debug(f"Sending keystroke string to {platform_name}: {prompt_content[:100]}...")
                send_keystroke_string(
                    prompt_content,
                    platform_name,
                    send_message=not self.args.no_send,
                )
            else:
                self.logger.info(
                    f"[{platform_name}] Skipping prompt (--no-send enabled)"
                )

            # Update timers
            current_time = time.time()
            state["last_activity"] = current_time
            state["last_prompt_time"] = current_time
            self.platform_manager.last_global_prompt_time = current_time

        # Create the flag file after sending initial prompts
        if not platform_to_prompt and not self.initial_prompt_sent:
            try:
                with open(INITIAL_PROMPT_SENT_FILE, "w") as f:
                    f.write(
                        "Initial prompt sent attempt at: " + datetime.now().isoformat()
                    )
                self.logger.info(
                    f"Created initial prompt sent file: {INITIAL_PROMPT_SENT_FILE}"
                )
                self.initial_prompt_sent = True
            except Exception as e:
                self.logger.error(f"Failed to create initial prompt sent file: {e}")

    def run(self) -> None:
        """
        Main execution loop
        """
        try:
            # Initialize
            if not self.initialize():
                self.logger.error("Initialization failed. Exiting.")
                return

            # Set up file watchers
            file_watcher = FileWatcherManager(
                self.platform_manager,
                self.config_manager,
                check_vision_conditions,  # Pass the vision checker function
                self.args
            )

            if not file_watcher.setup_watchers():
                self.logger.error("Failed to set up file watchers. Exiting.")
                return

            # Start watchers
            file_watcher.start_all_watchers()

            # Launch platforms first
            for platform_name in self.platform_manager.platform_names:
                platform_state = self.platform_manager.get_platform_state(platform_name)
                platform_type = platform_state.get("platform_type", platform_name)
                project_path = platform_state.get("project_path")
                self.logger.info(
                    f"Launching {platform_name} (type: {platform_type}) with project path: {project_path}"
                )
                if not launch_platform(platform_name, platform_type, project_path):
                    self.logger.error(f"Failed to launch {platform_name}")
                    return

            # Check if initial prompt has been sent
            if self.initial_prompt_sent:
                self.logger.info(
                    "Initial prompt file found. Sending continuation prompt..."
                )
                # Send continuation prompt to all platforms
                for platform_name in self.platform_manager.platform_names:
                    platform_state = self.platform_manager.get_platform_state(
                        platform_name
                    )
                    platform_config = self.config_manager.get_platform_config(
                        platform_name
                    )
                    platform_to_prompt = {
                        "name": platform_name,
                        "state": platform_state,
                        "config": platform_config,
                    }
                    self.send_prompt(platform_to_prompt)
            else:
                # Send initial prompts
                self.send_prompt()

            # Main loop
            self.logger.info("Entering main watcher loop...")
            stagger_delay = self.config_manager.config.get("general", {}).get("stagger_delay", 90)
            inactivity_delay = self.config_manager.config.get("general", {}).get(
                "inactivity_delay", 120
            )
            last_countdown_log = 0  # Track when we last logged the countdown

            while True:
                current_time = time.time()

                # Process file events to update activity timers
                self._process_file_events()

                # Check for configuration changes
                if self.config_manager.check_config_changed():
                    self.logger.info("Configuration file changed, reloading...")
                    if not self.config_manager.load_config(self.args):
                        self.logger.error("Failed to reload configuration, continuing with previous settings")
                    else:
                        stagger_delay = self.config_manager.config.get("general", {}).get("stagger_delay", 90)
                        inactivity_delay = self.config_manager.config.get(
                            "general", {}
                        ).get("inactivity_delay", 120)
                        self.logger.warning("Config reloaded, but observer paths might be stale. Restart recommended for path changes.")

                # Check for inactive platforms and send continuation prompts if needed
                self.logger.debug("Checking if continuation prompt should be sent...")
                platform_to_prompt = self.platform_manager.should_send_prompt(stagger_delay)
                self.logger.debug(f"should_send_prompt returned: {platform_to_prompt}")
                if platform_to_prompt:
                    self.logger.info(
                        f"Sending continuation prompt to platforms: {platform_to_prompt}"
                    )
                    self.send_prompt(platform_to_prompt)
                # Sleep for a short while to prevent high CPU usage
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            return
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
            return


def main():
    """Main entry point for the script."""
    args = parse_args()
    autopilot = CursorAutopilot(args)
    
    if not autopilot.initialize():
        autopilot.logger.error("Failed to initialize CursorAutopilot")
        return 1
    
    try:
        autopilot.run()
    except KeyboardInterrupt:
        autopilot.logger.info("Shutdown requested by user")
    except Exception as e:
        autopilot.logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())