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

def send_prompt(prompt, platform="cursor", new_chat=False):
    """
    Sends a prompt to Cursor or Windsurf.
    If new_chat is True, starts a new chat (Cmd+N or Cmd+Shift+L).
    platform: 'cursor' (default) or 'windsurf'
    """
    # Check if OPENAI_API_KEY is set
    if 'OPENAI_API_KEY' not in os.environ:
        print("OPENAI_API_KEY is not set in the environment.")
        return

    # Split prompt into lines and build keystrokes with Shift+Enter for newlines
    lines = prompt.splitlines()
    keystrokes = []
    for i, line in enumerate(lines):
        # Escape quotes for AppleScript
        safe_line = line.replace('"', '\"')
        keystrokes.append(f'keystroke "{safe_line}"')
        if i != len(lines) - 1:
            # Add Shift+Enter for new line (key code 36 is Enter)
            keystrokes.append('key code 36 using {shift down}')
    keystrokes_str = '\n            '.join(keystrokes)

    if platform == "cursor":
        script = f'''
        tell application "System Events"
            tell application "Cursor" to activate
            delay 0.8
            {'keystroke "n" using {command down}\n delay 0.3' if new_chat else ''}
            keystroke "k" using {{command down}}
            delay 0.5
            key code 125
            delay 0.3
            key code 36
            delay 0.5
            {keystrokes_str}
            delay 0.3
            key code 36
        end tell
        '''
    elif platform == "windsurf":
        script = f'''
        tell application "System Events"
            tell application "Windsurf" to activate
            delay 0.8
            {'keystroke "l" using {command down, shift down}\n delay 0.3' if new_chat else ''}
            keystroke "k" using {{command down}} -- or adjust as needed for Windsurf
            delay 0.5
            key code 125
            delay 0.3
            key code 36
            delay 0.5
            {keystrokes_str}
            delay 0.3
            key code 36
        end tell
        '''
    else:
        raise ValueError(f"Unknown platform: {platform}")
    subprocess.run(["osascript", "-e", script])
