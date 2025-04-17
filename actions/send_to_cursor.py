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

def send_prompt(prompt, platform="cursor", new_chat=False, initial_delay=0, send_message=True):
    """
    Sends a prompt to Cursor or Windsurf.
    If new_chat is True, starts a new chat (Cmd+N or Cmd+Shift+L).
    platform: 'cursor' (default) or 'windsurf'
    initial_delay: seconds to wait before sending final Enter key
    send_message: if False, will only type the message without sending it
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
        # First activate Cursor and wait for it to be ready
        activate_script = '''
        tell application "Cursor" to activate
        delay 2
        '''
        print("Activating Cursor...")
        subprocess.run(["osascript", "-e", activate_script])

        # Try to take a screenshot and check chat window
        screenshot = take_cursor_screenshot()
        if not screenshot or not is_chat_window_open(screenshot):
            print("Opening chat window...")
            subprocess.run(["osascript", "-e", '''
                tell application "System Events"
                    tell process "Cursor"
                        keystroke "k" using {command down}
                        delay 1.5
                    end tell
                end tell
            '''])

        if new_chat:
            print("Starting new chat...")
            subprocess.run(["osascript", "-e", '''
                tell application "System Events"
                    tell process "Cursor"
                        keystroke "n" using {command down}
                        delay 1.5
                    end tell
                end tell
            '''])
            
            print("Waiting 5 seconds for new chat to fully initialize...")
            time.sleep(5)
            print("Proceeding with prompt text entry...")

        # Now send the actual prompt
        script = f'''
        tell application "System Events"
            tell process "Cursor"
                -- Move to chat input and ensure we're in the right spot
                key code 125
                delay 0.5
                key code 36
                delay 1

                -- Clear any existing text (try multiple times to ensure it works)
                repeat 2 times
                    keystroke "a" using {{command down}}
                    delay 0.3
                    key code 51
                    delay 0.3
                end repeat
            end tell
        end tell
        '''
        print("Clearing any existing text with Command+A and Delete...")
        subprocess.run(["osascript", "-e", script])

        # Additional backspace script with logging
        backspace_script = '''
        tell application "System Events"
            tell process "Cursor"
                -- Extra safety check - press delete a few times
                repeat 3 times
                    key code 51
                    delay 0.3
                end repeat

                -- Additional backspace keystrokes to clear any remaining text
                repeat 5 times
                    key code 51
                    delay 0.3
                end repeat
            end tell
        end tell
        '''
        print("Pressing backspace multiple times to ensure text is cleared...")
        subprocess.run(["osascript", "-e", backspace_script])
        print("Finished backspace operations.")

        # Now send the actual prompt with a delay
        print("Starting to type prompt text...")
        prompt_script = f'''
        tell application "System Events"
            tell process "Cursor"
                -- Small pause before typing new text
                delay 1

                -- Type the prompt
                {keystrokes_str}
                delay 0.5
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", prompt_script])
        print("Finished typing prompt text.")

        if send_message:
            script = f'''
        tell application "System Events"
            tell process "Cursor"
                -- Wait before sending
                delay {initial_delay}
                
                -- Send the prompt (only if explicitly requested)
                key code 36
            end tell
        end tell
            '''
            print(f"Waiting {initial_delay} seconds before sending...")
            subprocess.run(["osascript", "-e", script])
            print("Prompt sent!")
        else:
            print("Prompt typed but not sent.")

    elif platform == "windsurf":
        # Similar changes for Windsurf...
        base_script = f'''
        tell application "System Events"
            tell application "Windsurf" to activate
            delay 2
            {('keystroke "l" using {command down, shift down}' + '\n delay 1') if new_chat else ''}
            keystroke "k" using {{command down}}
            delay 1
            key code 125
            delay 0.5
            key code 36
            delay 1
            {keystrokes_str}
            delay 0.5
        '''
        
        if send_message:
            base_script += f'''
            delay {initial_delay}
            key code 36
            '''
            
        base_script += '''
        end tell
        '''
        
        subprocess.run(["osascript", "-e", base_script])
    else:
        raise ValueError(f"Unknown platform: {platform}")
