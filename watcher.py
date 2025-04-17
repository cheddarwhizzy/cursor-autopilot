import time
import os
import hashlib
from actions.send_to_cursor import send_prompt
from state import get_mode

WATCH_PATH = os.environ.get("WATCH_PATH", os.path.expanduser("~/cheddar/mushattention/mushattention"))
EXCLUDE_DIRS = {"node_modules", ".git", "dist", "__pycache__"}
LAST_HASH = None

def hash_folder_state():
    sha = hashlib.sha256()
    for root, dirs, files in os.walk(WATCH_PATH):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith(".tmp"): continue
            path = os.path.join(root, f)
            sha.update(f.encode())
            sha.update(str(os.path.getmtime(path)).encode())
    return sha.hexdigest()

def run_watcher():
    global LAST_HASH
    inactivity_timer = 0
    while True:
        time.sleep(5)
        new_hash = hash_folder_state()

        if new_hash == LAST_HASH:
            inactivity_timer += 1
        else:
            inactivity_timer = 0

        LAST_HASH = new_hash

        if inactivity_timer >= 6 and get_mode() == "auto":
            print("No activity detected. Sending 'continue' to Cursor.")
            send_prompt("continue")
            inactivity_timer = 0

if __name__ == "__main__":
    run_watcher()
