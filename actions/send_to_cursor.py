import subprocess
import os
import time
from actions.openai_vision import is_chat_window_open
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true" else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('send_to_cursor')

# Add debug info about logging level
logger.debug("Debug logging enabled") if os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true" else logger.info("Info logging enabled")

def get_project_name():
    """Get the project name from the config file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    try:
        with open(config_path) as f:
            config = json.load(f)
            # Get the last part of the project path
            return os.path.basename(config["project_path"])
    except Exception as e:
        logger.warning(f"Could not get project name from config: {e}")
        return None

def get_cursor_window_id(max_retries=5, delay=1, platform="cursor"):
    """
    Gets the window ID of the Cursor/Windsurf app using AppleScript.
    Retries several times if not found, with debug info.
    Returns the window ID as a string, or None if not found.
    """
    project_name = get_project_name()
    if not project_name:
        logger.info("No project name found in config, will try to find any window")
    
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
    
    # List all windows and their properties
    windows_script = f'''
    tell application "System Events"
        tell process "{app_name}"
            set windowList to {{}}
            repeat with w in every window
                copy {{title:name of w, id:id of w, position:position of w, size:size of w}} to end of windowList
            end repeat
            return windowList
        end tell
    end tell
    '''
    
    for attempt in range(max_retries):
        logger.info(f"Attempt {attempt+1} to find {app_name} window...")
        result = subprocess.run(["osascript", "-e", windows_script], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            logger.info(f"Found windows: {result.stdout.strip()}")
            
            # Try to find the project window
            window_check = 'true' if not project_name else f'name of w contains "— {project_name}" or name of w contains "- {project_name}"'
            find_window_script = f'''
            tell application "System Events"
                tell process "{app_name}"
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
                logger.info(f"Found main window ID: {window_id}")
                return window_id
        
        logger.info(f"Attempt {attempt+1} failed.")
        if result.stderr:
            logger.warning(f"Error output: {result.stderr.strip()}")
        time.sleep(delay)
    
    logger.warning("Could not find window ID after retries.")
    return None

def activate_platform(platform="cursor"):
    """Activate the Cursor or Windsurf application window."""
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
    logger.info(f"Activating {app_name}...")
    script = f'''
    tell application "{app_name}" to activate
    delay 1
    tell application "System Events"
        tell process "{app_name}"
            set frontmost to true
        end tell
    end tell
    delay 1
    '''
    subprocess.run(["osascript", "-e", script])
    # Add extra delay after activation to ensure app is fully ready
    logger.info(f"Waiting 3 seconds for {app_name} to fully initialize...")
    time.sleep(3)
    logger.info("Done.")

def take_cursor_screenshot(filename="cursor_window.png", platform="cursor"):
    """
    Takes a screenshot of the Cursor/Windsurf window and saves it as filename.
    Returns the path to the screenshot, or None if failed.
    """
    project_name = get_project_name()
    if not project_name:
        print("Warning: No project name found in config, will try to find any window")
    
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
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
    debug_script = f'''
    tell application "System Events"
        tell process "{app_name}"
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
        print(f"Found {app_name} windows: {debug_result.stdout.strip()}")
    else:
        print("Could not list windows")
        if debug_result.stderr:
            print(f"Debug error: {debug_result.stderr}")
    
    # Get window bounds using AppleScript
    window_check = 'true' if not project_name else f'winName contains "— {project_name}" or winName contains "- {project_name}"'
    bounds_script = f'''
    tell application "System Events"
        tell process "{app_name}"
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
        print(f"Could not get window bounds: {error_msg}")
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
    Send a prompt to the specified platform with verbose logging and delays.
    """
    if initial_delay > 0:
        logger.info(f"Waiting {initial_delay} seconds before sending prompt...")
        time.sleep(initial_delay)
    
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
    logger.info(f"Starting to send prompt to {app_name}...")
    
    # Activate the application
    logger.info(f"Activating {app_name}...")
    activate_platform(platform)
    
    if new_chat:
        logger.info(f"Creating new chat window in {app_name}...")
        if platform == "cursor":
            # Send Command+N to create a new chat
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    keystroke "n" using {{command down}}
                end tell
            end tell
            '''
            logger.info("Sending Command+N to create new chat...")
            subprocess.run(["osascript", "-e", script])
            logger.info("Waiting 2 seconds for new chat to open...")
            time.sleep(2)
            
            # Open the chat window with Command+L
            logger.info("Sending Command+L to open chat window...")
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    keystroke "l" using {{command down}}
                end tell
            end tell
            '''
            subprocess.run(["osascript", "-e", script])
            logger.info("Waiting 2 seconds for chat window to fully open...")
            time.sleep(2)
        else:  # windsurf
            # Send Command+Shift+L to create a new chat
            print("⌨️  Sending Command+Shift+L to create new chat...")
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    keystroke "l" using {{command down, shift down}}
                end tell
            end tell
            '''
            subprocess.run(["osascript", "-e", script])
            print("⏳ Waiting 2 seconds for new chat to open...")
            time.sleep(2)
    
    # Clear any existing text with Command+A then backspace
    print("🧹 Clearing any existing text...")
    script = f'''
    tell application "System Events"
        tell process "{app_name}"
            -- Select all text
            keystroke "a" using {{command down}}
            delay 0.1
            
            -- Press delete key multiple times to ensure text is cleared
            repeat 10 times
                key code 51  -- Delete/Backspace key
                delay 0.05
            end repeat
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script])
    print("⏳ Waiting 1 second after clearing text...")
    time.sleep(1)
    
    # Split prompt into lines and send with Shift+Enter between them
    lines = prompt.splitlines()
    print(f"📄 Sending {len(lines)} lines of text...")
    
    for i, line in enumerate(lines):
        # Send the line
        print(f"📝 Sending line {i+1}/{len(lines)}: {line[:50]}{'...' if len(line) > 50 else ''}")
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                keystroke "{line.replace('"', '\\"')}"
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        
        if i < len(lines) - 1:
            print("⌨️  Sending Shift+Enter for newline...")
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    key code 36 using {{shift down}}  -- Shift+Enter
                end tell
            end tell
            '''
            subprocess.run(["osascript", "-e", script])
            print("⏳ Waiting 0.8 seconds after newline...")
            time.sleep(0.8)
        elif send_message:
            print("⌨️  Sending Enter to send message...")
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    key code 36  -- Enter
                end tell
            end tell
            '''
            subprocess.run(["osascript", "-e", script])
            print("⏳ Waiting 1 second after sending message...")
            time.sleep(1)
    
    print("✅ Prompt sent successfully!")

def kill_cursor(platform="cursor"):
    """Kill the Cursor or Windsurf application if it's running."""
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
    print(f"[kill_cursor] Checking if {app_name} is running...")
    
    # Check if app is running
    check_script = f'''
    tell application "System Events"
        count (every process whose name is "{app_name}")
    end tell
    '''
    
    result = subprocess.run(["osascript", "-e", check_script], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip() != "0":
        print(f"[kill_cursor] {app_name} is running, killing it...")
        subprocess.run(["pkill", "-x", app_name])
        print(f"[kill_cursor] Waiting 2 seconds for process to fully terminate...")
        time.sleep(2)  # Wait longer for process to fully terminate
        print("[kill_cursor] Done.")
    else:
        print(f"[kill_cursor] {app_name} is not running.")

def launch_platform(platform="cursor"):
    """Launch Cursor or Windsurf and wait for it to be ready."""
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
    print(f"[launch_platform] Starting {app_name}...")
    subprocess.run(["open", "-a", app_name])
    
    # Wait for process to appear
    print(f"[launch_platform] Waiting for {app_name} process...")
    for _ in range(10):  # Try for 10 seconds
        check_script = f'''
        tell application "System Events"
            count (every process whose name is "{app_name}")
        end tell
        '''
        result = subprocess.run(["osascript", "-e", check_script], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() != "0":
            print(f"[launch_platform] {app_name} process detected.")
            break
        time.sleep(1)
    
    # For Windsurf, press Enter to clear any dialog boxes
    if platform == "windsurf":
        print("[launch_platform] Pressing Enter to clear any dialog boxes in Windsurf...")
        script = '''
        tell application "System Events"
            tell process "Windsurf"
                key code 36  -- Enter key
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script])
        print("[launch_platform] Waiting 1 second after pressing Enter...")
        time.sleep(1)
    
    # Give it extra time to fully initialize
    print(f"[launch_platform] Waiting 5 seconds for {app_name} to fully initialize...")
    time.sleep(5)
    
    print("[launch_platform] Done.")
