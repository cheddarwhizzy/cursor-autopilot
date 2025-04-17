#!/usr/bin/env python3.13
import time
import os
import hashlib
import json
from actions.send_to_cursor import send_prompt
from state import get_mode

WATCH_PATH = os.environ.get("WATCH_PATH", os.path.expanduser("~/cheddar/mushattention/mushattention"))
EXCLUDE_DIRS = {"node_modules", ".git", "dist", "__pycache__"}
LAST_HASH = None

# --- Configurable README tracking ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
else:
    config = {}
TASK_README_PATH = config.get("task_readme_path", "@src/notifications/README.md")
LAST_README_MTIME = None
TASK_COMPLETED = False
PLATFORM = config.get("platform", "cursor")

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
    global LAST_HASH, LAST_README_MTIME, TASK_COMPLETED
    inactivity_timer = 0
    # Initialize README mtime
    if os.path.exists(TASK_README_PATH):
        LAST_README_MTIME = os.path.getmtime(TASK_README_PATH)
    while True:
        time.sleep(5)
        new_hash = hash_folder_state()
        # Check if README was updated
        if os.path.exists(TASK_README_PATH):
            new_readme_mtime = os.path.getmtime(TASK_README_PATH)
            if LAST_README_MTIME is not None and new_readme_mtime > LAST_README_MTIME:
                print(f"Task README {TASK_README_PATH} was updated. Marking task as completed.")
                TASK_COMPLETED = True
            LAST_README_MTIME = new_readme_mtime
        if new_hash == LAST_HASH:
            inactivity_timer += 5
        else:
            inactivity_timer = 0
        LAST_HASH = new_hash
        if inactivity_timer >= 30 and get_mode() == "auto":
            print("No activity detected. Resending initial prompt to Cursor.")
            try:
                with open("initial_prompt.txt", "r") as f:
                    initial_prompt = f.read().strip()
            except Exception as e:
                print(f"Failed to read initial_prompt.txt: {e}")
                initial_prompt = "continue"
            # Use platform and task completion flag
            if TASK_COMPLETED:
                send_prompt(initial_prompt, platform=PLATFORM, new_chat=True, 
                          initial_delay=config.get("initial_delay", 10),
                          send_message=config.get("send_message", True))
                TASK_COMPLETED = False
            else:
                send_prompt(initial_prompt, platform=PLATFORM, new_chat=False,
                          send_message=config.get("send_message", True))
            inactivity_timer = 0

if __name__ == "__main__":
    run_watcher()
