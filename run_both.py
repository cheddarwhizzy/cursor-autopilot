#!/usr/bin/env python3.13
import subprocess
import threading
import sys
import os
import logging
import time
from utils.colored_logging import setup_colored_logging

# Configure logging based on environment variables
debug = os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "1"
json_mode = os.environ.get("CURSOR_AUTOPILOT_JSON") == "1"
setup_colored_logging(debug=debug, use_json=json_mode)
logger = logging.getLogger('run_both')

def run_process(command, name):
    """Run a process and log its output."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Log output in real-time
    for line in iter(process.stdout.readline, ''):
        if json_mode:
            # For JSON mode, we want to preserve the original log format
            print(line.strip())
        else:
            logger.info(f"{name} | {line.strip()}")
    
    return process

def main():
    # Get configuration
    auto_mode = os.environ.get("CURSOR_AUTOPILOT_AUTO") == "1"
    logger.info(f"Starting both processes...")
    
    # Start Flask server (Slack bot)
    flask_process = run_process(["flask", "run"], "FLASK")
    
    # Give Flask a moment to start
    time.sleep(2)
    
    # Start watcher
    watcher_process = run_process(["python3", "watcher.py"], "WATCH")
    
    try:
        # Wait for either process to exit
        while True:
            if flask_process.poll() is not None:
                logger.error("Flask process died")
                break
            if watcher_process.poll() is not None:
                logger.error("Watcher process died")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Clean up processes
        flask_process.terminate()
        watcher_process.terminate()
        flask_process.wait()
        watcher_process.wait()

if __name__ == "__main__":
    main()
