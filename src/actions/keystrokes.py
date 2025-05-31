import platform
import pyautogui
import time
import logging
from typing import List, Optional
import subprocess

logger = logging.getLogger(__name__)

def map_key(key: str) -> str:
    """
    Map platform-specific keys to their equivalents.
    For example, 'command' becomes 'ctrl' on Windows/Linux.
    """
    os_name = platform.system().lower()

    # Map command key
    if key.lower() == 'command':
        if os_name == 'windows' or os_name == 'linux':
            return 'ctrl'
        return 'command'

    # Map option/alt key
    if key.lower() == 'option':
        if os_name == 'windows' or os_name == 'linux':
            return 'alt'
        return 'option'

    # Map control key
    if key.lower() == "control":
        return "ctrl"

    return key

def send_keystrokes(keys: str, delay_ms: int = 100) -> bool:
    """
    Send keystrokes using pyautogui with platform-specific key mapping.
    
    Args:
        keys: String of keys to press, e.g. "command+shift+p"
        delay_ms: Delay in milliseconds after sending keystrokes
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Split the keys and map them to platform-specific equivalents
        key_parts = keys.split('+')
        mapped_keys = [map_key(key) for key in key_parts]

        # Validate keys
        valid_keys = set(pyautogui.KEYBOARD_KEYS)
        for key in mapped_keys:
            if key.lower() not in valid_keys:
                logger.error(f"Invalid key: {key}")
                return False

        # Send the keystrokes
        if len(mapped_keys) == 1:
            pyautogui.press(mapped_keys[0])
        else:
            pyautogui.hotkey(*mapped_keys)

        # Add delay if specified
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

        return True
    except Exception as e:
        logger.error(f"Error sending keystrokes {keys}: {e}")
        return False


def send_keystroke(key_combo: str, platform: str = "cursor") -> bool:
    """
    Send a keystroke to Cursor or Windsurf.

    Args:
        key_combo: The keystroke combination to send (e.g., 'command+l', 'control+c')
        platform: Platform identifier or type (e.g., 'cursor_project', 'windsurf_project')

    Returns:
        bool: True if successful, False otherwise
    """
    # Detect platform type from name (default to the name itself if no '_' separator)
    platform_type = platform.split("_")[0] if "_" in platform else platform
    app_name = "Windsurf" if platform_type.lower() == "windsurf" else "Cursor"

    logger.debug(f"[{platform}] Sending keystroke: {key_combo}")

    try:
        # Normalize key combo format
        if "+" in key_combo:
            parts = key_combo.split("+")
            modifier = parts[0]
            key = parts[1]

            # Map to specific key codes based on platform
            script = f"""
            tell application "System Events"
                tell process "{app_name}"
                    keystroke "{key}" using {modifier} down
                end tell
            end tell
            """
        else:
            # Single key
            key = key_combo
            script = f"""
            tell application "System Events"
                tell process "{app_name}"
                    keystroke "{key}"
                end tell
            end tell
            """

        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(f"AppleScript error: {result.stderr}")
            return False

        return True
    except Exception as e:
        logger.error(f"Error sending keystroke: {e}")
        return False


def send_keystroke_sequence(key_sequence: list, platform: str = "cursor") -> bool:
    """
    Send a sequence of keystrokes.

    Args:
        key_sequence: List of keystroke dictionaries with 'keys' and optional 'delay_ms'
        platform: Platform identifier or type

    Returns:
        bool: True if all keystrokes were sent successfully
    """
    for item in key_sequence:
        keys = item.get("keys")
        delay_ms = item.get("delay_ms", 0)

        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

        if not send_keystroke(keys, platform):
            return False

    return True


def send_keystroke_string(
    text: str, platform: str = "cursor", send_message: bool = True
) -> bool:
    """
    Send a text string to Cursor or Windsurf.

    Args:
        text: The text to send
        platform: Platform identifier or type
        send_message: Whether to send Enter after typing the text

    Returns:
        bool: True if successful
    """
    platform_type = platform.split("_")[0] if "_" in platform else platform
    app_name = "Windsurf" if platform_type.lower() == "windsurf" else "Cursor"

    logger.debug(f"[{platform}] Typing string of {len(text)} characters")

    try:
        # Split text into smaller chunks to avoid issues with very long texts
        chunk_size = 500
        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            # Escape quotes and backslashes
            escaped_chunk = chunk.replace("\\", "\\\\").replace('"', '\\"')

            script = f"""
            tell application "System Events"
                tell process "{app_name}"
                    keystroke "{escaped_chunk}"
                end tell
            end tell
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error(f"AppleScript error while typing: {result.stderr}")
                return False

            # Add small delay between chunks to avoid overwhelming the application
            if i + chunk_size < len(text):
                time.sleep(0.2)

        # Send Enter after typing if requested
        if send_message:
            script = f"""
            tell application "System Events"
                tell process "{app_name}"
                    keystroke return
                end tell
            end tell
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )
            if result.returncode != 0:
                logger.error(f"AppleScript error sending Enter: {result.stderr}")
                return False

        return True
    except Exception as e:
        logger.error(f"Error sending keystrokes: {e}")
        return False


def activate_window(window_title: str) -> bool:
    """
    Activate a window by its title.
    
    Args:
        window_title: Title of the window to activate
    
    Returns:
        bool: True if window was activated, False otherwise
    """
    try:
        # On Windows, use pyautogui's built-in window activation
        if platform.system().lower() == 'windows':
            pyautogui.getWindowsWithTitle(window_title)[0].activate()
            return True
        
        # On macOS, use AppleScript
        elif platform.system().lower() == 'darwin':
            import subprocess
            script = f'''
            tell application "{window_title}"
                activate
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            return result.returncode == 0
        
        # On Linux, use wmctrl
        elif platform.system().lower() == 'linux':
            import subprocess
            result = subprocess.run(['wmctrl', '-a', window_title], capture_output=True, text=True)
            return result.returncode == 0
        
        return False
    except Exception as e:
        logger.error(f"Error activating window {window_title}: {e}")
        return False 
