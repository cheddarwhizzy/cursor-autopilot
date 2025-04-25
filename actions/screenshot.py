import os
import subprocess
import logging
from utils.colored_logging import setup_colored_logging

# Configure logging
setup_colored_logging(debug=os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('screenshot')

def take_screenshot(filename="screenshot.png", platform="cursor"):
    """
    Takes a screenshot of the Cursor/Windsurf window and saves it as filename.
    Returns the path to the screenshot, or None if failed.
    """
    screenshot_dir = os.path.dirname(filename)
    if not os.path.exists(screenshot_dir):
        logger.info(f"Ensuring screenshot directory exists: {os.path.abspath(screenshot_dir)}")
        os.makedirs(screenshot_dir, exist_ok=True)
    
    abs_path = os.path.abspath(filename)
    logger.info(f"Will save screenshot to: {abs_path}")
    
    # Get window bounds using AppleScript
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
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
                    if winName contains "—" or winName contains "-" then
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
                    logger.info(f"Screenshot saved successfully: {abs_path}")
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
        logger.error("Could not get Cursor window bounds")
        if bounds_result.stderr:
            logger.error(f"Error output: {bounds_result.stderr}")
    
    return None

def capture_chat_screenshot(filename="chat_screenshot.png", platform="cursor"):
    """
    Takes a screenshot of the chat window in Cursor/Windsurf and saves it as filename.
    Returns the path to the screenshot, or None if failed.
    """
    screenshot_dir = os.path.dirname(filename)
    if not os.path.exists(screenshot_dir):
        logger.info(f"Ensuring screenshot directory exists: {os.path.abspath(screenshot_dir)}")
        os.makedirs(screenshot_dir, exist_ok=True)
    
    abs_path = os.path.abspath(filename)
    logger.info(f"Will save chat screenshot to: {abs_path}")
    
    # Get chat window bounds using AppleScript
    app_name = "Windsurf" if platform == "windsurf" else "Cursor"
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
                    if winName contains "Chat" or winName contains "Assistant" then
                        set pos to position of w
                        set sz to size of w
                        return {{(item 1 of pos), (item 2 of pos), (item 1 of sz), (item 2 of sz)}}
                    end if
                end repeat
                error "No chat window found"
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
            logger.debug(f"Chat window bounds: {bounds}")
            
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
                    logger.info(f"Chat screenshot saved successfully: {abs_path}")
                    logger.debug(f"File size: {os.path.getsize(filename)} bytes")
                    return filename
                else:
                    logger.warning(f"Warning: screencapture returned success but file not found at {abs_path}")
            else:
                logger.error(f"Failed to capture chat screenshot. Return code: {result.returncode}")
                if result.stderr:
                    logger.error(f"Error output: {result.stderr}")
        except Exception as e:
            logger.error(f"Error parsing chat window bounds: {e}")
            logger.error(f"Raw bounds output: {bounds}")
    else:
        logger.error("Could not get chat window bounds")
        if bounds_result.stderr:
            logger.error(f"Error output: {bounds_result.stderr}")
    
    return None
