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
    Activate a window on macOS using AppleScript with improved case-insensitive matching
    """
    # Try with better case-insensitive matching and process enumeration
    script = f"""
    set targetTitle to "{title}"
    try
        tell application "System Events"
            -- Try multiple variations of case-insensitive matching
            set matchingProcesses to (processes whose (name contains targetTitle or title of windows contains targetTitle))
            
            if (count of matchingProcesses) > 0 then
                set targetProcess to item 1 of matchingProcesses
                set frontmost of targetProcess to true
                log "Activated process by name match: " & name of targetProcess
                
                -- Try to focus on the specific window within the process if possible
                try
                    tell targetProcess
                        set winList to windows whose title contains targetTitle
                        if (count of winList) > 0 then
                            set index of item 1 of winList to 1
                            log "Successfully focused specific window within application"
                        end if
                    end tell
                end try
                
                return true -- Indicate success
            else
                -- If no match by name, try a broader search with windows
                log "No direct process match, trying windows containing title"
                
                set anyMatches to false
                repeat with theProcess in processes
                    try
                        tell theProcess
                            set winList to windows whose title contains targetTitle
                            if (count of winList) > 0 then
                                set frontmost of theProcess to true
                                set index of item 1 of winList to 1
                                log "Found and activated window with matching title in: " & name of theProcess
                                set anyMatches to true
                                exit repeat -- Exit after first match
                            end if
                        end tell
                    end try
                end repeat
                
                if anyMatches then
                    return true
                else
                    log "No window found containing title: " & targetTitle
                    -- Final fallback: Try activating app by name (multiple case variations)
                    try
                        tell application targetTitle to activate
                        log "Activated application by exact name: " & targetTitle
                        return true
                    on error
                        try
                            set titleLower to do shell script "echo " & quoted form of targetTitle & " | tr '[:upper:]' '[:lower:]'"
                            tell application titleLower to activate
                            log "Activated application by lowercase name: " & titleLower
                            return true
                        on error
                            -- Simpler approach without AWK
                            try
                                set firstChar to (text 1 thru 1 of targetTitle)
                                set restChars to (text 2 thru (length of targetTitle) of targetTitle)
                                set titleProper to (do shell script "echo " & quoted form of firstChar & " | tr '[:lower:]' '[:upper:]'") & restChars
                                tell application titleProper to activate
                                log "Activated application with capitalized first letter: " & titleProper
                                return true
                            on error errMsg3 number errNum3
                                log "All activation methods failed: " & errMsg3
                                return false
                            end try
                        end try
                    end try
                end if
            end if
        end tell
    on error errMsg number errNum
        log "Error in window activation script: " & errMsg
        return false
    end try
    """

    # Use capture_output=True to get logs from AppleScript
    result = subprocess.run(['osascript', '-e', script], check=False, capture_output=True, text=True)
    if result.returncode == 0 and "Activated" in result.stdout:
        logger.debug(f"Successfully activated window/process containing '{title}'. Output: {result.stdout.strip()}")
        return True
    else:
        logger.warning(f"Could not activate window/process containing '{title}'. Error: {result.stderr.strip()} Output: {result.stdout.strip()}")

        # Add a final fallback for common variations
        variations = [title, title.lower(), title.upper(), title.title()]
        # Add a version where "WindSurf" becomes "Windsurf"
        if "WindSurf" in title:
            variations.append(title.replace("WindSurf", "Windsurf"))
        if "Windsurf" in title:
            variations.append(title.replace("Windsurf", "WindSurf"))

        for variation in variations:
            if variation == title:
                continue  # Skip the original title we already tried

            logger.debug(
                f"Trying fallback activation with title variation: '{variation}'"
            )
            simple_script = f'tell application "{variation}" to activate'
            result = subprocess.run(
                ["osascript", "-e", simple_script],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.debug(
                    f"Successfully activated using title variation: '{variation}'"
                )
                return True

        logger.warning(f"All activation attempts failed for window title: '{title}'")
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
