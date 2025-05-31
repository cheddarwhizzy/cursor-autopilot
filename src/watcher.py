#!/usr/bin/env python3
import time
import os
import logging
import argparse
from datetime import datetime
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
    
    return parser.parse_args()

# Import existing prompt generation logic
from src.generate_initial_prompt import (
    read_prompt_from_file,
    DEFAULT_INITIAL_PROMPT,
    DEFAULT_CONTINUATION_PROMPT
)

# Import platform interaction modules
from src.actions.send_to_cursor import send_prompt
from src.actions.keystrokes import send_keystroke, send_keystroke_string
from src.automation.window import activate_window
from src.actions.openai_vision import check_vision_conditions

# Path for the initial prompt flag file
INITIAL_PROMPT_SENT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".initial_prompt_sent"))

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
        self.initial_prompt_sent = False
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
            self.config_manager.gitignore_patterns
        )
        
        # Check if initial prompt has already been sent
        self.initial_prompt_sent = os.path.exists(INITIAL_PROMPT_SENT_FILE)
        self.logger.debug(f"Initial prompt sent file exists: {self.initial_prompt_sent}")
        
        return True
    
    def send_initial_prompts(self) -> None:
        """
        Send initial prompts to all active platforms if not already sent
        """
        if self.initial_prompt_sent:
            self.logger.info("Initial prompt file found. Skipping initial prompts/keystrokes.")
            # Ensure initial activity time is set even if skipping prompts
            current_time = time.time()
            for platform_name in self.platform_manager.platform_names:
                platform_state = self.platform_manager.get_platform_state(platform_name)
                platform_state["last_activity"] = current_time
            return
        
        self.logger.info("Initial prompt file not found. Sending initial prompts/keystrokes...")
        
        for platform_name in self.platform_manager.platform_names:
            platform_config = self.config_manager.get_platform_config(platform_name)
            platform_state = self.platform_manager.get_platform_state(platform_name)
            
            initialization = platform_config.get("initialization", [])
            options = platform_config.get("options", {})
            general_config = self.config_manager.config.get("general", {})
            
            # Get paths for prompt generation
            initial_prompt_file = platform_state.get("initial_prompt_file_path")
            task_file = platform_state.get("task_file_path")
            context_file = platform_state.get("additional_context_path")
            
            project_path = platform_state.get("project_path")
            initial_prompt_file = os.path.join(project_path, initial_prompt_file) if initial_prompt_file else None
            context_file = os.path.join(project_path, context_file) if context_file else None
            task_file = os.path.join(project_path, task_file)
            
            # Use global initial prompt setting from general config as default base
            default_initial_prompt_template = general_config.get("initial_prompt", DEFAULT_INITIAL_PROMPT)
            initial_prompt_template = read_prompt_from_file(initial_prompt_file) or default_initial_prompt_template
            self.logger.debug(f"[{platform_name}] Using initial prompt template (from file: {bool(initial_prompt_file)})")
            
            # Format the prompt
            try:
                # Make sure paths exist before formatting
                if task_file and not os.path.exists(task_file):
                    self.logger.warning(f"[{platform_name}] Task file not found: {task_file}")
                    task_file = ""
                
                if context_file and not os.path.exists(context_file):
                    self.logger.warning(f"[{platform_name}] Context file not found: {context_file}")
                    context_file = ""
                
                # Format prompt, providing empty string if files don't exist
                initial_prompt_content = initial_prompt_template.format(
                    task_file_path=task_file,
                    additional_context_path=context_file
                )
            except KeyError as e:
                self.logger.error(f"[{platform_name}] Error formatting initial prompt template (missing key {e}). Using raw template.")
                initial_prompt_content = initial_prompt_template
            
            self.logger.debug(f"[{platform_name}] Initialization config: {initialization}")
            self.logger.debug(f"[{platform_name}] Final initial_prompt content length: {len(initial_prompt_content)}")
            
            # Activate window first
            window_title = platform_state.get("window_title", platform_name)
            self.logger.info(f"[{platform_name}] Activating window for initialization: {window_title}")
            if not self.args.no_send:
                activate_window(window_title)
                time.sleep(1)  # Give time for window activation
            
            # Send initialization keystrokes
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
            elif initialization and self.args.no_send:
                self.logger.info(f"[{platform_name}] Skipping initialization keystrokes (--no-send enabled)")
            
            # Send initial prompt content
            if initial_prompt_content:
                if not self.args.no_send:
                    self.logger.info(f"[{platform_name}] Sending initial prompt content...")
                    # Activate window again just in case
                    activate_window(window_title)
                    time.sleep(0.5)
                    send_keystroke_string(initial_prompt_content, platform_name)
                    platform_state["last_activity"] = time.time()
                    platform_state["last_prompt_time"] = time.time()
                    self.platform_manager.last_global_prompt_time = time.time()
                else:
                    self.logger.info(f"[{platform_name}] Skipping initial prompt content (--no-send enabled)")
                    platform_state["last_activity"] = time.time()  # Reset timer anyway
        
        # Create the flag file after attempting for all platforms
        try:
            with open(INITIAL_PROMPT_SENT_FILE, 'w') as f:
                f.write("Initial prompt sent attempt at: " + datetime.now().isoformat())
            self.logger.info(f"Created initial prompt sent file: {INITIAL_PROMPT_SENT_FILE}")
            self.initial_prompt_sent = True
        except Exception as e:
            self.logger.error(f"Failed to create initial prompt sent file: {e}")
    
    def send_continuation_prompt(self, platform_to_prompt: dict) -> None:
        """
        Send a continuation prompt to a specific platform
        """
        platform_name = platform_to_prompt["name"]
        state = platform_to_prompt["state"]
        platform_config = platform_to_prompt["config"]
        general_config = self.config_manager.config.get("general", {})
        
        self.logger.info(f"Sending continuation prompt to platform '{platform_name}'")
        
        # Prepare continuation prompt for the selected platform
        continuation_prompt_file = state.get("continuation_prompt_file_path")
        task_file = state.get("task_file_path")
        context_file = platform_config.get("additional_context_path")
        
        project_path = state.get("project_path")
        continuation_prompt_file = os.path.join(project_path, continuation_prompt_file) if continuation_prompt_file else None
        context_file = os.path.join(project_path, context_file) if context_file else None
        task_file = os.path.join(project_path, task_file)
        
        # Determine prompt template (File > General > Default)
        continuation_prompt_template = read_prompt_from_file(continuation_prompt_file)
        source = "file"
        if not continuation_prompt_template:
            continuation_prompt_template = general_config.get("inactivity_prompt")
            source = "general config"
        if not continuation_prompt_template:
            continuation_prompt_template = DEFAULT_CONTINUATION_PROMPT
            source = "default"
        self.logger.debug(f"[{platform_name}] Using continuation prompt template from: {source}")
        
        # Format the prompt
        try:
            # Ensure paths exist before formatting
            if task_file and not os.path.exists(task_file):
                self.logger.warning(f"[{platform_name}] Task file not found for continuation prompt: {task_file}")
                task_file = ""
            
            if context_file and not os.path.exists(context_file):
                self.logger.warning(f"[{platform_name}] Context file not found for continuation prompt: {context_file}")
                context_file = ""
            
            continuation_prompt_content = continuation_prompt_template.format(
                task_file_path=task_file,
                additional_context_path=context_file
            )
        except KeyError as e:
            self.logger.error(f"[{platform_name}] Error formatting continuation prompt template (missing key {e}). Using raw template.")
            continuation_prompt_content = continuation_prompt_template
        
        self.logger.debug(f"[{platform_name}] Sending continuation prompt content (length: {len(continuation_prompt_content)})...")
        
        # Send the prompt if not in no-send mode
        if not self.args.no_send:
            window_title = state.get("window_title", platform_name)
            activate_window(window_title)
            time.sleep(0.5)
            send_keystroke_string(continuation_prompt_content, platform_name)
        else:
            self.logger.info(f"[{platform_name}] Skipping continuation prompt (--no-send enabled)")
        
        # Update timers for the prompted platform AND the global timer
        current_time = time.time()
        state["last_activity"] = current_time
        state["last_prompt_time"] = current_time
        self.platform_manager.last_global_prompt_time = current_time
        self.logger.info(f"[{platform_name}] Continuation prompt sent. Updated activity timestamps.")
    
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
            
            # Send initial prompts if needed
            self.send_initial_prompts()
            
            # Main loop
            self.logger.info("Entering main watcher loop...")
            stagger_delay = self.config_manager.config.get("general", {}).get("stagger_delay", 90)
            
            while True:
                current_time = time.time()
                
                # Check for configuration changes
                if self.config_manager.check_config_changed():
                    self.logger.info("Configuration file changed, reloading...")
                    if not self.config_manager.load_config(self.args):
                        self.logger.error("Failed to reload configuration, continuing with previous settings")
                    else:
                        stagger_delay = self.config_manager.config.get("general", {}).get("stagger_delay", 90)
                        self.logger.warning("Config reloaded, but observer paths might be stale. Restart recommended for path changes.")
                
                # Check for inactive platforms and send continuation prompts if needed
                platform_to_prompt = self.platform_manager.should_send_prompt(stagger_delay)
                if platform_to_prompt:
                    self.send_continuation_prompt(platform_to_prompt)
                
                # Sleep for a short interval
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Watcher stopping due to user interrupt (Ctrl+C)")
        except Exception as e:
            self.logger.error(f"Unhandled error in watcher main loop: {e}", exc_info=True)
        finally:
            # Clean up
            if 'file_watcher' in locals():
                file_watcher.stop_all_watchers()
            self.logger.info("Watcher finished.")

def main():
    # Parse command line arguments
    args = parse_args()
    
    # Create and run the autopilot
    autopilot = CursorAutopilot(args)
    autopilot.run()

if __name__ == "__main__":
    main()
