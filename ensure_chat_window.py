import time
import os
from actions.send_to_cursor import get_cursor_window_id, take_cursor_screenshot
from actions.openai_vision import is_chat_window_open
import subprocess

def ensure_chat_window_open():
    print("[ensure_chat_window] Waiting for Cursor to launch...")
    time.sleep(3)  # Wait for Cursor to fully launch

    print("[ensure_chat_window] Taking screenshot of Cursor window...")
    screenshot_path = take_cursor_screenshot()
    if not screenshot_path:
        print("[ensure_chat_window] Could not take screenshot. Sending single Command+L as fallback.")
        l_count = 1
    else:
        print("[ensure_chat_window] Sending screenshot to OpenAI Vision...")
        state = is_chat_window_open(screenshot_path)
        print(f"[ensure_chat_window] OpenAI Vision detected chat window state: {state}")
        if state == "open":
            l_count = 2  # toggle closed then open
        elif state == "closed":
            l_count = 1  # open once
        else:
            print("[ensure_chat_window] Could not determine chat window state. Defaulting to one Command+L.")
            l_count = 1

    l_keystrokes = '\n'.join(["keystroke \"l\" using {command down}\n delay 0.3" for _ in range(l_count)])
    script = f'''
    tell application "System Events"
        tell application "Cursor" to activate
        delay 0.5
        {l_keystrokes}
    end tell
    '''
    print(f"[ensure_chat_window] Sending {l_count} Command+L keystroke(s) to Cursor...")
    subprocess.run(["osascript", "-e", script])
    print("[ensure_chat_window] Done.")

if __name__ == "__main__":
    ensure_chat_window_open()
