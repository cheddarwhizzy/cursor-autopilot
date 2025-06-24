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
    Activate a window on macOS using AppleScript with simple and reliable approach
    """
    logger.debug(f"Attempting to activate window/app: '{title}'")
    
    # For window titles that contain project names, try to activate the parent application first
    app_name = None
    if "windsurf" in title.lower() or "meanscoop" in title.lower():
        app_name = "Windsurf"
    elif "cursor" in title.lower():
        app_name = "Cursor"
    
    # If we identified an app, try activating it directly first
    if app_name:
        logger.debug(f"Trying to activate application directly: '{app_name}'")
        simple_script = f'tell application "{app_name}" to activate'
        result = subprocess.run(
            ["osascript", "-e", simple_script],
            check=False,
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            logger.debug(f"Successfully activated application: '{app_name}'")
            # Add a small delay to ensure activation takes effect
            time.sleep(0.5)
            
            # Also try to bring to front using System Events
            try:
                front_script = f"""
                tell application "System Events"
                    tell process "{app_name}"
                        set frontmost to true
                    end tell
                end tell
                """
                subprocess.run(["osascript", "-e", front_script], 
                             check=False, capture_output=True, text=True)
                logger.debug(f"Also brought '{app_name}' to front via System Events")
            except:
                pass  # Don't fail if this doesn't work
            
            return True
        else:
            logger.debug(f"Failed to activate '{app_name}': {result.stderr.strip()}")
    
    # If direct app activation failed, try variations of the title
    variations = [title]
    
    # Add common variations based on the title
    if "windsurf" in title.lower():
        variations.extend(["WindSurf", "Windsurf", "windsurf"])
    elif "cursor" in title.lower():
        variations.extend(["Cursor", "cursor"])
    else:
        # Generic variations
        variations.extend([title.lower(), title.upper(), title.title()])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for v in variations:
        if v not in seen:
            seen.add(v)
            unique_variations.append(v)
    
    # Try each variation with simple activation
    for variation in unique_variations:
        logger.debug(f"Trying to activate application: '{variation}'")
        
        # Simple application activation
        simple_script = f'tell application "{variation}" to activate'
        result = subprocess.run(
            ["osascript", "-e", simple_script],
            check=False,
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            logger.debug(f"Successfully activated application: '{variation}'")
            time.sleep(0.5)
            return True
        else:
            logger.debug(f"Failed to activate '{variation}': {result.stderr.strip()}")
    
    # If all simple activations failed, try process-based activation
    logger.debug(f"Simple activation failed, trying process-based activation for '{title}'")
    
    # Try to find and activate any process containing parts of the title
    search_terms = []
    if app_name:
        search_terms.append(app_name)
    search_terms.extend([title, title.split('-')[0], title.split('—')[0]])
    
    for search_term in search_terms:
        if not search_term.strip():
            continue
            
        complex_script = f"""
        try
            tell application "System Events"
                set searchTerm to "{search_term.strip()}"
                set matchingProcesses to (processes whose name contains searchTerm)
                
                if (count of matchingProcesses) > 0 then
                    set targetProcess to item 1 of matchingProcesses
                    set frontmost of targetProcess to true
                    return "success"
                end if
            end tell
            return "no_match"
        on error errMsg
            return "error: " & errMsg
        end try
        """
        
        result = subprocess.run(['osascript', '-e', complex_script], 
                              check=False, capture_output=True, text=True)
        
        if result.returncode == 0 and "success" in result.stdout:
            logger.debug(f"Successfully activated via process matching with term '{search_term}': '{title}'")
            return True
    
    logger.warning(f"All activation attempts failed for: '{title}'")
    logger.debug(f"Last attempt output: {result.stdout.strip()}, error: {result.stderr.strip()}")
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
