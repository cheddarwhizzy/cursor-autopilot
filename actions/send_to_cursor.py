import subprocess
import os
import time
from actions.openai_vision import is_chat_window_open
import json

def get_project_name():
    """Get the project name from the config file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    try:
        with open(config_path) as f:
            config = json.load(f)
            # Get the last part of the project path
            return os.path.basename(config["project_path"])
    except Exception as e:
        print(f"Warning: Could not get project name from config: {e}")
        return None

def get_cursor_window_id(max_retries=5, delay=1):
    """
    Gets the window ID of the Cursor app using AppleScript.
    Retries several times if not found, with debug info.
    Returns the window ID as a string, or None if not found.
    """
    project_name = get_project_name()
    if not project_name:
        print("[get_cursor_window_id] No project name found in config, will try to find any Cursor window")
    
    # List all Cursor windows and their properties
    windows_script = '''
    tell application "System Events"
        tell process "Cursor"
            set windowList to {}
            repeat with w in every window
                copy {title:name of w, id:id of w, position:position of w, size:size of w} to end of windowList
            end repeat
            return windowList
        end tell
    end tell
    '''
    
    for attempt in range(max_retries):
        print(f"[get_cursor_window_id] Attempt {attempt+1} to find Cursor window...")
        result = subprocess.run(["osascript", "-e", windows_script], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"[get_cursor_window_id] Found windows: {result.stdout.strip()}")
            
            # Try to find the project window
            window_check = 'true' if not project_name else f'name of w contains "— {project_name}" or name of w contains "- {project_name}"'
            find_window_script = f'''
            tell application "System Events"
                tell process "Cursor"
                    repeat with w in every window
                        if {window_check} then
                            return id of w
                        end if
                    end repeat
                end tell
            end tell
            '''
            
            window_result = subprocess.run(["osascript", "-e", find_window_script], capture_output=True, text=True)
            if window_result.returncode == 0 and window_result.stdout.strip():
                window_id = window_result.stdout.strip()
                print(f"[get_cursor_window_id] Found main window ID: {window_id}")
                return window_id
        
        print(f"[get_cursor_window_id] Attempt {attempt+1} failed.")
        if result.stderr:
            print(f"[get_cursor_window_id] Error output: {result.stderr.strip()}")
        time.sleep(delay)
    
    print("[get_cursor_window_id] Could not find Cursor window ID after retries.")
    return None

def activate_cursor():
    """Activate the Cursor application window."""
    print("[activate_cursor] Activating Cursor...")
    script = '''
    tell application "Cursor" to activate
    delay 1
    tell application "System Events"
        tell process "Cursor"
            set frontmost to true
        end tell
    end tell
    delay 1
    '''
    subprocess.run(["osascript", "-e", script])
    # Add extra delay after activation to ensure app is fully ready
    print("[activate_cursor] Waiting 3 seconds for Cursor to fully initialize...")
    time.sleep(3)
    print("[activate_cursor] Done.")

def take_cursor_screenshot(filename="cursor_window.png"):
    """
    Takes a screenshot of the Cursor window and saves it as filename.
    Returns the path to the screenshot, or None if failed.
    """
    project_name = get_project_name()
    if not project_name:
        print("Warning: No project name found in config, will try to find any Cursor window")
    
    abs_path = os.path.abspath(filename)
    print(f"Attempting to take screenshot, will save to: {abs_path}")
    
    # First list all processes to debug
    process_script = '''
    tell application "System Events"
        set allProcesses to name of every process
        return allProcesses
    end tell
    '''
    
    process_result = subprocess.run(["osascript", "-e", process_script], capture_output=True, text=True)
    if process_result.returncode == 0:
        print(f"All processes: {process_result.stdout.strip()}")
    
    # First list all windows to debug
    debug_script = '''
    tell application "System Events"
        tell process "Cursor"
            set windowInfo to ""
            repeat with w in every window
                set windowInfo to windowInfo & "Window: " & name of w & ", "
            end repeat
            return windowInfo
        end tell
    end tell
    '''
    
    debug_result = subprocess.run(["osascript", "-e", debug_script], capture_output=True, text=True)
    if debug_result.returncode == 0:
        print(f"Found Cursor windows: {debug_result.stdout.strip()}")
    else:
        print("Could not list Cursor windows")
        if debug_result.stderr:
            print(f"Debug error: {debug_result.stderr}")
    
    # Get Cursor window bounds using AppleScript
    window_check = 'true' if not project_name else f'winName contains "— {project_name}" or winName contains "- {project_name}"'
    bounds_script = f'''
    tell application "System Events"
        tell process "Cursor"
            try
                set allWindows to every window
                if length of allWindows is 0 then
                    error "No windows found"
                end if
                
                repeat with w in allWindows
                    set winName to name of w
                    log "Checking window: " & winName
                    if {window_check} then
                        set pos to position of w
                        set sz to size of w
                        return {{(item 1 of pos), (item 2 of pos), (item 1 of sz), (item 2 of sz)}}
                    end if
                end repeat
                error "No suitable window found (no project window found)"
            on error errMsg
                return "error: " & errMsg
            end try
        end tell
    end tell
    '''
    
    bounds_result = subprocess.run(["osascript", "-e", bounds_script], capture_output=True, text=True)
    if bounds_result.returncode == 0 and not bounds_result.stdout.strip().startswith("error:"):
        try:
            # Parse the bounds - format is "x, y, width, height"
            bounds = bounds_result.stdout.strip()
            print(f"Window bounds: {bounds}")
            
            # Split by comma and clean up the values
            parts = [int(p.strip().strip('{}')) for p in bounds.split(',')]
            if len(parts) != 4:
                raise ValueError(f"Expected 4 values for bounds, got {len(parts)}: {parts}")
                
            x, y, width, height = parts
            if width <= 0 or height <= 0:
                raise ValueError(f"Invalid window dimensions: {width}x{height}")
            
            # Capture the specific region
            capture_cmd = ["screencapture", "-R", f"{x},{y},{width},{height}", filename]
            print(f"Running capture command: {' '.join(capture_cmd)}")
            
            result = subprocess.run(capture_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                if os.path.exists(filename):
                    print(f"Screenshot saved successfully: {filename}")
                    print(f"File size: {os.path.getsize(filename)} bytes")
                    return filename
                else:
                    print(f"Warning: screencapture returned success but file not found at {abs_path}")
            else:
                print(f"Failed to capture screenshot. Return code: {result.returncode}")
                if result.stderr:
                    print(f"Error output: {result.stderr}")
        except Exception as e:
            print(f"Error parsing window bounds: {e}")
            print(f"Raw bounds output: {bounds}")
    else:
        error_msg = bounds_result.stdout.strip()[7:] if bounds_result.stdout.strip().startswith("error:") else "unknown error"
        print(f"Could not get Cursor window bounds: {error_msg}")
        if bounds_result.stderr:
            print(f"Error output: {bounds_result.stderr}")
    
    return None

def send_keys(key_sequence):
    """
    Send a sequence of keystrokes to Cursor.
    key_sequence should be a list of strings, e.g. ["command down", "l", "command up"]
    """
    print(f"[send_keys] Sending key sequence: {key_sequence}")
    
    # First make sure Cursor is properly activated
    activate_script = '''
    tell application "Cursor" to activate
    delay 1
    tell application "System Events"
        tell process "Cursor"
            set frontmost to true
        end tell
    end tell
    delay 1
    '''
    
    print("[send_keys] Ensuring Cursor is active...")
    activate_result = subprocess.run(["osascript", "-e", activate_script], capture_output=True, text=True)
    if activate_result.returncode != 0:
        print(f"[send_keys] Warning: Error activating Cursor: {activate_result.stderr}")
    
    # Add a delay to ensure Cursor is ready
    print("[send_keys] Waiting 2 seconds for Cursor to be ready...")
    time.sleep(2)
    
    # Now send the keystroke
    script = '''
    tell application "System Events"
        tell process "Cursor"
            keystroke "l" using {command down}
        end tell
    end tell
    '''
    
    print("[send_keys] Executing keystroke...")
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode == 0:
        print("[send_keys] Keys sent successfully")
    else:
        print(f"[send_keys] Error sending keys: {result.stderr}")

def send_prompt(prompt, platform="cursor", new_chat=False, initial_delay=0, send_message=True):
    """
    Send a prompt to the specified platform.
    """
    if initial_delay > 0:
        print(f"Waiting {initial_delay} seconds before sending prompt...")
        time.sleep(initial_delay)
    
    if platform == "cursor":
        print("Activating Cursor...")
        activate_cursor()
        
        if new_chat:
            print("Opening chat window...")
            # No need to send Command+L, ensure_chat_window already handled it
            time.sleep(3)  # Wait for chat window to fully open
            
            # Clear any auto-entered text without pressing Enter
            script = '''
            tell application "System Events"
                keystroke "a" using {command down}
                delay 0.1
                key code 51  # Delete key
            end tell
            '''
            subprocess.run(["osascript", "-e", script])
            time.sleep(0.5)
        
        # Clear any existing text with Command+A then backspace
        print("Clearing any existing text...")
        script = '''
        tell application "System Events"
            -- Select all text
            keystroke "a" using {command down}
            delay 0.1
            
            -- Press delete key multiple times to ensure text is cleared
            repeat 10 times
                key code 51  # Delete/Backspace key
                delay 0.05
            end repeat
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        
        # Split prompt into lines and send with Shift+Enter between them
        lines = prompt.splitlines()
        for i, line in enumerate(lines):
            # Send the line
            script = f'''
            tell application "System Events"
                keystroke "{line.replace('"', '\\"')}"
                {'''
                delay 0.1
                ''' if i < len(lines) - 1 else ''}
                {'''
                key code 36 using {shift down}  # Shift+Enter for newline
                delay 0.1
                ''' if i < len(lines) - 1 else '''
                delay 0.1
                key code 36  # Just Enter for the last line
                ''' if send_message else ''}
            end tell
            '''
            subprocess.run(["osascript", "-e", script])
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
            keystroke "{prompt.replace('"', '\\"')}"
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

def kill_cursor():
    """Kill the Cursor application if it's running."""
    print("[kill_cursor] Checking if Cursor is running...")
    
    # Check if Cursor is running
    check_script = '''
    tell application "System Events"
        count (every process whose name is "Cursor")
    end tell
    '''
    
    result = subprocess.run(["osascript", "-e", check_script], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip() != "0":
        print("[kill_cursor] Cursor is running, killing it...")
        subprocess.run(["pkill", "-x", "Cursor"])
        print("[kill_cursor] Waiting 2 seconds for process to fully terminate...")
        time.sleep(2)  # Wait longer for process to fully terminate
        print("[kill_cursor] Done.")
    else:
        print("[kill_cursor] Cursor is not running.")

def launch_cursor():
    """Launch Cursor and wait for it to be ready."""
    print("[launch_cursor] Starting Cursor...")
    subprocess.run(["open", "-a", "Cursor"])
    
    # Wait for process to appear
    print("[launch_cursor] Waiting for Cursor process...")
    for _ in range(10):  # Try for 10 seconds
        check_script = '''
        tell application "System Events"
            count (every process whose name is "Cursor")
        end tell
        '''
        result = subprocess.run(["osascript", "-e", check_script], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() != "0":
            print("[launch_cursor] Cursor process detected.")
            break
        time.sleep(1)
    
    # Give it extra time to fully initialize
    print("[launch_cursor] Waiting 5 seconds for Cursor to fully initialize...")
    time.sleep(5)
    print("[launch_cursor] Done.")
