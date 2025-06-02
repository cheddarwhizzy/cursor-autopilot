#!/usr/bin/env python3
"""
Script to launch Cursor IDE with proper platform detection.
This script directly calls the necessary Python functions without relying on the CLI.
"""

import os
import sys
import time
import logging
import yaml
from src.utils.colored_logging import setup_colored_logging
from src.platforms.manager import PlatformManager
from src.actions.send_to_cursor import launch_platform

# Configure logging
setup_colored_logging(debug=True)  # Always use debug mode for this script
logger = logging.getLogger("cursor_launcher")


def load_config():
    """Load configuration from the config.yaml file."""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Could not read config: {e}")
        return {}


def main():
    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration.")
        return 1

    # Extract active platforms from config
    active_platforms = config.get("general", {}).get("active_platforms", [])
    if not active_platforms:
        logger.error("No active platforms defined in config.yaml.")
        return 1

    logger.info(f"Found active platforms: {active_platforms}")

    # Setup platform manager with minimal config - we just need platform details
    class MinimalConfigManager:
        def __init__(self, config):
            self.config = config

        def get_active_platforms(self, args=None):
            return self.config.get("general", {}).get("active_platforms", [])

        def get_platform_config(self, platform_name):
            return self.config.get("platforms", {}).get(platform_name, {})

    config_manager = MinimalConfigManager(config)
    platform_manager = PlatformManager(config_manager)

    # Initialize platforms (but don't start watchdog)
    class DummyArgs:
        def __init__(self):
            self.project_path = None
            self.inactivity_delay = None

    dummy_args = DummyArgs()
    success = platform_manager.initialize_platforms(dummy_args)

    if not success:
        logger.error("Failed to initialize platforms.")
        return 1

    # Launch each platform
    for platform_name in active_platforms:
        platform_state = platform_manager.get_platform_state(platform_name)
        if not platform_state:
            logger.error(f"No configuration found for platform: {platform_name}")
            continue

        platform_type = platform_state.get("platform_type")
        project_path = platform_state.get("project_path")

        logger.info(
            f"Launching {platform_name} (type: {platform_type}) with project path: {project_path}"
        )

        # Launch the platform
        success = launch_platform(
            platform_name=platform_name,
            platform_type=platform_type,
            project_path=project_path,
        )

        if success:
            logger.info(f"Successfully launched {platform_name}")
        else:
            logger.error(f"Failed to launch {platform_name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
