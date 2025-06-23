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
from src.config.loader import load_gitignore_patterns

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

        # Get relative path from project root
        project_path = self.platform_state.get("project_path", "")
        try:
            rel_path = os.path.relpath(path, project_path)
        except (ValueError, AttributeError):
            rel_path = path

        # Check if path should be ignored
        if self.file_filter.should_ignore_file(path, rel_path, project_path):
            self.ignored_paths.add(path)
            self.logger.debug(f"[{self.platform_name}] Ignoring file: {rel_path}")
            return True

        return False

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events"""
        if not event.is_directory and not self._should_ignore(event.src_path):
            self.logger.debug(f"queue_event {event}")
            self.platform_state["event_queue"].put(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events"""
        if not event.is_directory and not self._should_ignore(event.src_path):
            self.logger.debug(f"queue_event {event}")
            self.platform_state["event_queue"].put(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events"""
        if not event.is_directory and not self._should_ignore(event.src_path):
            self.logger.debug(f"queue_event {event}")
            self.platform_state["event_queue"].put(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move events"""
        if not event.is_directory:
            # Check both source and destination paths for moved events
            if not self._should_ignore(event.src_path) and not self._should_ignore(
                getattr(event, "dest_path", event.src_path)
            ):
                self.logger.debug(f"queue_event {event}")
                self.platform_state["event_queue"].put(event)


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
        self.platform_file_filters = {}  # Track file filters per platform

    def _create_file_filter_for_platform(
        self, platform_name: str, project_path: str
    ) -> FileFilter:
        """
        Create a FileFilter instance for a specific platform with its own gitignore patterns
        """
        # Load gitignore patterns specific to this project
        gitignore_patterns = set()
        if self.config_manager.use_gitignore:
            gitignore_patterns = load_gitignore_patterns(project_path)
            logger.info(
                f"[{platform_name}] Loaded {len(gitignore_patterns)} gitignore patterns from {project_path}"
            )
        else:
            logger.debug(f"[{platform_name}] Gitignore patterns disabled")

        # Create file filter with platform-specific patterns
        file_filter = FileFilter(
            self.config_manager.exclude_dirs,
            self.config_manager.exclude_files,
            gitignore_patterns,
            self.config_manager.use_gitignore,
        )
        return file_filter

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

            # Create platform-specific file filter
            file_filter = self._create_file_filter_for_platform(
                platform_name, project_path
            )
            self.platform_file_filters[platform_name] = file_filter

            # Initialize event queue for this platform
            platform_state["event_queue"] = Queue()

            event_handler = PlatformEventHandler(
                platform_name,
                platform_state,
                file_filter,
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

        # Wait for all observers to stop
        for observer in self.observers:
            try:
                observer.join()
            except Exception as e:
                logger.error(f"Error joining observer: {e}")

        logger.info("All watchers stopped.")

    def is_alive(self) -> bool:
        """
        Check if any observers are still alive
        """
        return any(observer.is_alive() for observer in self.observers)
