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
TASK_README_PATH = config.get("task_readme_path", "@src/notifications/README.md")
LAST_README_MTIME = None
TASK_COMPLETED = False
PLATFORM = config.get("platform", "cursor")

# Add debug info about paths
print(f"\nWatcher Configuration:")
print(f"Project Path: {WATCH_PATH}")
print(f"Task README: {TASK_README_PATH}")
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
    Watch directory for changes and trigger prompts based on inactivity.
    """
    global LAST_HASH, LAST_README_MTIME, TASK_COMPLETED, FILE_MTIMES
    inactivity_timer = 0
    last_check_time = time.time()
    
    # Initialize README mtime
    if os.path.exists(TASK_README_PATH):
        LAST_README_MTIME = os.path.getmtime(TASK_README_PATH)
        print(f"Initialized watching task README at: {TASK_README_PATH}")
    
    print(f"\nStarting file watcher for directory: {WATCH_PATH}")
    print(f"Excluded directories: {EXCLUDE_DIRS}")
    print("Watching for changes...")
    
    while True:
        try:
            time.sleep(5)
            current_time = time.time()
            elapsed = current_time - last_check_time
            
            # Check if project directory exists
            if not os.path.exists(WATCH_PATH):
                print(f"\n⚠️  Warning: Project directory not found: {WATCH_PATH}")
                print("Waiting for directory to become available...")
                last_check_time = current_time
                continue
            
            new_hash, changed_files, total_files = hash_folder_state()
            
            # Check if README was updated
            readme_updated = False
            if os.path.exists(TASK_README_PATH):
                new_readme_mtime = os.path.getmtime(TASK_README_PATH)
                if LAST_README_MTIME is not None and new_readme_mtime > LAST_README_MTIME:
                    print(f"\n🎯 Task README {TASK_README_PATH} was updated!")
                    print("Marking task as completed - next prompt will start a new chat")
                    TASK_COMPLETED = True
                    readme_updated = True
                LAST_README_MTIME = new_readme_mtime
            
            if new_hash == LAST_HASH:
                inactivity_timer += elapsed
                if inactivity_timer >= 30:  # Only log status when getting close to timeout
                    print(f"\n⏳ No changes detected for {int(inactivity_timer)} seconds")
                    print(f"Will send continuation prompt in {max(0, 60-int(inactivity_timer))} seconds")
                    print(f"Currently watching {total_files} files")
            else:
                if changed_files:
                    print(f"\n📝 Detected changes in {len(changed_files)} files:")
                    for f in changed_files[:5]:  # Show up to 5 changed files
                        print(f"  - {f}")
                    if len(changed_files) > 5:
                        print(f"  ... and {len(changed_files)-5} more files")
                    print(f"Resetting inactivity timer (was at {int(inactivity_timer)} seconds)")
                inactivity_timer = 0
            
            LAST_HASH = new_hash
            last_check_time = current_time
            
            if inactivity_timer >= 60 and get_mode() == "auto":
                print("\n⚡ Inactivity timeout reached. Sending prompt to Cursor.")
                # Use platform and task completion flag
                if TASK_COMPLETED:
                    try:
                        with open("initial_prompt.txt", "r") as f:
                            initial_prompt = f.read().strip()
                    except Exception as e:
                        print(f"Failed to read initial_prompt.txt: {e}")
                        initial_prompt = "continue"
                    print("Starting new chat with initial prompt (task was completed)")
                    send_prompt(initial_prompt, platform=PLATFORM, new_chat=True, 
                              initial_delay=config.get("initial_delay", 10),
                              send_message=config.get("send_message", True))
                    TASK_COMPLETED = False
                else:
                    # Use the continuation prompt for subsequent prompts
                    prompt = CONTINUATION_PROMPT.format(
                        task_readme_path=config.get("task_readme_path", "@src/notifications/README.md"),
                        important_llm_docs_path=config.get("important_llm_docs_path", "docs/structure/*.md")
                    )
                    print("Sending continuation prompt (no task completion)")
                    send_prompt(prompt, platform=PLATFORM, new_chat=False,
                              send_message=config.get("send_message", True))
                inactivity_timer = 0
                print("\nWatching for changes...")
        except Exception as e:
            print(f"\n⚠️  Error in watcher: {e}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    run_watcher()
