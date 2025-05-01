import platform
import pyautogui
import time
import logging
from typing import List, Optional

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

def send_keystroke_sequence(sequence: List[dict]) -> bool:
    """
    Send a sequence of keystrokes with delays.
    
    Args:
        sequence: List of dictionaries with 'keys' and 'delay_ms' keys
    
    Returns:
        bool: True if all keystrokes were sent successfully, False otherwise
    """
    try:
        for keystroke in sequence:
            if not send_keystrokes(keystroke['keys'], keystroke.get('delay_ms', 100)):
                logger.error(f"Failed to send keystroke: {keystroke}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error in keystroke sequence: {e}")
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