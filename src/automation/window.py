#!/usr/bin/env python3
import os
import platform as platform_module
import subprocess
import logging
import time

logger = logging.getLogger('watcher.automation.window')

def activate_window(title):
    """
    Activate a window by its title (or part of it).
    
    Args:
        title: The window title or part of the title to match
        
    Returns:
        bool: True if successfully activated, False otherwise
    """
    if not title:
        logger.warning("activate_window called with empty title.")
        return False
        
    try:
        logger.debug(f"Attempting to activate window containing title: '{title}'")
        current_os = platform_module.system()

        if current_os == "Darwin":
            # For macOS, use AppleScript
            return _activate_window_macos(title)
        elif current_os == "Windows":
            # For Windows, use win32gui if available
            return _activate_window_windows(title)
        elif current_os == "Linux":
            # For Linux, use wmctrl or xdotool
            return _activate_window_linux(title)
        else:
            logger.error(f"Unsupported OS for window activation: {current_os}")
            return False
            
    except Exception as e:
        logger.error(f"Error activating window with title '{title}': {e}", exc_info=True)
        return False

def _activate_window_macos(title):
    """
    Activate a window on macOS using AppleScript
    """
    # Try activating by finding a process containing the title
    script = f'''
    set targetTitle to "{title}"
    try
        tell application "System Events"
            set matchingProcesses to (processes whose name contains targetTitle or title contains targetTitle)
            if (count of matchingProcesses) > 0 then
                set targetProcess to item 1 of matchingProcesses
                set frontmost of targetProcess to true
                log "Activated process: " & name of targetProcess
                return true -- Indicate success
            else
                log "No process found containing title: " & targetTitle
                -- Fallback: Try activating app by name if title matches app name
                try
                    tell application targetTitle to activate
                    log "Activated application by name: " & targetTitle
                    return true
                on error errMsg number errNum
                    log "Fallback activation by name failed: " & errMsg
                    return false
                end try
            end if
        end tell
    on error errMsg number errNum
        log "Error activating window: " & errMsg
        return false
    end try
    '''
    # Use capture_output=True to get logs from AppleScript
    result = subprocess.run(['osascript', '-e', script], check=False, capture_output=True, text=True)
    if result.returncode == 0 and "Activated" in result.stdout:
        logger.debug(f"Successfully activated window/process containing '{title}'. Output: {result.stdout.strip()}")
        return True
    else:
        logger.warning(f"Could not activate window/process containing '{title}'. Error: {result.stderr.strip()} Output: {result.stdout.strip()}")
        return False

def _activate_window_windows(title):
    """
    Activate a window on Windows using win32gui if available
    """
    try:
        import win32gui
        import win32con
        
        # Find window - potentially partial match needed? FindWindow is exact match.
        # EnumWindows might be needed for partial match. Sticking to exact for now.
        hwnd = win32gui.FindWindow(None, title)
        if hwnd:
            # Restore if minimized, then bring to front
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            logger.debug(f"Activated window '{title}' on Windows (HWND: {hwnd})")
            return True
        else:
            logger.warning(f"Window '{title}' not found on Windows using exact match.")
            # TODO: Implement EnumWindows fallback for partial title match if needed
            return False
    except ImportError:
        logger.warning("win32gui not available for window activation on Windows.")
        return False
    except Exception as e:
        logger.error(f"Error activating window '{title}' on Windows: {e}")
        return False

def _activate_window_linux(title):
    """
    Activate a window on Linux using wmctrl or xdotool
    """
    try:
        # Use wmctrl or xdotool - prefer wmctrl as it's often more reliable
        # Activate by bringing window containing title to current desktop and raising
        logger.debug(f"Trying to activate window '{title}' using wmctrl...")
        cmd = ['wmctrl', '-a', title]
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            logger.debug(f"Activated window containing '{title}' on Linux using wmctrl.")
            return True
        else:
            logger.warning(f"wmctrl activation failed (code: {result.returncode}, is wmctrl installed?). Error: {result.stderr.strip()}")
            # Fallback to xdotool
            try:
                logger.debug(f"Trying to activate window '{title}' using xdotool...")
                cmd_xdo = ['xdotool', 'search', '--name', title, 'windowactivate', '%@']
                result_xdo = subprocess.run(cmd_xdo, check=False, capture_output=True, text=True)
                if result_xdo.returncode == 0:
                    logger.debug(f"Activated window containing '{title}' on Linux using xdotool.")
                    return True
                else:
                    logger.warning(f"xdotool activation also failed (code: {result_xdo.returncode}). Error: {result_xdo.stderr.strip()}")
                    return False
            except FileNotFoundError:
                logger.warning("xdotool not found for Linux window activation fallback.")
                return False
            except Exception as e_xdo:
                logger.error(f"Error during xdotool fallback for '{title}': {e_xdo}")
                return False
    except FileNotFoundError:
        logger.warning("wmctrl not found. Cannot activate window on Linux.")
        return False
    except Exception as e_linux:
        logger.error(f"Error activating window '{title}' on Linux: {e_linux}")
        return False 