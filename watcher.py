#!/usr/bin/env python3.13
import time
import os
import hashlib
import yaml
from datetime import datetime
from actions.send_to_cursor import send_prompt
from state import get_mode
from generate_initial_prompt import DEFAULT_CONTINUATION_PROMPT
import logging
from utils.colored_logging import setup_colored_logging
import fnmatch
import platform
import openai
import requests
from typing import Dict, List, Optional, Tuple

# Configure logging
setup_colored_logging(debug=os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('watcher')

# Add debug info about logging level
logger.debug("Debug logging enabled") if os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true" else logger.info("Info logging enabled")

# --- Configurable README tracking ---
def load_gitignore_patterns(gitignore_path):
    patterns = set()
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Remove trailing slashes for directory patterns
                if line.endswith('/'):
                    patterns.add(line.rstrip('/'))
                else:
                    patterns.add(line)
    return patterns

GITIGNORE_PATH = os.path.join(os.path.dirname(__file__), ".gitignore")
GITIGNORE_PATTERNS = load_gitignore_patterns(GITIGNORE_PATH)

# Set up EXCLUDE_DIRS for os.walk (directories only)
EXCLUDE_DIRS = {p for p in GITIGNORE_PATTERNS if not any(char in p for char in '*?[]!') and not '.' in os.path.basename(p)}
# Also add hardcoded ones for safety
EXCLUDE_DIRS.update({"node_modules", ".git", "dist", "__pycache__"})

# Set up EXCLUDE_FILES for file-level ignores
EXCLUDE_FILES = {p for p in GITIGNORE_PATTERNS if '.' in os.path.basename(p) or '*' in p or '?' in p or '[' in p or '!' in p}

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

# Get current OS type
CURRENT_OS = platform.system().lower()
if CURRENT_OS == "darwin":
    CURRENT_OS = "osx"

# Get platform configuration
PLATFORM = config.get("platform", "cursor")
platform_config = config["platforms"].get(PLATFORM, {})
if not platform_config:
    logger.error(f"Platform {PLATFORM} not found in config")
    exit(1)

# Get paths from platform config
WATCH_PATH = os.path.expanduser(platform_config.get("project_path", ""))
if not WATCH_PATH:
    logger.error(f"Project path not configured for platform {PLATFORM}")
    exit(1)

TASK_FILE_PATH = platform_config.get("task_file_path", "tasks.md")
LAST_README_MTIME = None
TASK_COMPLETED = False
INACTIVITY_DELAY = config.get("inactivity_delay", 120)  # Default to 120 seconds if not specified

# Defensive: Ensure INACTIVITY_DELAY is not None and is a number
try:
    inactivity_delay_val = float(INACTIVITY_DELAY)
except (TypeError, ValueError):
    logger.warning(f"INACTIVITY_DELAY invalid or None, defaulting to 120.")
    inactivity_delay_val = 120.0
logger.debug(f"DEBUG: INACTIVITY_DELAY raw value: {INACTIVITY_DELAY}, parsed: {inactivity_delay_val} (type: {type(INACTIVITY_DELAY)})")

# Defensive: Ensure all timing variables are initialized to 0 if None
last_activity = 0.0
last_prompt_time = 0.0
inactivity_timer = 0.0

# Initialize OpenAI client if configured
openai_client = None
if config.get("openai", {}).get("vision", {}).get("enabled", False):
    openai.api_key = config["openai"]["vision"]["api_key"]
    openai_client = openai

# Initialize Slack client if configured
slack_client = None
if config.get("slack", {}).get("enabled", False):
    slack_client = {
        "bot_token": config["slack"]["bot_token"],
        "app_token": config["slack"]["app_token"],
        "channels": config["slack"]["channels"]
    }

# Add debug info about paths
logger.info(f"Watcher Configuration:")
logger.info(f"Platform: {PLATFORM}")
logger.info(f"Project Path: {WATCH_PATH}")
logger.info(f"Task README: {TASK_FILE_PATH}")
logger.info(f"Inactivity Delay: {inactivity_delay_val} seconds")
logger.info(f"Excluded Dirs: {EXCLUDE_DIRS}")
logger.info(f"Gitignore Patterns: {GITIGNORE_PATTERNS}")
logger.info(f"Current OS: {CURRENT_OS}")
logger.info(f"OpenAI Vision: {'Enabled' if openai_client else 'Disabled'}")
logger.info(f"Slack Integration: {'Enabled' if slack_client else 'Disabled'}")

# Verify project path exists
if not os.path.exists(WATCH_PATH):
    logger.error(f"Project path {WATCH_PATH} does not exist")
    exit(1)

LAST_HASH = None
FILE_MTIMES = {}

def get_platform_config(platform_name: str) -> Dict:
    """Get platform-specific configuration with OS-specific keystrokes."""
    platform_config = config["platforms"].get(platform_name, {})
    if not platform_config:
        return {}
    
    # Map OS-specific keystrokes
    os_type = platform_config.get("os_type", "osx")
    if os_type != CURRENT_OS:
        logger.warning(f"Platform {platform_name} configured for {os_type} but running on {CURRENT_OS}")
    
    # Convert keystrokes based on OS
    keystrokes = platform_config.get("keystrokes", [])
    for keystroke in keystrokes:
        keys = keystroke["keys"]
        if CURRENT_OS == "windows":
            keys = keys.replace("command", "ctrl")
        elif CURRENT_OS == "linux":
            keys = keys.replace("command", "ctrl")
        keystroke["keys"] = keys
    
    return platform_config

def check_vision_conditions(file_path: str, action: str) -> Optional[Tuple[str, List[Dict]]]:
    """Check if a file matches any vision conditions and return the appropriate keystrokes."""
    if not openai_client:
        return None
    
    platform_config = get_platform_config(PLATFORM)
    vision_conditions = platform_config.get("options", {}).get("vision_conditions", [])
    
    for condition in vision_conditions:
        if fnmatch.fnmatch(file_path, condition["file_type"]) and condition["action"] == action:
            try:
                # Take screenshot and analyze with OpenAI Vision
                response = openai_client.chat.completions.create(
                    model=config["openai"]["vision"]["model"],
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": condition["question"]},
                                {"type": "image_url", "image_url": {"url": f"file://{file_path}"}}
                            ]
                        }
                    ],
                    max_tokens=config["openai"]["vision"]["max_tokens"],
                    temperature=config["openai"]["vision"]["temperature"]
                )
                
                # Determine success based on response
                success = "yes" in response.choices[0].message.content.lower()
                return condition["question"], condition["success_keystrokes" if success else "failure_keystrokes"]
            except Exception as e:
                logger.error(f"Error in vision analysis: {e}")
                return None
    
    return None

def send_slack_message(message: str, channel: str = "automation"):
    """Send a message to Slack if configured."""
    if not slack_client:
        return
    
    try:
        channel_id = next((c["id"] for c in slack_client["channels"] if c["name"] == channel), None)
        if not channel_id:
            logger.error(f"Slack channel {channel} not found")
            return
        
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {slack_client['bot_token']}"},
            json={
                "channel": channel_id,
                "text": message
            }
        )
        
        if not response.ok:
            logger.error(f"Failed to send Slack message: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Slack message: {e}")

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
    watched_files = []
    
    # Walk through directory
    for root, dirs, files in os.walk(WATCH_PATH):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not any(fnmatch.fnmatch(d, pat) for pat in GITIGNORE_PATTERNS)]
        
        # Process each file
        for filename in sorted(files):  # Sort for consistent ordering
            # Skip files matching .gitignore patterns
            skip_file = False
            rel_file_path = os.path.relpath(os.path.join(root, filename), WATCH_PATH)
            for pat in GITIGNORE_PATTERNS:
                if fnmatch.fnmatch(filename, pat) or fnmatch.fnmatch(rel_file_path, pat):
                    skip_file = True
                    break
            if skip_file or filename.endswith(".tmp"): 
                continue
                
            abs_path = os.path.join(root, filename)
            rel_path = os.path.relpath(abs_path, WATCH_PATH)
            watched_files.append(rel_path)
            
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
                    
                    # Check vision conditions for changed files
                    if current_mtime > last_mtime and last_mtime is not None:
                        vision_result = check_vision_conditions(abs_path, "save")
                        if vision_result:
                            question, keystrokes = vision_result
                            logger.info(f"Vision analysis triggered for {rel_path}")
                            logger.info(f"Question: {question}")
                            for keystroke in keystrokes:
                                send_prompt(keystroke["keys"], platform=PLATFORM, delay_ms=keystroke["delay_ms"])
                
                total_files += 1
                
            except OSError as e:
                logger.warning(f"Could not access {rel_path}: {e}")
                continue
    
    # Log watched files only during initialization
    if LAST_HASH is None:
        logger.info(f"Watching {total_files} files:")
        for file in sorted(watched_files):
            logger.info(f"  {file}")
    
    # Log changed files only when there are actual changes
    if changed_files and LAST_HASH is not None:
        logger.info(f"Changed files:")
        for file in changed_files:
            logger.info(f"  {file}")
    
    return sha.hexdigest(), changed_files, total_files

def run_watcher():
    """
    Main watcher loop that monitors for changes and sends prompts.
    """
    global LAST_HASH, FILE_MTIMES, LAST_README_MTIME
    
    # Check if initial prompt has been sent
    initial_prompt_sent = os.path.exists(os.path.join(os.path.dirname(__file__), ".initial_prompt_sent"))
    logger.info(f"Initial prompt {'has' if initial_prompt_sent else 'has not'} been sent yet")
    
    # Get absolute path to task file
    task_file_abs_path = os.path.join(WATCH_PATH, TASK_FILE_PATH)
    if not os.path.exists(task_file_abs_path):
        logger.error(f"Task file not found at {task_file_abs_path}")
        return
    
    while True:
        try:
            global last_activity, last_prompt_time, inactivity_timer, inactivity_delay_val
            # Defensive: Ensure all timing variables are initialized and valid before use
            if last_activity is None or not isinstance(last_activity, (int, float)):
                logger.error(f"last_activity is invalid in loop: {last_activity} (type: {type(last_activity)}) - setting to time.time()")
                last_activity = time.time()
            if last_prompt_time is None or not isinstance(last_prompt_time, (int, float)):
                logger.error(f"last_prompt_time is invalid in loop: {last_prompt_time} (type: {type(last_prompt_time)}) - setting to 0.0")
                last_prompt_time = 0.0
            if inactivity_timer is None or not isinstance(inactivity_timer, (int, float)):
                logger.error(f"inactivity_timer is invalid in loop: {inactivity_timer} (type: {type(inactivity_timer)}) - setting to 0.0")
                inactivity_timer = 0.0
            if 'inactivity_delay_val' not in globals() or inactivity_delay_val is None or not isinstance(inactivity_delay_val, (int, float)):
                logger.error(f"inactivity_delay_val is invalid or not set in loop: {globals().get('inactivity_delay_val', None)} (type: {type(globals().get('inactivity_delay_val', None))}) - setting to 120.0")
                inactivity_delay_val = 120.0

            # FINAL DEFENSIVE CHECK: If any timing variable is still None, skip this loop iteration
            if any(x is None for x in [last_activity, last_prompt_time, inactivity_timer, inactivity_delay_val]):
                logger.critical(f"Timing variable(s) still None after defensive checks. Skipping iteration. last_activity={last_activity}, last_prompt_time={last_prompt_time}, inactivity_timer={inactivity_timer}, inactivity_delay_val={inactivity_delay_val}")
                time.sleep(1)
                continue
            # ADDITIONAL DEFENSIVE CHECK: If any timing variable is not a number, log and skip
            if not all(isinstance(x, (int, float)) for x in [last_activity, last_prompt_time, inactivity_timer, inactivity_delay_val]):
                logger.critical(f"Timing variable(s) not numeric after defensive checks. Skipping iteration. last_activity={last_activity} (type: {type(last_activity)}), last_prompt_time={last_prompt_time} (type: {type(last_prompt_time)}), inactivity_timer={inactivity_timer} (type: {type(inactivity_timer)}), inactivity_delay_val={inactivity_delay_val} (type: {type(inactivity_delay_val)})")
                time.sleep(1)
                continue
            # Get current state
            current_hash, changed_files, total_files = hash_folder_state()
            # Check if task file was modified
            task_file_modified = False
            if TASK_FILE_PATH in changed_files:
                current_mtime = os.path.getmtime(task_file_abs_path)
                if LAST_README_MTIME is None or current_mtime > LAST_README_MTIME:
                    task_file_modified = True
                    LAST_README_MTIME = current_mtime
                    logger.info(f"Task file {TASK_FILE_PATH} was modified!")
                    logger.info(f"  Last modified: {datetime.fromtimestamp(current_mtime)}")
                    if slack_client:
                        send_slack_message(f"Task file modified: {TASK_FILE_PATH}")
            # Update inactivity timer
            if current_hash != LAST_HASH or task_file_modified:
                inactivity_timer = 0
                last_activity = time.time()
                LAST_HASH = current_hash
                logger.info(f"Activity detected! Resetting inactivity timer (was at {int(inactivity_timer)} seconds)")
                if changed_files:
                    logger.info(f"  Changed files: {', '.join(changed_files)}")
            else:
                inactivity_timer = time.time() - last_activity
                if inactivity_timer >= 30:  # Log status when getting close to timeout
                    logger.info(f"No changes detected for {int(inactivity_timer)} seconds")
                    logger.info(f"  Will send prompt in {max(0, inactivity_delay_val-int(inactivity_timer))} seconds if no changes occur")
            if inactivity_timer >= inactivity_delay_val and get_mode() == "auto":
                current_time = time.time()
                logger.debug(f"DEBUG: current_time={current_time}, current_time-last_prompt_time={current_time - last_prompt_time}")
                # Defensive: Ensure current_time and last_prompt_time are not None
                if current_time is None or last_prompt_time is None:
                    logger.error(f"current_time or last_prompt_time is None: current_time={current_time}, last_prompt_time={last_prompt_time}")
                # Only send a new prompt if it's been at least INACTIVITY_DELAY seconds since the last one
                elif current_time - last_prompt_time >= inactivity_delay_val:
                    logger.info(f"Inactivity timeout reached ({int(inactivity_timer)} seconds). Sending prompt to {PLATFORM}.")
                    
                    # Use the appropriate prompt based on whether initial prompt was sent
                    if not initial_prompt_sent:
                        try:
                            with open("initial_prompt.txt", "r") as f:
                                prompt = f.read().strip()
                        except Exception as e:
                            logger.error(f"Failed to read initial_prompt.txt: {e}")
                            prompt = "continue"
                        logger.info("Starting new chat with initial prompt")
                        send_prompt(prompt, platform=PLATFORM, new_chat=True, 
                                  initial_delay=config.get("initial_delay", 10),
                                  send_message=config.get("send_message", True))
                        initial_prompt_sent = True
                    else:
                        # Use the continuation prompt
                        prompt = DEFAULT_CONTINUATION_PROMPT.format(
                            task_file_path=task_file_abs_path,
                            additional_context_path=config.get("additional_context_path", "context.md")
                        )
                        logger.info("Sending continuation prompt")
                        send_prompt(prompt, platform=PLATFORM, new_chat=False,
                                  send_message=config.get("send_message", True))
                    
                    last_prompt_time = current_time
                    inactivity_timer = 0
                    logger.info("Watching for changes...")
                else:
                    logger.info(f"Skipping prompt - last prompt was sent {int(current_time - last_prompt_time)} seconds ago")
            time.sleep(5)  # Check every 5 seconds
        except Exception as e:
            logger.error(f"Error in watcher: {e}")
            if slack_client:
                send_slack_message(f"Error in watcher: {str(e)}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    run_watcher()
