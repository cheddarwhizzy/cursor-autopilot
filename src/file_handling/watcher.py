#!/usr/bin/env python3
import os
import time
import logging
from typing import Dict, Any, Optional, Tuple
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# Import existing automation functionality
from src.actions.keystrokes import send_keystroke
from src.automation.window import activate_window

logger = logging.getLogger('watcher.file_watcher')

class PlatformEventHandler(FileSystemEventHandler):
    """
    Handles file system events for a specific platform.
    """
    def __init__(self, platform_name, platform_manager, config_manager, vision_checker=None, args=None):
        self.platform_name = platform_name
        self.platform_manager = platform_manager
        self.config_manager = config_manager
        self.vision_checker = vision_checker  # Function to check vision conditions
        self.args = args
        logger.debug(f"Initialized event handler for platform: {self.platform_name}")

    def on_any_event(self, event: FileSystemEvent) -> None:
        """
        Handle any file system event (create, modify, delete, move)
        """
        # Ignore directory events for simplicity, focus on file changes
        if event.is_directory:
            return

        src_path = event.src_path
        event_type = event.event_type  # 'modified', 'created', 'deleted', 'moved'
        platform_state = self.platform_manager.get_platform_state(self.platform_name)
        platform_config = self.config_manager.get_platform_config(self.platform_name)

        if not platform_state or not platform_config:
            logger.warning(f"[{self.platform_name}] State or config not found for event: {src_path}")
            return

        project_path = platform_state.get("project_path")
        if not project_path:
            logger.warning(f"[{self.platform_name}] Project path not found in state for event: {src_path}")
            return

        # Calculate relative path - ensure it's within the project path
        try:
            # Ensure src_path is absolute for relpath calculation if it isn't already
            abs_src_path = os.path.abspath(src_path)
            if not abs_src_path.startswith(os.path.abspath(project_path)):
                logger.debug(f"[{self.platform_name}] Event path {abs_src_path} outside project path {project_path}")
                return  # Event is outside this platform's project directory
            rel_path = os.path.relpath(abs_src_path, project_path)
        except ValueError:
            logger.warning(f"[{self.platform_name}] Could not determine relative path for {src_path} against {project_path}")
            return

        # Check if the file should be ignored using a helper function
        if self._should_ignore_file(abs_src_path, rel_path, project_path):
            logger.debug(f"[{self.platform_name}] Ignoring event for file: {rel_path}")
            return

        logger.info(f"[{self.platform_name}] File event {event_type}: {rel_path}")

        # Update last activity time for this platform
        self.platform_manager.update_activity(self.platform_name)
        
        # Check vision conditions if file was modified or created and vision checking is enabled
        if event_type in ['modified', 'created'] and self.vision_checker:
            self._handle_vision_check(abs_src_path, event_type, rel_path)

    def _handle_vision_check(self, abs_src_path: str, event_type: str, rel_path: str) -> None:
        """
        Handle vision checking for modified or created files
        """
        # Skip if no vision checker
        if not self.vision_checker:
            return
            
        # Call the vision condition checker
        vision_result = self.vision_checker(abs_src_path, event_type, self.platform_name)
        if vision_result:
            question, keystrokes = vision_result
            logger.info(f"[{self.platform_name}] Vision analysis triggered for {rel_path}")
            logger.info(f"[{self.platform_name}] Vision Question: {question}")
            
            # Activate window before sending vision keystrokes
            platform_state = self.platform_manager.get_platform_state(self.platform_name)
            window_title = platform_state.get("window_title", self.platform_name)
            logger.info(f"[{self.platform_name}] Activating window for vision keystrokes: {window_title}")
            
            if not self.args or not self.args.no_send:
                activate_window(window_title)
                time.sleep(0.5)  # Give time for activation

                logger.info(f"[{self.platform_name}] Sending vision result keystrokes...")
                for keystroke in keystrokes:
                    keys = keystroke.get("keys", "")
                    delay_ms = keystroke.get("delay_ms", 0)
                    if keys:
                        if delay_ms > 0:
                            time.sleep(delay_ms / 1000.0)
                        # Send keystroke using the platform name for context
                        send_keystroke(keys, self.platform_name)
                    else:
                        logger.warning(f"[{self.platform_name}] Vision keystroke entry missing 'keys': {keystroke}")
            else:
                logger.info(f"[{self.platform_name}] Skipping vision keystrokes (--no-send enabled)")

    def _should_ignore_file(self, file_path: str, rel_path: str, platform_path: str) -> bool:
        """
        Check if a file should be ignored (placeholder - should use FileFilter in practice)
        """
        # This is just a temporary implementation - in practice, should use the FileFilter class
        # to maintain consistency with other file filtering logic
        exclude_dirs = {"node_modules", ".git", "dist", "__pycache__", ".idea", "venv", ".env"}
        exclude_files = {'*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.exe', '*.tmp', '*.log', '*.swp', '*.swo'}
        
        # Skip files in excluded directories
        for exclude_dir in exclude_dirs:
            if exclude_dir in file_path.split(os.sep):
                return True
        
        # Skip excluded file types
        for pattern in exclude_files:
            if pattern.startswith('*.'):
                ext = pattern[1:]  # Remove the * to get just the extension pattern
                if file_path.endswith(ext):
                    return True
                    
        return False

class FileWatcherManager:
    """
    Manager class for setting up and controlling file watchers for multiple platforms
    """
    def __init__(self, platform_manager, config_manager, vision_checker=None, args=None):
        self.platform_manager = platform_manager
        self.config_manager = config_manager
        self.vision_checker = vision_checker
        self.args = args
        self.observers = []  # Track all observers
        
    def setup_watchers(self) -> bool:
        """
        Set up file watchers for all active platforms
        Returns True if successful
        """
        platform_names = self.platform_manager.platform_names
        
        if not platform_names:
            logger.error("No active platforms to watch")
            return False
            
        for platform_name in platform_names:
            platform_state = self.platform_manager.get_platform_state(platform_name)
            project_path = platform_state.get("project_path")
            
            if not project_path or not os.path.isdir(project_path):
                logger.error(f"[{platform_name}] Invalid project path: {project_path}. Skipping observer setup.")
                continue
                
            logger.info(f"[{platform_name}] Setting up file watcher for path: {project_path}")
            event_handler = PlatformEventHandler(
                platform_name, 
                self.platform_manager, 
                self.config_manager,
                self.vision_checker,
                self.args
            )
            observer = Observer()
            observer.schedule(event_handler, project_path, recursive=True)
            
            # Store observer and handler in platform state
            platform_state["observer"] = observer
            platform_state["watch_handler"] = event_handler
            
            self.observers.append(observer)
            logger.debug(f"[{platform_name}] Observer scheduled.")
            
        if not self.observers:
            logger.error("No valid observers could be scheduled")
            return False
            
        return True
        
    def start_all_watchers(self) -> None:
        """
        Start all configured observers
        """
        for observer in self.observers:
            try:
                observer.start()
            except Exception as e:
                logger.error(f"Error starting observer: {e}")
        
        logger.info(f"Started {len(self.observers)} file watcher observers")
        
    def stop_all_watchers(self) -> None:
        """
        Stop all active observers
        """
        logger.info("Stopping all watchers...")
        for observer in self.observers:
            try:
                observer.stop()
                logger.debug(f"Observer stopped: {observer}")
            except Exception as e:
                logger.error(f"Error stopping observer: {e}")
        
        # Wait for observer threads to finish
        for observer in self.observers:
            try:
                observer.join()
                logger.debug(f"Observer joined: {observer}")
            except Exception as e:
                logger.error(f"Error joining observer: {e}")
                
        logger.info("All watcher observers stopped and joined.")
        
    def is_alive(self) -> bool:
        """
        Check if any observers are still alive
        """
        for observer in self.observers:
            if observer.is_alive():
                return True
        return False 