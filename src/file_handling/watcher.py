#!/usr/bin/env python3
import os
import time
import logging
import fnmatch
from typing import Dict, Any, Optional, Tuple
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileSystemEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
    DirModifiedEvent,
)
from queue import Queue

# Import existing automation functionality
from src.actions.keystrokes import send_keystroke
from src.automation.window import activate_window
from src.file_handling.filters import FileFilter

logger = logging.getLogger('watcher.file_watcher')

class PlatformEventHandler(FileSystemEventHandler):
    """
    Handles file system events for a specific platform.
    """
    def __init__(
        self,
        platform_name: str,
        platform_state: dict,
        file_filter: FileFilter,
        logger: logging.Logger,
    ):
        self.platform_name = platform_name
        self.platform_state = platform_state
        self.file_filter = file_filter
        self.logger = logger
        self.ignored_paths = set()  # Cache for ignored paths
        self.logger.debug(f"Initialized event handler for platform: {platform_name}")

    def _should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored"""
        # Check cache first
        if path in self.ignored_paths:
            return True

        # Check if path should be ignored
        if self.file_filter.should_ignore_file(
            path, path, self.platform_state.get("project_path", "")
        ):
            self.ignored_paths.add(path)
            return True

        return False

    def _handle_event(self, event: FileSystemEvent) -> None:
        """Handle a file system event"""
        try:
            # Get relative path
            src_path = os.path.relpath(
                event.src_path, self.platform_state.get("project_path", "")
            )

            # Check if we should ignore this path before any processing
            if self._should_ignore(src_path):
                return

            # Handle different event types
            if isinstance(event, FileCreatedEvent):
                self.logger.debug(f"queue_event {event}")
                self.platform_state["event_queue"].put(event)
            elif isinstance(event, FileModifiedEvent):
                self.logger.debug(f"queue_event {event}")
                self.platform_state["event_queue"].put(event)
            elif isinstance(event, FileDeletedEvent):
                self.logger.debug(f"queue_event {event}")
                self.platform_state["event_queue"].put(event)
            elif isinstance(event, FileMovedEvent):
                self.logger.debug(f"queue_event {event}")
                self.platform_state["event_queue"].put(event)
            elif isinstance(event, DirModifiedEvent):
                self.logger.debug(f"queue_event {event}")
                self.platform_state["event_queue"].put(event)
            else:
                self.logger.debug(f"Unhandled event type: {type(event)}")

        except Exception as e:
            self.logger.error(f"Error handling event: {e}", exc_info=True)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events"""
        if not event.is_directory:
            self._handle_event(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events"""
        if not event.is_directory:
            self._handle_event(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events"""
        if not event.is_directory:
            self._handle_event(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move events"""
        if not event.is_directory:
            self._handle_event(event)


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

        # Initialize file filter
        self.file_filter = FileFilter(
            self.config_manager.exclude_dirs,
            self.config_manager.exclude_files,
            self.config_manager.gitignore_patterns,
            self.config_manager.use_gitignore,
        )

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

            # Initialize event queue for this platform
            platform_state["event_queue"] = Queue()

            event_handler = PlatformEventHandler(
                platform_name,
                platform_state,
                self.file_filter,  # Use the instance we created
                logger,
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
