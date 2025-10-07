#!/usr/bin/env python3.13
import subprocess
import threading
import sys
import os
import logging
import yaml
import time

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from src
try:
    from src.utils.colored_logging import setup_colored_logging
except ImportError:
    # Fallback to basic logging if colored logging is not available
    def setup_colored_logging(debug=False):
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

# Configure logging
setup_colored_logging(debug=os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('run_both')

def get_config():
    # Get config from project root (parent of src directory)
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
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
            # Highlight countdown messages for better visibility
            if "countdown:" in line_text.lower():
                logger.info(f"🕐 {prefix} | {line_text}")
            else:
                logger.info(f"{prefix} | {line_text}")

def run_flask():
    """Run the Flask API server"""
    env = os.environ.copy()
    env["FLASK_APP"] = "src.api.app:create_production_app"
    env["FLASK_ENV"] = "development"
    logger.info("Starting Configuration API server on port 5005...")
    process = subprocess.Popen(
        ["flask", "run", "--port=5005", "--host=127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=False,
        cwd=os.path.dirname(os.path.dirname(__file__))  # Go up one level to project root
    )
    stream_output(process, "API")

def run_watcher(watcher_args=None):
    """Run the watcher process with optional arguments"""
    logger.info("Starting file watcher and platform manager...")
    
    # Build the command
    cmd = ["python3", "-m", "src.watcher"]
    
    # Add any arguments passed from the command line
    if watcher_args:
        cmd.extend(watcher_args)
        logger.info(f"Running watcher with arguments: {watcher_args}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False,
        cwd=os.path.dirname(os.path.dirname(__file__))  # Go up one level to project root
    )
    stream_output(process, "WATCHER")

def main():
    """Main function to run both Flask server and watcher process."""
    logger.info("Starting both processes...")
    
    # Pass all command line arguments to the watcher (skip the script name)
    watcher_args = sys.argv[1:] if len(sys.argv) > 1 else None
    if watcher_args:
        logger.info(f"Forwarding arguments to watcher: {watcher_args}")
    
    # Start each process in its own thread
    flask_thread = threading.Thread(target=run_flask)
    watcher_thread = threading.Thread(target=run_watcher, args=(watcher_args,))
    
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
