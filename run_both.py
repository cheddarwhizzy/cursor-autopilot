#!/usr/bin/env python3.13
import subprocess
import threading
import sys
import os
import logging
from utils.colored_logging import setup_colored_logging

# Configure logging
setup_colored_logging(debug=os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('run_both')

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

if __name__ == "__main__":
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
