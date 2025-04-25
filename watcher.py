#!/usr/bin/env python3.13
import time
import os
import hashlib
import json
from datetime import datetime
from actions.send_to_cursor import send_prompt
from state import get_mode
from generate_initial_prompt import CONTINUATION_PROMPT

EXCLUDE_DIRS = {"node_modules", ".git", "dist", "__pycache__"}
LAST_HASH = None
FILE_MTIMES = {}

# --- Configurable README tracking ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
else:
    config = {}

# Get paths from config
WATCH_PATH = os.path.expanduser(config.get("project_path", "~/cheddar/mushattention/mushattention"))
TASK_FILE_PATH = config.get("task_file_path", "tasks.md")
LAST_README_MTIME = None
TASK_COMPLETED = False
PLATFORM = config.get("platform", "cursor")

# Add debug info about paths
print(f"\nWatcher Configuration:")
print(f"Project Path: {WATCH_PATH}")
print(f"Task README: {TASK_FILE_PATH}")
print(f"Task README: {TASK_FILE_PATH}")
print(f"Platform: {PLATFORM}")
print(f"Excluded Dirs: {EXCLUDE_DIRS}")

def hash_folder_state():
    """
    Scan directory for changes and return:
    - A hash representing the current state
    - List of files that changed since last scan
    - Total number of files being watched
    """
    sha = hashlib.sha256()
    changed_files = []
    total_files = 0
    
    # Walk through directory
    for root, dirs, files in os.walk(WATCH_PATH):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        # Process each file
        for filename in sorted(files):  # Sort for consistent ordering
            if filename.endswith(".tmp"): 
                continue
                
            abs_path = os.path.join(root, filename)
            rel_path = os.path.relpath(abs_path, WATCH_PATH)
            
            try:
                # Get file stats
                stats = os.stat(abs_path)
                current_mtime = stats.st_mtime
                current_size = stats.st_size
                
                # Create a unique hash for this file's state
                file_state = f"{rel_path}:{current_mtime}:{current_size}"
                sha.update(file_state.encode())
                
                # Check if file changed
                last_mtime = FILE_MTIMES.get(abs_path, {}).get('mtime')
                last_size = FILE_MTIMES.get(abs_path, {}).get('size')
                
                if last_mtime is None or last_size is None or \
                   current_mtime > last_mtime or current_size != last_size:
                    changed_files.append(rel_path)
                    FILE_MTIMES[abs_path] = {
                        'mtime': current_mtime,
                        'size': current_size
                    }
                
                total_files += 1
                
            except OSError as e:
                print(f"Warning: Could not access {rel_path}: {e}")
                continue
    
    return sha.hexdigest(), changed_files, total_files

def run_watcher():
    """
    Main watcher loop that monitors for changes and sends prompts.
    """
    global LAST_HASH, FILE_MTIMES, LAST_README_MTIME, TASK_COMPLETED
    
    inactivity_timer = 0
    last_activity = time.time()
    last_prompt_time = 0  # Track when we last sent a prompt
    
    # Check if initial prompt has been sent
    initial_prompt_sent = os.path.exists(os.path.join(os.path.dirname(__file__), ".initial_prompt_sent"))
    print(f"\n📝 Initial prompt {'has' if initial_prompt_sent else 'has not'} been sent yet")
    
    while True:
        try:
            # Get current state
            current_hash, changed_files, total_files = hash_folder_state()
            
            # Check if task file was modified
            task_file_modified = False
            if TASK_FILE_PATH in changed_files:
                current_mtime = os.path.getmtime(TASK_FILE_PATH)
                if LAST_README_MTIME is None or current_mtime > LAST_README_MTIME:
                    task_file_modified = True
                    LAST_README_MTIME = current_mtime
                    print(f"\n📝 Task file {TASK_FILE_PATH} was modified!")
            
            # Update inactivity timer
            if current_hash != LAST_HASH or task_file_modified:
                inactivity_timer = 0
                last_activity = time.time()
                LAST_HASH = current_hash
                print(f"\n🔄 Activity detected! Resetting inactivity timer (was at {int(inactivity_timer)} seconds)")
            else:
                inactivity_timer = time.time() - last_activity
                if inactivity_timer >= 30:  # Log status when getting close to timeout
                    print(f"\n⏳ No changes detected for {int(inactivity_timer)} seconds")
                    print(f"Will send prompt in {max(0, 120-int(inactivity_timer))} seconds if no changes occur")
            
            # Check for inactivity timeout (2 minutes = 120 seconds)
            if inactivity_timer >= 120 and get_mode() == "auto":
                current_time = time.time()
                # Only send a new prompt if it's been at least 2 minutes since the last one
                if current_time - last_prompt_time >= 120:
                    print(f"\n⚡ Inactivity timeout reached ({int(inactivity_timer)} seconds). Sending prompt to {PLATFORM}.")
                    
                    # Use the appropriate prompt based on whether initial prompt was sent
                    if not initial_prompt_sent:
                        try:
                            with open("initial_prompt.txt", "r") as f:
                                prompt = f.read().strip()
                        except Exception as e:
                            print(f"Failed to read initial_prompt.txt: {e}")
                            prompt = "continue"
                        print("Starting new chat with initial prompt")
                        send_prompt(prompt, platform=PLATFORM, new_chat=True, 
                                  initial_delay=config.get("initial_delay", 10),
                                  send_message=config.get("send_message", True))
                        initial_prompt_sent = True
                    else:
                        # Use the continuation prompt
                        prompt = CONTINUATION_PROMPT.format(
                            task_file_path=config.get("task_file_path", "tasks.md"),
                            additional_context_path=config.get("additional_context_path", "context.md")
                        )
                        print("Sending continuation prompt")
                        send_prompt(prompt, platform=PLATFORM, new_chat=False,
                                  send_message=config.get("send_message", True))
                    
                    last_prompt_time = current_time
                    inactivity_timer = 0
                    print("\n👀 Watching for changes...")
                else:
                    print(f"\n⏳ Skipping prompt - last prompt was sent {int(current_time - last_prompt_time)} seconds ago")
            
            time.sleep(5)  # Check every 5 seconds
        except Exception as e:
            print(f"\n⚠️  Error in watcher: {e}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    run_watcher()
