import time
import os
import json
import yaml
from src.actions.send_to_cursor import get_cursor_window_id, take_cursor_screenshot, send_keys, kill_cursor, launch_platform
from src.actions.openai_vision import is_chat_window_open
import subprocess
import logging
from src.utils.colored_logging import setup_colored_logging

def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not read config: {e}")
        return {}

# Configure logging
setup_colored_logging(debug=os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('ensure_chat_window')

def ensure_chat_window(platform=None):
    """
    Ensures the Cursor/Windsurf chat window is open by:
    1. Killing any existing Cursor/Windsurf process
    2. Launching Cursor/Windsurf and waiting for it to be ready
    3. Taking a screenshot and using OpenAI Vision to check if chat window is open (if enabled)
    """
    config = get_config()
    use_vision_api = config.get("use_vision_api", False)
    
    # Use platform from config if not explicitly provided
    if platform is None:
        platform = config.get("platform", "cursor")
    
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
    logger.info(f"Using configured IDE: {app_name}")
    logger.info(f"Starting {app_name} chat window check...")
    
    # First kill any existing process
    kill_cursor(platform)
    
    # Launch app and wait for it to be ready
    launch_platform(platform)
    
    if use_vision_api:
        # Take screenshot of window
        logger.info(f"Taking screenshot of {app_name} window...")
        screenshot_path = take_cursor_screenshot(platform=platform)
        if not screenshot_path:
            logger.info(f"Could not take screenshot. Skipping vision check.")
            return
        
        # Check if chat window is open using Vision API
        logger.info("[ensure_chat_window] Sending screenshot to OpenAI Vision...")
        chat_window_open = is_chat_window_open(screenshot_path)
        logger.info(f"[ensure_chat_window] OpenAI Vision detected chat window state: {chat_window_open}")
        
        # If chat window is open, we want to close it
        # If chat window is closed, we want to open it
        # In either case, one Command+L will do the job
        logger.info(f"[ensure_chat_window] Chat window is {'open' if chat_window_open else 'closed'}, sending Command+L to toggle state...")
        send_keys(["command down", "l", "command up"], platform=platform)
    else:
        logger.info("[ensure_chat_window] Vision API disabled, skipping chat window check.")
    
    logger.info("[ensure_chat_window] Done.")

if __name__ == "__main__":
    import sys
    platform = sys.argv[1] if len(sys.argv) > 1 else None
    ensure_chat_window(platform)
