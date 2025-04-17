import subprocess
from datetime import datetime
import os

def capture_chat_screenshot():
    os.makedirs("screenshots", exist_ok=True)
    filename = f"screenshots/chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    subprocess.run(["screencapture", "-R500,650,850,400", filename])
    return filename
