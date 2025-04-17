import subprocess
import os
import time
from actions.openai_vision import is_chat_window_open

def get_cursor_window_id(max_retries=5, delay=1):
    """
    Gets the window ID of the Cursor app using AppleScript.
    Retries several times if not found, with debug info.
    Returns the window ID as a string, or None if not found.
    """
    script = '''
    tell application "System Events"
        set cursorProcs to (every process whose name is "Cursor")
        if (count of cursorProcs) > 0 then
            set cursorProc to first item of cursorProcs
            if (count of windows of cursorProc) > 0 then
                return id of first window of cursorProc
            else
                return "NO_WINDOWS"
            end if
        else
            return "NO_PROCESS"
        end if
    end tell
    '''
    for attempt in range(max_retries):
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        window_id = result.stdout.strip()
        if window_id and window_id not in ("NO_WINDOWS", "NO_PROCESS"):
            print(f"[get_cursor_window_id] Found window ID: {window_id}")
            return window_id
        print(f"[get_cursor_window_id] Attempt {attempt+1}: {window_id}")
        if window_id == "NO_WINDOWS":
            # Print window names for debugging
            debug_script = '''
            tell application "System Events"
                set cursorProcs to (every process whose name is "Cursor")
                if (count of cursorProcs) > 0 then
                    set cursorProc to first item of cursorProcs
                    set windowNames to name of every window of cursorProc
                    return windowNames
                else
                    return "NO_PROCESS"
                end if
            end tell
            '''
            debug_result = subprocess.run(["osascript", "-e", debug_script], capture_output=True, text=True)
            print(f"[get_cursor_window_id] Window names: {debug_result.stdout.strip()}")
        time.sleep(delay)
    print("[get_cursor_window_id] Could not find Cursor window ID after retries.")
    return None

def take_cursor_screenshot(filename="cursor_window.png"):
    """
    Takes a screenshot of the Cursor window and saves it as filename.
    Returns the path to the screenshot, or None if failed.
    """
    window_id = get_cursor_window_id()
    if not window_id:
        print("Could not find Cursor window ID.")
        return None
    result = subprocess.run(["screencapture", "-l", window_id, filename])
    if result.returncode == 0:
        return filename
    else:
        print("Failed to take screenshot of Cursor window.")
        return None

def send_prompt(prompt, platform="cursor"):
    """
    Ensures Cursor or Windsurf chat window is open using OpenAI Vision, then sends the prompt.
    Requires OPENAI_API_KEY to be set in the environment.
    platform: 'cursor' (default) or 'windsurf'
    """
    # Check if OPENAI_API_KEY is set
    if 'OPENAI_API_KEY' not in os.environ:
        print("OPENAI_API_KEY is not set in the environment.")
        return

    # Take screenshot of Cursor/Windsurf window
    screenshot_path = take_cursor_screenshot()
    if not screenshot_path:
        print("Could not take screenshot. Proceeding with single Command+L.")
        l_count = 1
    else:
        # Use OpenAI Vision to check chat window state
        state = is_chat_window_open(screenshot_path)
        if state == "open":
            l_count = 2  # toggle closed then open
        elif state == "closed":
            l_count = 1  # open once
        else:
            print("Could not determine chat window state. Defaulting to one Command+L.")
            l_count = 1

    # Build AppleScript for platform
    if platform == "cursor":
        l_keystrokes = '\n'.join(["keystroke \"l\" using {command down}\n delay 0.3" for _ in range(l_count)])
        # Add Command+N for new chat
        new_chat_keystroke = 'keystroke "n" using {command down}\n delay 0.3'
        script = f'''
        tell application "System Events"
            tell application "Cursor" to activate
            delay 0.8
            {l_keystrokes}
            delay 0.5
            {new_chat_keystroke}
            delay 0.3
            keystroke "k" using {{command down}}
            delay 0.5
            key code 125
            delay 0.3
            key code 36
            delay 0.5
            keystroke "{prompt}"
            delay 0.3
            key code 36
        end tell
        '''
    elif platform == "windsurf":
        # Windsurf uses Command+Shift+L for chat and new chat
        l_keystrokes = '\n'.join(["keystroke \"l\" using {command down, shift down}\n delay 0.3" for _ in range(l_count)])
        # Add Command+Shift+L again for new chat
        new_chat_keystroke = 'keystroke "l" using {command down, shift down}\n delay 0.3'
        script = f'''
        tell application "System Events"
            tell application "Windsurf" to activate
            delay 0.8
            {l_keystrokes}
            delay 0.5
            {new_chat_keystroke}
            delay 0.3
            keystroke "k" using {{command down}} -- or adjust as needed for Windsurf
            delay 0.5
            key code 125
            delay 0.3
            key code 36
            delay 0.5
            keystroke "{prompt}"
            delay 0.3
            key code 36
        end tell
        '''
    else:
        raise ValueError(f"Unknown platform: {platform}")
    subprocess.run(["osascript", "-e", script])
