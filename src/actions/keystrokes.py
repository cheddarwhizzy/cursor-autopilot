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
        # Parse key combination
        if "+" in key_combo:
            parts = key_combo.split("+")
            # The last part is the key, everything before are modifiers
            key = parts[-1]
            modifiers = parts[:-1]

            # Map modifiers to AppleScript syntax
            modifier_map = {
                "command": "command down",
                "cmd": "command down",
                "control": "control down",
                "ctrl": "control down",
                "option": "option down",
                "alt": "option down",
                "shift": "shift down",
            }

            # Convert modifiers to AppleScript format
            applescript_modifiers = []
            for modifier in modifiers:
                if modifier.lower() in modifier_map:
                    applescript_modifiers.append(modifier_map[modifier.lower()])
                else:
                    logger.warning(f"Unknown modifier: {modifier}")
                    applescript_modifiers.append(f"{modifier} down")

            # Handle special keys that need mapping
            key_map = {
                "enter": "return",
                "`": '"`"',  # Backtick needs to be quoted
                "space": '" "',  # Space needs to be quoted
                "tab": "tab",
                "escape": "escape",
                "delete": "delete",
                "backspace": "delete",
            }

            # Map the key if needed
            if key.lower() in key_map:
                applescript_key = key_map[key.lower()]
            else:
                # Quote the key for AppleScript
                applescript_key = f'"{key}"'

            # Build the AppleScript
            if len(applescript_modifiers) == 1:
                modifier_clause = applescript_modifiers[0]
            else:
                modifier_clause = "{" + ", ".join(applescript_modifiers) + "}"

            script = f"""
            tell application "System Events"
                tell process "{app_name}"
                    keystroke {applescript_key} using {modifier_clause}
                end tell
            end tell
            """
        else:
            # Single key - handle special keys
            key_map = {
                "enter": "return",
                "`": '"`"',  # Backtick needs to be quoted
                "space": '" "',  # Space needs to be quoted
                "tab": "tab",
                "escape": "escape",
                "delete": "delete",
                "backspace": "delete",
            }

            if key_combo.lower() in key_map:
                applescript_key = key_map[key_combo.lower()]
            else:
                applescript_key = f'"{key_combo}"'

            script = f"""
            tell application "System Events"
                tell process "{app_name}"
                    keystroke {applescript_key}
                end tell
            end tell
            """

        logger.debug(f"[{platform}] Generated AppleScript: {script.strip()}")

        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(
                f"AppleScript error for keystroke '{key_combo}': {result.stderr}"
            )
            return False

        return True
    except Exception as e:
        logger.error(f"Error sending keystroke '{key_combo}': {e}")
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
    Send a text string to Cursor or Windsurf with proper newline handling.

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
        # Split text by lines to handle newlines properly
        lines = text.split('\n')
        
        for line_idx, line in enumerate(lines):
            if line:  # Only process non-empty lines
                # Split line into smaller chunks to avoid issues with very long texts
                chunk_size = 500
                for i in range(0, len(line), chunk_size):
                    chunk = line[i : i + chunk_size]
                    # Escape quotes and backslashes for AppleScript
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

                    # Add small delay between chunks
                    if i + chunk_size < len(line):
                        time.sleep(0.1)
            
            # Add newline (shift+enter) if not the last line
            if line_idx < len(lines) - 1:
                logger.debug(f"[{platform}] Adding newline with shift+enter")
                script = f"""
                tell application "System Events"
                    tell process "{app_name}"
                        keystroke return using shift down
                    end tell
                end tell
                """
                result = subprocess.run(
                    ["osascript", "-e", script], capture_output=True, text=True
                )
                if result.returncode != 0:
                    logger.error(f"AppleScript error sending shift+enter: {result.stderr}")
                    return False
                
                # Add delay between newlines as requested (0.8 seconds)
                time.sleep(0.8)

        # Send Enter after typing if requested (to actually send the message)
        if send_message:
            logger.debug(f"[{platform}] Sending final Enter to submit message")
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
