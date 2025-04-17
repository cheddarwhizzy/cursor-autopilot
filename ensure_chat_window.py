import time
import os
from actions.send_to_cursor import get_cursor_window_id, take_cursor_screenshot
from actions.openai_vision import is_chat_window_open
import subprocess

def ensure_chat_window_open():
    print("[ensure_chat_window] Waiting for Cursor to launch...")
    print("[ensure_chat_window] Note: The chat window should be closed when Cursor initially opens.")
    print("[ensure_chat_window] Waiting 3 seconds for Cursor to fully launch...")
    time.sleep(3)  # Wait for Cursor to fully launch

    print("[ensure_chat_window] Taking screenshot of Cursor window...")
    screenshot_path = take_cursor_screenshot()
    if not screenshot_path:
        print("[ensure_chat_window] Could not take screenshot. Sending single Command+L as fallback.")
        print("[ensure_chat_window] Note: This can happen if the window bounds cannot be detected.")
        l_count = 1
        l_keystrokes = "keystroke \"l\" using {command down}"
    else:
        print("[ensure_chat_window] Sending screenshot to OpenAI Vision...")
        is_open = is_chat_window_open(screenshot_path)
        print(f"[ensure_chat_window] OpenAI Vision detected chat window state: {is_open}")
        if is_open:
            print("[ensure_chat_window] Chat window is open, sending Command+L twice to toggle closed then open...")
            print("[ensure_chat_window] Will wait 1 second between keystrokes for UI to react...")
            l_count = 2
            # Add a longer delay between the two Command+L presses
            l_keystrokes = '''
            keystroke "l" using {command down}
            delay 1
            keystroke "l" using {command down}
            '''
        else:
            print("[ensure_chat_window] Chat window is closed, sending Command+L once to open...")
            l_count = 1
            l_keystrokes = "keystroke \"l\" using {command down}"

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
