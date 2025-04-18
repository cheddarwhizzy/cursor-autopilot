import time
import os
import json
from actions.send_to_cursor import get_cursor_window_id, take_cursor_screenshot, send_keys, kill_cursor, launch_cursor
from actions.openai_vision import is_chat_window_open
import subprocess

def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not read config: {e}")
        return {}

def ensure_chat_window(platform="cursor"):
    """
    Ensures the Cursor/Windsurf chat window is open by:
    1. Killing any existing Cursor/Windsurf process
    2. Launching Cursor/Windsurf and waiting for it to be ready
    3. Taking a screenshot and using OpenAI Vision to check if chat window is open (if enabled)
    """
    config = get_config()
    use_vision_api = config.get("use_vision_api", False)
    
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
    print(f"[ensure_chat_window] Starting {app_name} chat window check...")
    
    # First kill any existing process
    kill_cursor(platform)
    
    # Launch app and wait for it to be ready
    launch_cursor(platform)
    
    if use_vision_api:
        # Take screenshot of window
        print(f"[ensure_chat_window] Taking screenshot of {app_name} window...")
        screenshot_path = take_cursor_screenshot()
        if not screenshot_path:
            print(f"[ensure_chat_window] Could not take screenshot. Skipping vision check.")
            return
        
        # Check if chat window is open using Vision API
        print("[ensure_chat_window] Sending screenshot to OpenAI Vision...")
        chat_window_open = is_chat_window_open(screenshot_path)
        print(f"[ensure_chat_window] OpenAI Vision detected chat window state: {chat_window_open}")
        
        # If chat window is open, we want to close it
        # If chat window is closed, we want to open it
        # In either case, one Command+L will do the job
        print(f"[ensure_chat_window] Chat window is {'open' if chat_window_open else 'closed'}, sending Command+L to toggle state...")
        send_keys(["command down", "l", "command up"])
    else:
        print("[ensure_chat_window] Vision API disabled, skipping chat window check.")
    
    print("[ensure_chat_window] Done.")

if __name__ == "__main__":
    ensure_chat_window()
