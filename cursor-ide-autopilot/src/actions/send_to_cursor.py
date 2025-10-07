import subprocess
import os
import time
from src.actions.openai_vision import is_chat_window_open
import yaml
import logging
from src.utils.colored_logging import setup_colored_logging
from typing import Optional, List, Dict
from .keystrokes import send_keystrokes, send_keystroke_sequence, activate_window

# Configure logging
setup_colored_logging(debug=os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('send_to_cursor')

# Add debug info about logging level
logger.debug("Debug logging enabled") if os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true" else logger.info("Info logging enabled")

def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not read config: {e}")
        return {}

def get_project_name():
    """Get the project name from the config file."""
    config = get_config()
    return config.get("project_path", {}).get("name")

def get_cursor_window_id(app_name: str = "Cursor", project_name: Optional[str] = None, max_retries: int = 3, delay: float = 1.0) -> Optional[str]:
    """
    Get the window ID of the Cursor/Windsurf window.
    """
    if not project_name:
        logger.info("No project name found in config, will try to find any window")
    
    if not project_name:
        project_name = get_project_name()
    
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

def take_cursor_screenshot(filename: str = "cursor_window.png", platform: str = "cursor") -> Optional[str]:
    """
    Take a screenshot of the Cursor/Windsurf window.
    """
    project_name = get_project_name()
    if not project_name:
        logger.warning("No project name found in config, will try to find any window")
    
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
    abs_path = os.path.abspath(filename)
    logger.info(f"Attempting to take screenshot, will save to: {abs_path}")
    
    # First list all processes to debug
    process_script = '''
    tell application "System Events"
        set allProcesses to name of every process
        return allProcesses
    end tell
    '''
    
    process_result = subprocess.run(["osascript", "-e", process_script], capture_output=True, text=True)
    if process_result.returncode == 0:
        logger.debug(f"All processes: {process_result.stdout.strip()}")
    
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
        logger.debug(f"Found {app_name} windows: {debug_result.stdout.strip()}")
    else:
        logger.warning("Could not list windows")
        if debug_result.stderr:
            logger.warning(f"Debug error: {debug_result.stderr}")
    
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
            logger.debug(f"Window bounds: {bounds}")
            
            # Split by comma and clean up the values
            parts = [int(p.strip().strip('{}')) for p in bounds.split(',')]
            if len(parts) != 4:
                raise ValueError(f"Expected 4 values for bounds, got {len(parts)}: {parts}")
                
            x, y, width, height = parts
            if width <= 0 or height <= 0:
                raise ValueError(f"Invalid window dimensions: {width}x{height}")
            
            # Capture the specific region
            capture_cmd = ["screencapture", "-R", f"{x},{y},{width},{height}", filename]
            logger.debug(f"Running capture command: {' '.join(capture_cmd)}")
            
            result = subprocess.run(capture_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                if os.path.exists(filename):
                    logger.info(f"Screenshot saved successfully: {filename}")
                    logger.debug(f"File size: {os.path.getsize(filename)} bytes")
                    return filename
                else:
                    logger.warning(f"Warning: screencapture returned success but file not found at {abs_path}")
            else:
                logger.error(f"Failed to capture screenshot. Return code: {result.returncode}")
                if result.stderr:
                    logger.error(f"Error output: {result.stderr}")
        except Exception as e:
            logger.error(f"Error parsing window bounds: {e}")
            logger.error(f"Raw bounds output: {bounds}")
    else:
        error_msg = bounds_result.stdout.strip()[7:] if bounds_result.stdout.strip().startswith("error:") else "unknown error"
        logger.error(f"Could not get window bounds: {error_msg}")
        if bounds_result.stderr:
            logger.error(f"Error output: {bounds_result.stderr}")
    
    return None

def send_keys(key_sequence: List[str], platform: str = "cursor") -> bool:
    """
    Send a sequence of keystrokes to Cursor/Windsurf.
    key_sequence should be a list of strings, e.g. ["command down", "l", "command up"]
    """
    logger.info(f"Sending key sequence: {key_sequence}")
    
    # First make sure Cursor/Windsurf is properly activated
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
    if not activate_window(app_name):
        logger.warning(f"Error activating app: {app_name}")
        return False
    
    # Add a delay to ensure app is ready
    logger.info("Waiting 2 seconds for app to be ready...")
    time.sleep(2)
    
    # Convert key sequence to pyautogui format
    keys = []
    modifiers = []
    
    for key in key_sequence:
        if key.endswith(" down"):
            modifiers.append(key[:-5])
        elif key.endswith(" up"):
            pass  # We'll handle this in the hotkey
        else:
            keys.append(key)
    
    # Send the keystrokes
    if modifiers:
        pyautogui.hotkey(*modifiers, *keys)
    else:
        for key in keys:
            pyautogui.press(key)
    
    logger.info("Keys sent successfully")
    return True

def send_prompt(prompt: str, platform: str = "cursor", new_chat: bool = False, initial_delay: int = 0, send_message: bool = True) -> bool:
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
    if not activate_window(app_name):
        logger.error(f"Failed to activate {app_name}")
        return False
    
    if new_chat:
        logger.info(f"Creating new chat window in {app_name}...")
        if platform == "cursor":
            # Send Command+N to create a new chat
            if not send_keystrokes("command+n"):
                return False
            logger.info("Waiting 2 seconds for new chat to open...")
            time.sleep(2)
            
            # Open the chat window with Command+L
            logger.info("Sending Command+L to open chat window...")
            if not send_keystrokes("command+l"):
                return False
            logger.info("Waiting 2 seconds for chat window to fully open...")
            time.sleep(2)
        else:  # windsurf
            # Send Command+Shift+L to create a new chat
            logger.info("Sending Command+Shift+L to create new chat...")
            if not send_keystrokes("command+shift+l"):
                return False
            logger.info("Waiting 2 seconds for new chat to open...")
            time.sleep(2)
    
    # Clear any existing text with Command+A then backspace
    logger.info("Clearing any existing text...")
    if not send_keystrokes("command+a"):
        return False
    time.sleep(0.1)
    
    # Press delete key multiple times to ensure text is cleared
    for _ in range(10):
        if not send_keystrokes("backspace"):
            return False
        time.sleep(0.05)
    
    logger.info("Waiting 1 second after clearing text...")
    time.sleep(1)
    
    # Split prompt into lines and send with Shift+Enter between them
    lines = prompt.splitlines()
    logger.info(f"Sending {len(lines)} lines of text...")
    
    for i, line in enumerate(lines):
        # Send the line
        logger.info(f"Sending line {i+1}/{len(lines)}: {line[:50]}{'...' if len(line) > 50 else ''}")
        pyautogui.write(line)
        
        if i < len(lines) - 1:
            logger.info("Sending Shift+Enter for newline...")
            if not send_keystrokes("shift+enter"):
                return False
            logger.info("Waiting 0.8 seconds after newline...")
            time.sleep(0.8)
        elif send_message:
            logger.info("Sending Enter to send message...")
            if not send_keystrokes("enter"):
                return False
            logger.info("Waiting 1 second after sending message...")
            time.sleep(1)
    
    logger.info("Prompt sent successfully!")
    return True

def kill_cursor(platform="cursor"):
    """Kill the Cursor or Windsurf application if it's running."""
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
    logger.info(f"Checking if {app_name} is running...")

    # Check if app is running
    check_script = f'''
    tell application "System Events"
        count (every process whose name is "{app_name}")
    end tell
    '''

    result = subprocess.run(["osascript", "-e", check_script], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip() != "0":
        logger.info(f"{app_name} is running, killing it...")
        subprocess.run(["pkill", "-x", app_name])
        logger.info(f"Waiting 2 seconds for process to fully terminate...")
        time.sleep(2)  # Wait longer for process to fully terminate
        logger.info("Done.")
    else:
        logger.info(f"{app_name} is not running.")


def launch_platform(platform_name="cursor", platform_type=None, project_path=None):
    """
    Launch Cursor or Windsurf and wait for it to be ready.

    Args:
        platform_name: Unique identifier for this platform instance
        platform_type: Type of platform ("cursor" or "windsurf"). If None, uses platform_name
        project_path: Path to the project to open
    """
    # If platform_type not provided, use platform_name as the type
    if platform_type is None:
        platform_type = platform_name

    is_windsurf = platform_type.lower() == "windsurf"
    app_name = "Windsurf" if is_windsurf else "Cursor"
    logger.info(f"Starting {app_name} for platform {platform_name}...")

    # Ensure the application is not already running (sometimes kill doesn't fully terminate)
    kill_cursor("windsurf" if is_windsurf else "cursor")
    time.sleep(1)  # Brief pause to ensure previous instances are terminated

    # Get list of processes before launch to compare later
    before_pids = set(_get_process_pids_by_name(app_name))
    logger.debug(f"Processes matching '{app_name}' before launch: {before_pids}")

    if project_path:
        logger.info(f"Launching {app_name} with project path: {project_path}")
        # Launch using open command
        result = subprocess.run(
            ["open", "-a", app_name, project_path], capture_output=True, text=True
        )

        if result.returncode != 0:
            logger.warning(f"Open command failed: {result.stderr}")
            # Method 2: Try with AppleScript if open command failed
            logger.info(f"Trying to launch {app_name} with AppleScript...")
            project_path_escaped = project_path.replace('"', '\\"')
            script = f"""
            tell application "{app_name}" to open "{project_path_escaped}"
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error(f"AppleScript launch failed: {result.stderr}")
                return False
    else:
        logger.warning(f"No project path provided for {platform_name} ({app_name})")
        result = subprocess.run(
            ["open", "-a", app_name], capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(f"Failed to launch {app_name}: {result.stderr}")
            return False

    # Wait for new process to appear by comparing PIDs before and after
    logger.info(f"Waiting for {app_name} process to start...")
    max_attempts = 30 if is_windsurf else 20  # Give more time for WindSurf
    detected_pid = None

    # Try to find the app bundle path to help with process detection
    app_path = None
    try:
        app_path_result = subprocess.run(
            ["mdfind", f"kMDItemCFBundleIdentifier == '*{app_name.lower()}*'"],
            capture_output=True,
            text=True,
        )
        if app_path_result.returncode == 0 and app_path_result.stdout.strip():
            app_path = os.path.basename(app_path_result.stdout.strip().split("\n")[0])
            logger.debug(f"Found potential app bundle: {app_path}")
    except Exception as e:
        logger.debug(f"Could not find app bundle path: {e}")

    for attempt in range(max_attempts):
        # Small delay to allow processes to start
        time.sleep(1)

        # Log progress on every 5th attempt
        if attempt % 5 == 0:
            logger.info(
                f"Waiting for {app_name} process... (attempt {attempt+1}/{max_attempts})"
            )

        # Get all variations of the app name
        app_variations = [
            app_name,
            app_name.lower(),
            app_name.title(),
            app_name.upper(),
        ]
        if "windsurf" in app_name.lower():
            app_variations.extend(["WindSurf", "Windsurf", "windsurf"])
        if app_path:
            app_variations.append(app_path)

        # Try to find PIDs for all variations
        all_pids = set()
        for variation in app_variations:
            variation_pids = set(_get_process_pids_by_name(variation))
            if variation_pids:
                logger.debug(f"Found PIDs for {variation}: {variation_pids}")
                all_pids.update(variation_pids)

        # Alternative method using ps command directly with grep (more thorough)
        try:
            alt_cmd = [
                "ps",
                "-A",
                "-o",
                "pid,comm",
                "|",
                "grep",
                "-i",
                app_name.lower(),
            ]
            alt_result = subprocess.run(
                " ".join(alt_cmd), shell=True, capture_output=True, text=True
            )
            if (
                alt_result.returncode == 0 or alt_result.returncode == 1
            ):  # grep returns 1 if no matches
                for line in alt_result.stdout.splitlines():
                    if line and not "grep" in line.lower():  # Skip grep process itself
                        parts = line.strip().split(None, 1)
                        if len(parts) >= 1:
                            try:
                                alt_pid = int(parts[0])
                                all_pids.add(alt_pid)
                                logger.debug(
                                    f"Found via grep: PID={alt_pid}, line={line}"
                                )
                            except ValueError:
                                pass
        except Exception as e:
            logger.debug(f"Alternative process detection failed: {e}")

        # Find new PIDs that weren't there before
        new_pids = all_pids - before_pids

        if new_pids:
            detected_pid = list(new_pids)[0]  # Just take the first one
            detected_name = _get_process_name_by_pid(detected_pid)
            logger.info(f"Detected new process: {detected_name} (PID: {detected_pid})")
            break

        if attempt == max_attempts - 1:
            logger.error(
                f"Failed to detect {app_name} process after {max_attempts} seconds"
            )
            return False

    if not detected_pid:
        logger.error(f"Could not detect a new process for {app_name}")
        return False

    # For Windsurf, try to press Enter to clear any dialog boxes
    if is_windsurf:
        logger.info("Pressing Enter to clear any dialog boxes in Windsurf...")
        script = f"""
        tell application "System Events"
            tell process id {detected_pid}
                key code 36  -- Enter key
            end tell
        end tell
        """
        subprocess.run(["osascript", "-e", script], capture_output=True)
        logger.info("Waiting 1 second after pressing Enter...")
        time.sleep(1)

    # Give it extra time to fully initialize
    extra_time = 8 if is_windsurf else 5  # Give WindSurf more initialization time
    logger.info(f"Waiting {extra_time} seconds for application to fully initialize...")
    time.sleep(extra_time)

    # Try to activate the window using the detected process or window title
    activation_success = False

    try:
        # Try by detected process ID first
        if detected_pid:
            script = f"""
            tell application "System Events"
                set proc to first process whose unix id is {detected_pid}
                set frontmost of proc to true
            end tell
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )
            activation_success = result.returncode == 0
            logger.info(
                f"Window activation by PID {detected_pid}: {'succeeded' if activation_success else 'failed'}"
            )

        # Also try activating with the specified window title if different
        from src.platforms.manager import PlatformManager

        platform_manager = globals().get("platform_manager", None)
        if platform_manager:
            platform_state = platform_manager.get_platform_state(platform_name)
            window_title = platform_state.get("window_title")
            if window_title:
                title_activation = activate_window(window_title)
                logger.info(
                    f"Window activation by title '{window_title}': {'succeeded' if title_activation else 'failed'}"
                )
                activation_success = activation_success or title_activation
    except Exception as e:
        logger.error(f"Error during window activation: {e}")

    if not activation_success:
        logger.warning(f"Could not activate window, but continuing...")
        # Try basic app activation as last resort
        try:
            subprocess.run(
                ["osascript", "-e", f'tell application "{app_name}" to activate'],
                capture_output=True,
            )
        except:
            pass

    logger.info(
        f"{platform_name} ({app_name}) launched successfully with PID {detected_pid}"
    )
    return True


def _get_process_pids_by_name(process_name):
    """
    Get PIDs of processes matching the given name
    """
    try:
        # Use ps command to find matching processes
        cmd = ["ps", "-A", "-o", "pid,comm"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            pids = []
            for line in result.stdout.splitlines()[1:]:  # Skip header line
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    pid_str, comm = parts
                    # More thorough check - case insensitive, handle paths containing the name
                    if (
                        process_name.lower() in comm.lower()
                        or process_name.lower() in os.path.basename(comm).lower()
                    ):
                        try:
                            pids.append(int(pid_str))
                            logger.debug(
                                f"Found matching process: PID={pid_str}, name={comm}"
                            )
                        except ValueError:
                            pass
            return pids
    except Exception as e:
        logger.error(f"Error getting process PIDs: {e}")

    return []


def _get_process_name_by_pid(pid):
    """
    Get the name of a process by its PID
    """
    try:
        cmd = ["ps", "-p", str(pid), "-o", "comm="]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.error(f"Error getting process name for PID {pid}: {e}")

    return "Unknown"


def activate_platform_window(platform_name, platform_state):
    """
    Activate a specific platform window by its title or platform type.

    Args:
        platform_name: The unique platform identifier
        platform_state: The platform state dictionary

    Returns:
        bool: True if activation was successful, False otherwise
    """
    window_title = platform_state.get("window_title")
    if not window_title:
        # Fall back to platform type
        platform_type = platform_state.get("platform_type", platform_name)
        window_title = "Windsurf" if platform_type.lower() == "windsurf" else "Cursor"

    logger.info(f"Activating window for {platform_name}: '{window_title}'")
    return activate_window(window_title)
