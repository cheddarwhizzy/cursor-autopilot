#!/usr/bin/env python3
"""
Script to specifically launch only WindSurf with proper error handling.
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
logger = logging.getLogger("windsurf_launcher")


def load_config():
    """Load configuration from the config.yaml file."""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Could not read config: {e}")
        return {}


def kill_windsurf():
    """Kill any running WindSurf processes."""
    logger.info("Checking if WindSurf is running...")

    # Check if app is running - use multiple variations of the name
    for app_name in ["WindSurf", "Windsurf", "windsurf"]:
        check_script = f"""
        tell application "System Events"
            count (every process whose name is "{app_name}")
        end tell
        """

        result = subprocess.run(
            ["osascript", "-e", check_script], capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip() != "0":
            logger.info(f"{app_name} is running, killing it...")
            subprocess.run(["pkill", "-x", app_name])
            logger.info("Waiting 2 seconds for process to fully terminate...")
            time.sleep(2)  # Wait longer for process to fully terminate
            logger.info("Done.")
            return

    logger.info("WindSurf is not running.")


def launch_windsurf(project_path):
    """
    Launch WindSurf with the specified project path.

    Args:
        project_path: Path to the project to open
    """
    logger.info("Starting WindSurf for platform windsurf_mushattention...")

    # Ensure WindSurf is not already running
    kill_windsurf()

    # Get list of processes before launch using ps command to capture all variants
    before_processes = subprocess.run(
        ["ps", "-A"], capture_output=True, text=True
    ).stdout.lower()
    logger.debug(
        f"Processes containing 'windsurf' before launch: {before_processes.count('windsurf')}"
    )

    if project_path:
        logger.info(f"Launching WindSurf with project path: {project_path}")
        # Launch using open command with -n flag to ensure new instance
        app_name = "WindSurf"  # Use proper capitalization
        result = subprocess.run(
            ["open", "-n", "-a", app_name, project_path], capture_output=True, text=True
        )

        if result.returncode != 0:
            logger.warning(f"Open command failed: {result.stderr}")
            logger.info("Trying to launch WindSurf with AppleScript...")
            project_path_escaped = project_path.replace('"', '\\"')
            script = f"""
            tell application "WindSurf" to open "{project_path_escaped}"
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error(f"AppleScript launch failed: {result.stderr}")
                return False
    else:
        logger.warning(
            f"No project path provided for windsurf_mushattention (WindSurf)"
        )
        result = subprocess.run(
            ["open", "-n", "-a", "WindSurf"], capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(f"Failed to launch WindSurf: {result.stderr}")
            return False

    # Wait for WindSurf to launch - increase timeout for WindSurf which is slower to start
    logger.info("Waiting for WindSurf process to start...")
    max_attempts = 60  # Give WindSurf more time to start (up to 60 seconds)
    is_launched = False

    # Check using multiple methods
    for attempt in range(max_attempts):
        time.sleep(1)

        # Log progress periodically
        if attempt % 5 == 0:
            logger.info(
                f"Waiting for WindSurf process... (attempt {attempt+1}/{max_attempts})"
            )

        # Method 1: ps with grep - WindSurf might appear with different capitalizations
        ps_cmd = "ps -A | grep -i 'windsurf' | grep -v grep"
        ps_result = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True)
        if ps_result.returncode == 0 and ps_result.stdout.strip():
            if (
                len(ps_result.stdout.strip().split("\n")) > 3
            ):  # WindSurf usually has multiple processes
                logger.info(f"WindSurf process found with multiple processes")
                is_launched = True
                break

        # Method 2: Check Applications folder
        if attempt % 10 == 0:  # Check less frequently as it's expensive
            script = """
            tell application "System Events"
                set allProcesses to name of every process
                set windsurfFound to false
                repeat with processName in allProcesses
                    if processName contains "WindSurf" or processName contains "Windsurf" or processName contains "windsurf" then
                        set windsurfFound to true
                        exit repeat
                    end if
                end repeat
                return windsurfFound as string
            end tell
            """
            as_result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )
            if as_result.returncode == 0 and "true" in as_result.stdout.lower():
                logger.info("WindSurf process found via AppleScript process check")
                is_launched = True
                break

        # Method 3: Try activating and see if it exists
        if attempt % 15 == 0 and attempt > 10:  # Try after a while
            activate_script = """
            try
                tell application "WindSurf" to activate
                delay 2
                return "activated"
            on error errMsg
                return "error: " & errMsg
            end try
            """
            activate_result = subprocess.run(
                ["osascript", "-e", activate_script], capture_output=True, text=True
            )
            if (
                activate_result.returncode == 0
                and "activated" in activate_result.stdout
            ):
                logger.info("WindSurf successfully activated")
                is_launched = True
                break

    if not is_launched:
        logger.error(
            f"Failed to detect WindSurf process after {max_attempts} attempts."
        )
        return False

    # Give extra time for WindSurf to fully initialize (it's slower than Cursor)
    logger.info("Waiting 10 seconds for WindSurf to fully initialize...")
    time.sleep(10)  # WindSurf needs more time to initialize

    # Try to activate the window
    script = """
    tell application "WindSurf"
        activate
    end tell
    """
    subprocess.run(["osascript", "-e", script])

    # Wait an additional moment for activation
    time.sleep(2)

    # Press Enter to clear any potential dialog boxes
    enter_script = """
    tell application "System Events" to keystroke return
    """
    subprocess.run(["osascript", "-e", enter_script])

    logger.info("WindSurf launched successfully!")
    return True


def main():
    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration.")
        return 1

    # Get windsurf_mushattention platform config
    platform_config = config.get("platforms", {}).get("windsurf_mushattention")
    if not platform_config:
        logger.error("No configuration found for platform: windsurf_mushattention")
        return 1

    # Get project path
    project_path = platform_config.get("project_path")
    if not project_path:
        logger.error("No project path defined for platform: windsurf_mushattention")
        return 1

    # Expand user directory
    project_path = os.path.expanduser(project_path)
    if not os.path.exists(project_path):
        logger.error(f"Project path does not exist: {project_path}")
        return 1

    # Launch WindSurf
    success = launch_windsurf(project_path)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
