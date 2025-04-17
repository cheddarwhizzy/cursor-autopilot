import time
import os
from actions.send_to_cursor import get_cursor_window_id, take_cursor_screenshot, send_keys, kill_cursor, launch_cursor
from actions.openai_vision import is_chat_window_open
import subprocess

def ensure_chat_window():
    """
    Ensures the Cursor chat window is open by:
    1. Killing any existing Cursor process
    2. Launching Cursor and waiting for it to be ready
    3. Taking a screenshot
    4. Using OpenAI Vision to check if chat window is open
    5. Sending Command+L keystroke if needed
    """
    print("[ensure_chat_window] Starting chat window check...")
    
    # First kill any existing Cursor process
    kill_cursor()
    
    # Launch Cursor and wait for it to be ready
    launch_cursor()
    
    # Take screenshot of Cursor window
    print("[ensure_chat_window] Taking screenshot of Cursor window...")
    screenshot_path = take_cursor_screenshot()
    if not screenshot_path:
        print("[ensure_chat_window] Could not take screenshot. Sending single Command+L as fallback.")
        print("[ensure_chat_window] Note: This can happen if the window bounds cannot be detected.")
        print("[ensure_chat_window] Sending Command+L to toggle chat window...")
        send_keys(["command down", "l", "command up"])
        print("[ensure_chat_window] Done.")
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
    
    print("[ensure_chat_window] Done. Chat window should now be in correct state.")

if __name__ == "__main__":
    ensure_chat_window()
