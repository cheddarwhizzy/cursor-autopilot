#!/usr/bin/env python3
"""
Script to specifically launch only Cursor with proper error handling.
This script focuses on a single platform to reduce complexity.
"""

import os
import sys
import time
import logging
import yaml
import subprocess
from src.utils.colored_logging import setup_colored_logging

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


def kill_cursor():
    """Kill any running Cursor processes."""
    logger.info("Checking if Cursor is running...")

    # Check if app is running
    check_script = """
    tell application "System Events"
        count (every process whose name is "Cursor")
    end tell
    """

    result = subprocess.run(
        ["osascript", "-e", check_script], capture_output=True, text=True
    )
    if result.returncode == 0 and result.stdout.strip() != "0":
        logger.info("Cursor is running, killing it...")
        subprocess.run(["pkill", "-x", "Cursor"])
        logger.info("Waiting 2 seconds for process to fully terminate...")
        time.sleep(2)  # Wait longer for process to fully terminate
        logger.info("Done.")
    else:
        logger.info("Cursor is not running.")


def launch_cursor(project_path):
    """
    Launch Cursor with the specified project path.

    Args:
        project_path: Path to the project to open
    """
    logger.info("Starting Cursor for platform cursor_meanscoop...")

    # Ensure Cursor is not already running
    kill_cursor()

    # Get list of all processes before launch
    before_cmd = ["pgrep", "Cursor"]
    before_result = subprocess.run(before_cmd, capture_output=True, text=True)
    before_pids = (
        set(before_result.stdout.strip().split("\n"))
        if before_result.stdout.strip()
        else set()
    )
    logger.debug(f"Cursor PIDs before launch: {before_pids}")

    if project_path:
        logger.info(f"Launching Cursor with project path: {project_path}")
        # Launch using open command with -n flag to ensure new instance
        result = subprocess.run(
            ["open", "-n", "-a", "Cursor", project_path], capture_output=True, text=True
        )

        if result.returncode != 0:
            logger.warning(f"Open command failed: {result.stderr}")
            logger.info("Trying to launch Cursor with AppleScript...")
            project_path_escaped = project_path.replace('"', '\\"')
            script = f"""
            tell application "Cursor" to open "{project_path_escaped}"
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error(f"AppleScript launch failed: {result.stderr}")
                return False
    else:
        logger.warning(f"No project path provided for cursor_meanscoop (Cursor)")
        result = subprocess.run(
            ["open", "-n", "-a", "Cursor"], capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(f"Failed to launch Cursor: {result.stderr}")
            return False

    # Wait for Cursor to launch
    logger.info("Waiting for Cursor process to start...")
    max_attempts = 30  # Increase max attempts to 30 seconds
    is_launched = False

    for attempt in range(max_attempts):
        time.sleep(1)

        # Use multiple ways to check if Cursor is running

        # Method 1: pgrep
        check_cmd = ["pgrep", "Cursor"]
        result = subprocess.run(check_cmd, capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            current_pids = set(result.stdout.strip().split("\n"))
            new_pids = current_pids - before_pids
            if new_pids:
                logger.info(
                    f"New Cursor process(es) found! PIDs: {', '.join(new_pids)}"
                )
                is_launched = True
                break

        # Method 2: ps with grep
        if not is_launched:
            ps_cmd = "ps -A | grep -i 'Cursor' | grep -v grep"
            ps_result = subprocess.run(
                ps_cmd, shell=True, capture_output=True, text=True
            )
            if ps_result.returncode == 0 and ps_result.stdout.strip():
                logger.info(f"Cursor process found via ps+grep")
                is_launched = True
                break

        # Method 3: check with AppleScript
        if (
            not is_launched and attempt % 5 == 0
        ):  # Only check every 5 seconds to avoid overhead
            script = """
            tell application "System Events"
                set cursorRunning to (name of processes) contains "Cursor"
                return cursorRunning
            end tell
            """
            as_result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )
            if as_result.returncode == 0 and "true" in as_result.stdout.lower():
                logger.info("Cursor process found via AppleScript")
                is_launched = True
                break

        if attempt % 5 == 0:  # Log progress every 5 seconds
            logger.info(
                f"Waiting for Cursor process... (attempt {attempt+1}/{max_attempts})"
            )

    if not is_launched:
        logger.error(f"Failed to detect Cursor process after {max_attempts} attempts.")
        logger.info("Trying to activate Cursor anyway...")
        # Try to activate Cursor even if we didn't detect it
        script = """
        tell application "Cursor"
            activate
        end tell
        """
        subprocess.run(["osascript", "-e", script])
        time.sleep(5)

        # Check one more time
        check_cmd = ["pgrep", "Cursor"]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            logger.info(
                f"Cursor process found after activation! PIDs: {result.stdout.strip()}"
            )
            is_launched = True

        if not is_launched:
            return False

    # Give extra time for Cursor to fully initialize
    logger.info("Waiting 5 seconds for Cursor to fully initialize...")
    time.sleep(5)

    # Try to activate the window
    script = """
    tell application "Cursor"
        activate
    end tell
    """
    subprocess.run(["osascript", "-e", script])

    logger.info("Cursor launched successfully!")
    return True


def main():
    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration.")
        return 1

    # Get cursor_meanscoop platform config
    platform_config = config.get("platforms", {}).get("cursor_meanscoop")
    if not platform_config:
        logger.error("No configuration found for platform: cursor_meanscoop")
        return 1

    # Get project path
    project_path = platform_config.get("project_path")
    if not project_path:
        logger.error("No project path defined for platform: cursor_meanscoop")
        return 1

    # Expand user directory
    project_path = os.path.expanduser(project_path)
    if not os.path.exists(project_path):
        logger.error(f"Project path does not exist: {project_path}")
        return 1

    # Launch Cursor
    success = launch_cursor(project_path)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
