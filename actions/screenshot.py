import subprocess
from datetime import datetime
import os

def capture_chat_screenshot():
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    print(f"Ensuring screenshot directory exists: {os.path.abspath(screenshot_dir)}")
    
    filename = f"screenshots/chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    abs_path = os.path.abspath(filename)
    print(f"Will save screenshot to: {abs_path}")
    
    # Get Cursor window bounds using AppleScript
    bounds_script = '''
    tell application "System Events"
        tell process "Cursor"
            try
                set win to first window whose name does not contain "Settings"
                return {position, size} of win
            on error
                return "error"
            end try
        end tell
    end tell
    '''
    
    bounds_result = subprocess.run(["osascript", "-e", bounds_script], capture_output=True, text=True)
    if bounds_result.returncode == 0 and bounds_result.stdout.strip() != "error":
        try:
            # Parse the bounds - format is "x, y, width, height"
            bounds = bounds_result.stdout.strip()
            print(f"Window bounds: {bounds}")
            
            # Split by comma and clean up the values
            parts = [int(p.strip().strip('{}')) for p in bounds.split(',')]
            window_x, window_y, window_width, window_height = parts
            
            # Calculate the chat region relative to the window position
            # Original values were 500,650,850,400
            x = window_x + 500
            y = window_y + 650
            width = 850
            height = 400
            
            # Capture the specific region
            capture_cmd = ["screencapture", "-R", f"{x},{y},{width},{height}", filename]
            print(f"Running capture command: {' '.join(capture_cmd)}")
            
            result = subprocess.run(capture_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                if os.path.exists(filename):
                    print(f"Screenshot saved successfully: {abs_path}")
                    print(f"File size: {os.path.getsize(filename)} bytes")
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
        print("Could not get Cursor window bounds")
        if bounds_result.stderr:
            print(f"Error output: {bounds_result.stderr}")
    
    return filename
