#!/usr/bin/env python3.13
import subprocess
import threading
import sys
import os
import logging
import yaml
import time
from src.utils.colored_logging import setup_colored_logging

# Configure logging
setup_colored_logging(debug=os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('run_both')

def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Could not read config: {e}")
        return {}

def stream_output(process, prefix):
    """Stream output from a process with a prefix"""
    for line in iter(process.stdout.readline, b''):
        # Decode the line and remove any trailing newlines
        line_text = line.decode().rstrip()
        if line_text:  # Only log non-empty lines
            logger.info(f"{prefix} | {line_text}")

def run_flask():
    """Run the Flask server"""
    env = os.environ.copy()
    env["FLASK_APP"] = "slack_bot.py"
    process = subprocess.Popen(
        ["flask", "run", "--port=5005"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=False
    )
    stream_output(process, "FLASK")

def run_watcher():
    """Run the watcher process"""
    process = subprocess.Popen(
        ["python3", "watcher.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False
    )
    stream_output(process, "WATCH")

def main():
    """Main function to run both Flask server and watcher process."""
    logger.info("Starting both processes...")
    
    # Start each process in its own thread
    flask_thread = threading.Thread(target=run_flask)
    watcher_thread = threading.Thread(target=run_watcher)
    
    flask_thread.daemon = True
    watcher_thread.daemon = True
    
    flask_thread.start()
    watcher_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            flask_thread.join(1)
            watcher_thread.join(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
