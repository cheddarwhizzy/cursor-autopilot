#!/usr/bin/env python3.13
import time
import os
import hashlib
import yaml
from datetime import datetime
import logging
from src.utils.colored_logging import setup_colored_logging
import fnmatch
import platform
import openai
import requests
from typing import Dict, List, Optional, Tuple
import base64
import json
import subprocess
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import prompt generation logic
from src.generate_initial_prompt import (
    read_prompt_from_file,
    DEFAULT_INITIAL_PROMPT,
    DEFAULT_CONTINUATION_PROMPT
)

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='Cursor Autopilot Watcher')
    parser.add_argument('--auto', action='store_true', help='Enable auto mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--no-send', action='store_true', help='Disable sending messages')
    parser.add_argument('--project-path', type=str, help='Override project path from config')
    parser.add_argument('--inactivity-delay', type=int, help='Override inactivity delay in seconds')
    parser.add_argument('--platform', type=str, help='Override platform to use')
    
    return parser.parse_args()

# Get command line arguments
args = parse_args()

# Configure logging first before any other imports that might use it
setup_colored_logging(debug=args.debug or True)  # Always enable debug logging
logger = logging.getLogger('watcher')
logger.setLevel(logging.DEBUG)  # Set logger level to DEBUG
logger.debug("Debug logging enabled")

# Log command line arguments
if args.project_path:
    logger.info(f"Command line project path override: {args.project_path}")
if args.auto:
    logger.info("Auto mode enabled")
if args.no_send:
    logger.info("Message sending disabled")
if args.inactivity_delay:
    logger.info(f"Inactivity delay override: {args.inactivity_delay} seconds")
if args.platform:
    logger.info(f"Platform override: {args.platform}")

# Import OpenAI after logger is defined
try:
    from openai import OpenAI
    logger.debug("OpenAI module imported successfully")
except ImportError:
    logger.warning("OpenAI module not available")
    OpenAI = None

# Import other modules that might depend on logger
from src.actions.send_to_cursor import send_prompt
from src.state import get_mode

# Platform-specific imports with proper error handling
try:
    import pyautogui
except ImportError:
    logger.warning("pyautogui not available")
    pyautogui = None

try:
    import win32gui
    import win32con
except ImportError:
    logger.warning("win32gui not available")
    win32gui = None
    win32con = None

# Global variables
config = {}
PLATFORM = []
WATCH_PATH = ""
INACTIVITY_DELAY = 0

# Try to find config file in parent directory first, then current directory
root_config = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
src_config = os.path.join(os.path.dirname(__file__), "config.yaml")

if os.path.exists(root_config):
    CONFIG_PATH = root_config
    logger.debug(f"Using root config file: {os.path.abspath(CONFIG_PATH)}")
elif os.path.exists(src_config):
    CONFIG_PATH = src_config
    logger.debug(f"Using src config file: {os.path.abspath(CONFIG_PATH)}")
else:
    CONFIG_PATH = root_config  # Default to root even if it doesn't exist
    logger.debug(f"No config file found, defaulting to: {os.path.abspath(CONFIG_PATH)}")

CONFIG_MTIME = os.path.getmtime(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else 0
LAST_HASH = None
FILE_MTIMES = {}
openai_client = None

# Path for the initial prompt flag file
INITIAL_PROMPT_SENT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".initial_prompt_sent"))
logger.debug(f"Initial prompt sent file path: {INITIAL_PROMPT_SENT_FILE}")

# Exclude patterns
EXCLUDE_DIRS = {"node_modules", ".git", "dist", "__pycache__", ".idea", "venv", ".env"}
EXCLUDE_FILES = {'*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.exe', '*.tmp', '*.log', '*.swp', '*.swo'}
GITIGNORE_PATTERNS = set()

# Load gitignore patterns
def load_gitignore_patterns(project_path):
    """
    Find and load all .gitignore files in the project path and its parent directories
    Returns a set of gitignore patterns
    """
    logger.debug(f"Loading .gitignore patterns from {project_path}")
    patterns = set()
    
    # First check if there's a .gitignore in the project root
    root_gitignore = os.path.join(project_path, ".gitignore")
    if os.path.exists(root_gitignore):
        logger.debug(f"Found root .gitignore at {root_gitignore}")
        with open(root_gitignore, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Remove trailing slashes for directory patterns
                if line.endswith('/'):
                    patterns.add(line.rstrip('/'))
                else:
                    patterns.add(line)
        logger.debug(f"Loaded {len(patterns)} patterns from root .gitignore")
    
    # Then find all .gitignore files in subdirectories
    for root, dirs, files in os.walk(project_path):
        if ".gitignore" in files:
            gitignore_path = os.path.join(root, ".gitignore")
            logger.debug(f"Found .gitignore at {gitignore_path}")
            try:
                with open(gitignore_path, "r") as f:
                    subdir_patterns = set()
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        # Remove trailing slashes for directory patterns
                        if line.endswith('/'):
                            subdir_patterns.add(line.rstrip('/'))
                        else:
                            subdir_patterns.add(line)
                    
                    # Get relative path from project root to this .gitignore file's directory
                    rel_path = os.path.relpath(root, project_path)
                    if rel_path == ".":
                        # This is already the root .gitignore which we handled above
                        continue
                    
                    # Add patterns with path prefix for non-root .gitignore files
                    for pattern in subdir_patterns:
                        if pattern.startswith('/'):
                            # Absolute path within repo - add directory prefix
                            patterns.add(os.path.join(rel_path, pattern.lstrip('/')))
                        elif not pattern.startswith('*') and '/' not in pattern:
                            # Simple filename/dirname - add directory prefix
                            patterns.add(os.path.join(rel_path, pattern))
                        else:
                            # Pattern with wildcards - add both with and without prefix
                            patterns.add(pattern)
                            patterns.add(os.path.join(rel_path, pattern))
                    
                    logger.debug(f"Loaded {len(subdir_patterns)} patterns from {gitignore_path}")
            except Exception as e:
                logger.error(f"Error loading {gitignore_path}: {e}")
    
    logger.info(f"Loaded a total of {len(patterns)} gitignore patterns")
    return patterns

# Initialize global variables with default values
GITIGNORE_PATH = ""
GITIGNORE_PATTERNS = set()

# Set up EXCLUDE_DIRS for os.walk (directories only)
EXCLUDE_DIRS.update({"node_modules", ".git", "dist", "__pycache__"})

# Set up EXCLUDE_FILES for file-level ignores
EXCLUDE_FILES.update({p for p in GITIGNORE_PATTERNS if '.' in os.path.basename(p) or '*' in p or '?' in p or '[' in p or '!' in p})

# Get current OS type
OS_TYPE = "darwin" if os.uname().sysname == "Darwin" else "windows" if os.uname().sysname == "Windows" else "linux"
logger.debug(f"Detected OS type: {OS_TYPE}")

# Initialize global variables with default values
PLATFORM = "cursor"
TASK_FILE_PATH = "tasks.md"
LAST_README_MTIME = None
TASK_COMPLETED = False
inactivity_delay_val = 120.0
last_activity = 0.0
last_prompt_time = 0.0
inactivity_timer = 0.0
slack_client = None

def load_config():
    """
    Load configuration from YAML file and initialize global variables
    Returns True if successful, False otherwise
    """
    try:
        global config, PLATFORM, WATCH_PATH, INACTIVITY_DELAY, openai_client, GITIGNORE_PATTERNS
        
        logger.debug("Starting configuration load...")
        
        # Load config file
        if not os.path.exists(CONFIG_PATH):
            logger.error(f"Config file not found: {CONFIG_PATH}")
            return False
            
        logger.debug(f"Loading config from {CONFIG_PATH}")
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        # Log raw config for debugging
        logger.debug(f"Raw config: {config}")
        
        # Validate required fields
        if not config.get("platforms"):
            logger.error("No platforms configured")
            return False
            
        # Override platform if specified in command line
        if args.platform:
            if args.platform in config["platforms"]:
                PLATFORM = [args.platform]
                logger.info(f"Using platform override from command line: {args.platform}")
            else:
                logger.error(f"Platform {args.platform} not found in config")
                return False
        else:
            # Initialize platforms - check general.active_platforms first
            if config.get("general", {}).get("active_platforms"):
                active_platforms = config["general"]["active_platforms"]
                logger.debug(f"Using active_platforms from general section: {active_platforms}")
                # Filter the list to only include platforms that exist in the config
                PLATFORM = [p for p in active_platforms if p in config["platforms"]]
            else:
                # Fallback to using all platforms
                PLATFORM = list(config["platforms"].keys())
            
        logger.debug(f"Final active platforms: {PLATFORM}")
        
        if not PLATFORM:
            logger.error("No platforms enabled")
            return False
            
        # Initialize OpenAI client if configured
        if config.get("openai", {}).get("api_key"):
            logger.debug("Initializing OpenAI client")
            openai_client = OpenAI(api_key=config["openai"]["api_key"])
        else:
            logger.warning("OpenAI API key not configured")
            openai_client = None
            
        # Set inactivity delay - override from command line if provided
        if args.inactivity_delay:
            INACTIVITY_DELAY = args.inactivity_delay
            logger.info(f"Using inactivity delay override from command line: {INACTIVITY_DELAY}")
        else:
            INACTIVITY_DELAY = config.get("inactivity_delay", 120)
            
        logger.debug(f"Set inactivity delay to {INACTIVITY_DELAY}")
        
        # Validate platform configurations
        platform_paths = {}
        for platform in PLATFORM:
            logger.debug(f"Validating platform {platform}")
            platform_config = config["platforms"].get(platform, {})
            if not platform_config:
                logger.error(f"No configuration found for platform {platform}")
                return False
                
            # Get project path - override from command line if provided
            if args.project_path and platform == PLATFORM[0]:  # Apply override to first/active platform
                project_path = args.project_path
                logger.info(f"Using project path override from command line for {platform}: {project_path}")
                
                # Update the config with the override
                config["platforms"][platform]["project_path"] = project_path
            else:
                project_path = platform_config.get("project_path", "")
            
            logger.debug(f"Platform {platform} project path: {project_path}")
            
            if not project_path:
                logger.error(f"Project path not configured for platform {platform}")
                return False
                
            # Expand user directory
            project_path = os.path.expanduser(project_path)
            logger.debug(f"Expanded project path for {platform}: {project_path}")
            
            if not os.path.exists(project_path):
                logger.error(f"Project path does not exist for platform {platform}: {project_path}")
                return False
                
            platform_paths[platform] = project_path
            
        # Set watch path to first platform's project path
        WATCH_PATH = next(iter(platform_paths.values()))
        logger.debug(f"Set WATCH_PATH to {WATCH_PATH}")
        
        # Load gitignore patterns from the watch path
        GITIGNORE_PATTERNS = load_gitignore_patterns(WATCH_PATH)
        
        # Log configuration
        logger.info("Configuration loaded successfully:")
        logger.info(f"Platforms: {', '.join(PLATFORM)}")
        logger.info(f"Platform paths: {platform_paths}")
        logger.info(f"Active project path: {WATCH_PATH}")
        logger.info(f"Task file path: {config.get('task_file_path', 'tasks.md')}")
        logger.info(f"Inactivity delay: {INACTIVITY_DELAY} seconds")
        logger.info(f"Loaded {len(GITIGNORE_PATTERNS)} gitignore patterns")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        logger.exception("Full traceback:")
        return False

def get_platform_config(platform_name: str) -> Dict:
    """Get platform-specific configuration with OS-specific keystrokes."""
    platform_config = config["platforms"].get(platform_name, {})
    if not platform_config:
        return {}
    
    # Map OS-specific keystrokes
    os_type = platform_config.get("os_type", "osx")
    if os_type != OS_TYPE:
        logger.warning(f"Platform {platform_name} configured for {os_type} but running on {OS_TYPE}")
    
    # Convert keystrokes based on OS
    keystrokes = platform_config.get("keystrokes", [])
    for keystroke in keystrokes:
        keys = keystroke["keys"]
        if OS_TYPE == "windows":
            keys = keys.replace("command", "ctrl")
        elif OS_TYPE == "linux":
            keys = keys.replace("command", "ctrl")
        keystroke["keys"] = keys
    
    return platform_config

def check_vision_conditions(file_path, event_type, platform):
    """
    Check if vision analysis should be triggered for a file change
    Returns tuple of (question, keystrokes) if conditions are met, None otherwise
    """
    try:
        # Skip if OpenAI is not configured
        if not openai_client:
            logger.debug("Skipping vision analysis - OpenAI client not initialized")
            return None
            
        # Get platform-specific configuration
        platform_config = config["platforms"].get(platform, {})
        if not platform_config:
            logger.warning(f"No configuration found for platform {platform}")
            return None
        
        # Check if vision analysis is enabled for this platform
        options = platform_config.get("options", {})
        if not options or not options.get("enable_vision", False):
            logger.debug(f"Vision analysis not enabled for platform {platform}")
            return None
            
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            return None
            
        # Get file extension
        _, ext = os.path.splitext(file_path)
        if not ext:
            logger.debug(f"File has no extension: {file_path}")
            return None
        
        # Check if file type is supported for vision analysis
        supported_extensions = options.get("vision_extensions", [])
        if ext.lower() not in supported_extensions:
            logger.debug(f"File extension {ext} not in supported vision extensions: {supported_extensions}")
            return None
        
        # Check if file is too large for vision analysis
        max_size = options.get("max_vision_file_size", 10 * 1024 * 1024)  # Default 10MB
        if os.path.getsize(file_path) > max_size:
            logger.warning(f"File {file_path} too large for vision analysis")
            return None
        
        # Get vision prompt template
        prompt_template = options.get("vision_prompt", "")
        if not prompt_template:
            logger.warning(f"No vision prompt template configured for platform {platform}")
            return None
        
        # Format prompt with file information
        prompt = prompt_template.format(
            file_path=file_path,
            event_type=event_type,
            platform=platform
        )
        logger.debug(f"Using vision prompt: {prompt}")
        
        # Get vision analysis result
        vision_result = analyze_vision(file_path, prompt)
        if not vision_result:
            logger.debug("Vision analysis returned no result")
            return None
        
        logger.debug(f"Vision result: {vision_result}")
        
        # Parse vision result into question and keystrokes
        question = vision_result.get("question", "")
        keystrokes = vision_result.get("keystrokes", [])
        
        if not question or not keystrokes:
            logger.debug("Missing question or keystrokes in vision result")
            return None
        
        return question, keystrokes
        
    except Exception as e:
        logger.error(f"Error checking vision conditions: {e}")
        logger.exception("Full traceback:")
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

def should_ignore_file(file_path, rel_path, platform_path):
    """
    Check if a file should be ignored based on exclude patterns and gitignore rules
    
    Args:
        file_path: Absolute path to the file
        rel_path: Path relative to the platform directory
        platform_path: Absolute path to the platform directory
        
    Returns:
        bool: True if the file should be ignored
    """
    # Skip files in excluded directories
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in file_path.split(os.sep):
            return True
    
    # Skip excluded file types
    for pattern in EXCLUDE_FILES:
        if fnmatch.fnmatch(os.path.basename(file_path), pattern):
            return True
    
    # Skip gitignore patterns
    for pattern in GITIGNORE_PATTERNS:
        # Handle patterns with directory components
        if os.sep in pattern:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # Also try with / separator for cross-platform compatibility
            if fnmatch.fnmatch(rel_path, pattern.replace(os.sep, '/')):
                return True
        # Handle filename-only patterns
        elif fnmatch.fnmatch(os.path.basename(file_path), pattern):
            return True
    
    return False

def hash_folder_state():
    """
    Scan directory for changes and return:
    - A hash representing the current state
    - List of files that changed since last scan
    - Total number of files being watched
    """
    global LAST_HASH
    sha = hashlib.sha256()
    changed_files = []
    total_files = 0
    watched_files = []
    
    # Get platform-specific paths
    platform_paths = {}
    for platform in PLATFORM:
        platform_config = config["platforms"].get(platform, {})
        if platform_config:
            watch_path = os.path.expanduser(platform_config.get("project_path", ""))
            if watch_path:
                platform_paths[platform] = watch_path
            else:
                logger.error(f"No project path found for {platform}")
        else:
            logger.error(f"No configuration found for {platform}")
    
    if not platform_paths:
        logger.error("No valid platform paths found")
        return None, [], 0
    
    # Walk through each platform's directory
    for platform, watch_path in platform_paths.items():
        for root, dirs, files in os.walk(watch_path):
            # Filter out excluded directories in-place to prevent walking them
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not any(fnmatch.fnmatch(d, pat) for pat in GITIGNORE_PATTERNS)]
            
            # Process files
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, watch_path)
                
                # Skip ignored files
                if should_ignore_file(file_path, rel_path, watch_path):
                    continue
                
                # Get file stats
                try:
                    stat = os.stat(file_path)
                    mtime = stat.st_mtime
                    size = stat.st_size
                    
                    # Update hash
                    sha.update(f"{rel_path}:{mtime}:{size}".encode())
                    
                    # Check if file changed
                    if rel_path in FILE_MTIMES:
                        if FILE_MTIMES[rel_path] != mtime:
                            changed_files.append((platform, rel_path))
                    else:
                        # Only log new files on first run
                        if LAST_HASH is None:
                            logger.debug(f"New file: {rel_path}")
                        changed_files.append((platform, rel_path))
                    
                    # Update mtime cache
                    FILE_MTIMES[rel_path] = mtime
                    watched_files.append((platform, rel_path))
                    total_files += 1
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    logger.exception("Full traceback:")
    
    # Calculate final hash
    current_hash = sha.hexdigest()
    
    # Update global hash
    if LAST_HASH is None:
        LAST_HASH = current_hash
        logger.debug("First run, setting initial hash")
        return current_hash, [], total_files
    
    # Return results
    return current_hash, changed_files, total_files

def run_watcher():
    """
    Main watcher loop that monitors file changes and triggers actions
    """
    logger.debug("Starting run_watcher...")
    
    # Initialize global variables
    global CONFIG_MTIME, LAST_HASH, FILE_MTIMES
    
    # Load configuration
    if not load_config():
        logger.error("Failed to load configuration")
        return
    
    logger.info("Starting file watcher...")
    
    # Initialize time tracking variables
    last_activity_time = time.time() # Use this to track last file change or prompt sent
    
    # Initialize file tracking variables
    if LAST_HASH is None:
        logger.debug("Initializing file state hash...")
        current_hash, _, total_files = hash_folder_state()
        LAST_HASH = current_hash
        logger.debug(f"Initialized LAST_HASH to {LAST_HASH} with {total_files} files")
    
    # Initialize configuration tracking
    if os.path.exists(CONFIG_PATH):
        CONFIG_MTIME = os.path.getmtime(CONFIG_PATH)
        logger.debug(f"Initialized CONFIG_MTIME to {CONFIG_MTIME}")
        
    # Check if initial prompt has already been sent
    initial_prompt_sent = os.path.exists(INITIAL_PROMPT_SENT_FILE)
    logger.debug(f"Initial prompt sent file exists: {initial_prompt_sent}")

    # Send initialization keystrokes/initial prompt if needed
    if not initial_prompt_sent:
        logger.info("Initial prompt file not found. Sending initial prompts/keystrokes...")
        for platform in PLATFORM:
            platform_config = config["platforms"].get(platform, {})
            initialization = platform_config.get("initialization", [])
            options = platform_config.get("options", {})
            
            # Get paths for prompt generation
            initial_prompt_file = platform_config.get("initial_prompt_file_path", None)
            task_file = platform_config.get("task_file_path", "tasks.md")
            context_file = platform_config.get("additional_context_path", "context.md")
            
            # Resolve absolute paths relative to project path if needed
            project_path = os.path.expanduser(platform_config.get("project_path", "."))
            initial_prompt_file = os.path.join(project_path, initial_prompt_file) if initial_prompt_file else None
            task_file = os.path.join(project_path, task_file)
            context_file = os.path.join(project_path, context_file)
            
            # Try reading custom prompt, otherwise use default
            initial_prompt_template = read_prompt_from_file(initial_prompt_file) or DEFAULT_INITIAL_PROMPT
            logger.debug(f"Using initial prompt template (from file: {bool(initial_prompt_file)})")
            
            # Format the prompt
            try:
                initial_prompt_content = initial_prompt_template.format(task_file_path=task_file, additional_context_path=context_file)
            except KeyError as e:
                logger.error(f"Error formatting initial prompt template (missing key {e}). Using raw template.")
                initial_prompt_content = initial_prompt_template # Send raw template if formatting fails
                
            logger.debug(f"Platform {platform} initialization config: {initialization}")
            logger.debug(f"Platform {platform} final initial_prompt content length: {len(initial_prompt_content)}")
            
            # Activate window first
            window_title = platform_config.get("window_title", platform)
            logger.info(f"Activating window for {platform}: {window_title}")
            activate_window(window_title)
            time.sleep(1) # Give time for window activation
            
            # Send initialization keystrokes
            if initialization and not args.no_send:
                logger.info(f"Sending initialization keystrokes to {platform}")
                for keystroke in initialization:
                    keys = keystroke.get("keys", "")
                    delay_ms = keystroke.get("delay_ms", 0)
                    if keys:
                        logger.info(f"Sending initialization keystroke to {platform}: {keys}")
                        if delay_ms > 0:
                            time.sleep(delay_ms / 1000)
                        send_keystroke(keys, platform)
            elif initialization and args.no_send:
                logger.info(f"Skipping initialization keystrokes to {platform} (--no-send enabled)")
            
            # Send initial prompt content
            if initial_prompt_content:
                 if not args.no_send:
                     logger.info(f"Sending initial prompt content to {platform}...")
                     # Activate window again just in case
                     activate_window(window_title)
                     time.sleep(0.5)
                     send_keystroke_string(initial_prompt_content, platform)
                     last_activity_time = time.time() # Reset timer after sending prompt
                 else:
                     logger.info(f"Skipping initial prompt content to {platform} (--no-send enabled)")
                     last_activity_time = time.time() # Reset timer anyway

        # Create the flag file after sending to all platforms
        try:
            with open(INITIAL_PROMPT_SENT_FILE, 'w') as f:
                f.write("Initial prompt sent at: " + datetime.now().isoformat())
            logger.info(f"Created initial prompt sent file: {INITIAL_PROMPT_SENT_FILE}")
            initial_prompt_sent = True # Update state
        except Exception as e:
            logger.error(f"Failed to create initial prompt sent file: {e}")
    else:
        logger.info("Initial prompt file found. Skipping initial prompts/keystrokes.")

    # Reset timer after initialization phase
    last_activity_time = time.time()
    
    try:
        logger.info("Entering main watcher loop...")
        last_hash_check = ""
        
        while True:
            # Check for configuration changes
            if os.path.exists(CONFIG_PATH):
                current_mtime = os.path.getmtime(CONFIG_PATH)
                if current_mtime > CONFIG_MTIME:
                    logger.info("Configuration file changed, reloading...")
                    if not load_config():
                        logger.error("Failed to reload configuration, continuing with previous settings")
                    else:
                        CONFIG_MTIME = current_mtime
            
            # Get current state (with less logging)
            current_hash, changed_files, total_files = hash_folder_state()
            
            # Only log if hash changed
            if current_hash != last_hash_check:
                logger.debug(f"Current hash: {current_hash}, Total files: {total_files}")
                last_hash_check = current_hash
            
            # Check for changes
            if current_hash != LAST_HASH:
                logger.info(f"Detected changes in {len(changed_files)} files")
                last_activity_time = time.time() # Reset timer on file change
                
                # Process changed files
                for platform, rel_path in changed_files:
                    abs_path = os.path.join(config["platforms"][platform]["project_path"], rel_path)
                    logger.info(f"File changed: {rel_path} for platform {platform}")
                    
                    # Check vision conditions for changed files
                    vision_result = check_vision_conditions(abs_path, "save", platform)
                    if vision_result:
                        question, keystrokes = vision_result
                        logger.info(f"Vision analysis triggered for {rel_path} in {platform}")
                        logger.info(f"Question: {question}")
                        for keystroke in keystrokes:
                            send_prompt(keystroke["keys"], platform=platform, delay_ms=keystroke["delay_ms"])
                
                # Update last hash
                LAST_HASH = current_hash
            
            # Check for inactivity and send continuation prompt
            current_time = time.time()
            elapsed_time = current_time - last_activity_time
            time_remaining = INACTIVITY_DELAY - elapsed_time

            # Log countdown periodically (e.g., every 10 seconds or when close to 0)
            if int(time_remaining) % 10 == 0 or time_remaining < 10:
                 logger.debug(f"Time until next continuation prompt: {time_remaining:.1f}s")

            if elapsed_time > INACTIVITY_DELAY:
                if initial_prompt_sent:
                    logger.info("Inactivity period elapsed, sending continuation prompt...")
                    for platform in PLATFORM:
                        platform_config = config["platforms"].get(platform, {})
                        options = platform_config.get("options", {})
                        general_config = config.get("general", {})
                        
                        # Get paths for prompt generation
                        continuation_prompt_file = platform_config.get("continuation_prompt_file_path", None)
                        task_file = platform_config.get("task_file_path", "tasks.md")
                        context_file = platform_config.get("additional_context_path", "context.md")
                        
                        # Resolve absolute paths relative to project path if needed
                        # Apply project path override if provided by command line
                        if args.project_path and platform == PLATFORM[0]:  # Apply override to first/active platform
                            project_path = args.project_path
                            logger.info(f"Using command line project path override for continuation prompt: {project_path}")
                        else:
                            project_path = os.path.expanduser(platform_config.get("project_path", "."))
                            
                        continuation_prompt_file = os.path.join(project_path, continuation_prompt_file) if continuation_prompt_file else None
                        task_file = os.path.join(project_path, task_file)
                        context_file = os.path.join(project_path, context_file)
                        
                        # Try reading custom prompt file
                        continuation_prompt_template = read_prompt_from_file(continuation_prompt_file)
                        
                        if continuation_prompt_template:
                            logger.debug(f"Using continuation prompt template from file: {continuation_prompt_file}")
                        else:
                            # Fallback 1: general.inactivity_prompt
                            continuation_prompt_template = general_config.get("inactivity_prompt")
                            if continuation_prompt_template:
                                logger.debug("Using continuation prompt template from general.inactivity_prompt")
                            else:
                                # Fallback 2: Default continuation prompt
                                continuation_prompt_template = DEFAULT_CONTINUATION_PROMPT
                                logger.debug("Using default continuation prompt template")

                        # Format the prompt
                        try:
                            continuation_prompt_content = continuation_prompt_template.format(task_file_path=task_file, additional_context_path=context_file)
                        except KeyError as e:
                            logger.error(f"Error formatting continuation prompt template (missing key {e}). Using raw template.")
                            continuation_prompt_content = continuation_prompt_template
                            
                        logger.debug(f"Sending continuation prompt content to {platform} (length: {len(continuation_prompt_content)})...")
                        
                        # Only send if not in no-send mode
                        if not args.no_send:
                            # Activate window
                            window_title = platform_config.get("window_title", platform)
                            activate_window(window_title)
                            time.sleep(0.5)
                            
                            # Type the prompt
                            send_keystroke_string(continuation_prompt_content, platform)
                        else:
                            logger.info(f"Skipping continuation prompt to {platform} (--no-send enabled)")
                        
                    last_activity_time = time.time() # Reset timer after sending prompt
                else:
                    # This case should ideally not happen if initialization logic is correct
                    # but handles the state where the flag file wasn't created.
                    logger.warning("Inactivity period elapsed, but initial prompt flag not found. Check initialization.")
                    # Optionally, send initial prompt again or just wait
                    last_activity_time = time.time() # Reset timer anyway
            
            # Sleep for a short interval
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Watcher stopped by user")
    except Exception as e:
        logger.error(f"Error in watcher loop: {e}")
        logger.exception("Full traceback:")
    finally:
        logger.info("Watcher stopped")

def analyze_vision(file_path, prompt):
    """
    Analyze a file using OpenAI Vision API
    Returns dict with question and keystrokes if successful, None otherwise
    """
    try:
        # Check if OpenAI client is initialized
        if not openai_client:
            logger.error("OpenAI client not initialized")
            return None
            
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return None
            
        # Check if OpenAI config exists
        if not config.get("openai", {}).get("vision", {}):
            logger.error("OpenAI Vision configuration not found")
            return None
            
        # Get OpenAI vision config
        vision_config = config["openai"]["vision"]
        model = vision_config.get("model", "gpt-4-vision-preview")
        max_tokens = vision_config.get("max_tokens", 300)
        temperature = vision_config.get("temperature", 0.7)
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Create base64 encoded image
        image_b64 = base64.b64encode(file_content).decode('utf-8')
        
        # Call OpenAI Vision API
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Parse response
        content = response.choices[0].message.content
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            logger.error(f"Failed to parse vision response: {content}")
            return None
            
    except Exception as e:
        logger.error(f"Error in vision analysis: {e}")
        return None

def send_prompt(prompt, platform=None, delay_ms=0):
    """
    Send a prompt to the specified platform
    Args:
        prompt: The prompt text to send
        platform: The platform to send the prompt to (defaults to first platform)
        delay_ms: Delay in milliseconds before sending keystrokes
    """
    try:
        # Check if sending is disabled via command line
        if args.no_send:
            logger.info(f"Sending prompt to {platform} skipped (--no-send enabled): {prompt}")
            return
            
        # Get platform configuration
        if not platform:
            platform = PLATFORM[0]
            
        platform_config = config["platforms"].get(platform, {})
        if not platform_config:
            logger.error(f"No configuration found for platform {platform}")
            return
            
        # Get keystrokes for platform
        keystrokes = platform_config.get("keystrokes", {})
        if not keystrokes:
            logger.error(f"No keystrokes configured for platform {platform}")
            return
            
        # Map platform-specific keys
        mapped_keys = []
        for key in prompt:
            if key in keystrokes:
                mapped_keys.append(keystrokes[key])
            else:
                mapped_keys.append(key)
                
        # Send keystrokes
        if mapped_keys:
            logger.info(f"Sending keystrokes to {platform}: {mapped_keys}")
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            for key in mapped_keys:
                send_keystroke(key, platform)
                
    except Exception as e:
        logger.error(f"Error sending prompt to {platform}: {e}")

def send_keystroke(key, platform):
    """
    Send a keystroke to the specified platform
    Args:
        key: The keystroke to send
        platform: The platform to send the keystroke to
    """
    try:
        # Check if sending is disabled via command line
        if args.no_send:
            logger.info(f"Sending keystroke to {platform} skipped (--no-send enabled): {key}")
            return
            
        logger.info(f"Sending keystroke to {platform}: {key}")
        
        # Get platform configuration
        platform_config = config["platforms"].get(platform, {})
        if not platform_config:
            logger.error(f"No configuration found for platform {platform}")
            return
            
        # Get window title for platform
        window_title = platform_config.get("window_title", platform)
        if window_title:
            activate_window(window_title)
            
        # Check if it's a keyboard shortcut (contains +)
        if "+" in key:
            key_parts = key.split("+")
            
            if platform == "cursor":
                # Cursor uses pyautogui for keyboard shortcuts
                if pyautogui:
                    logger.info(f"Sending hotkey to {platform}: {key_parts}")
                    pyautogui.hotkey(*key_parts)
                else:
                    logger.error("pyautogui not available")
            elif platform == "windsurf":
                # Windsurf uses AppleScript for keyboard shortcuts
                modifiers = []
                for mod in key_parts[:-1]:
                    if mod == "command":
                        modifiers.append("command down")
                    elif mod == "shift":
                        modifiers.append("shift down")
                    elif mod == "option" or mod == "alt":
                        modifiers.append("option down")
                    elif mod == "control" or mod == "ctrl":
                        modifiers.append("control down")
                
                # Get the key (last part after splitting by +)
                key_char = key_parts[-1]
                
                # Special case for function keys and other special keys
                if key_char.startswith("f") and key_char[1:].isdigit():
                    # Function keys use key code
                    fn_num = int(key_char[1:])
                    # F1-F12 key codes (F1=122, F2=120, etc.)
                    fn_codes = {1: 122, 2: 120, 3: 99, 4: 118, 5: 96, 6: 97, 
                               7: 98, 8: 100, 9: 101, 10: 109, 11: 103, 12: 111}
                    if fn_num in fn_codes:
                        code = fn_codes[fn_num]
                        applescript = f'tell application "System Events" to key code {code}'
                        if modifiers:
                            applescript = f'tell application "System Events" to key code {code} using {{{", ".join(modifiers)}}}'
                        logger.info(f"Sending AppleScript: {applescript}")
                        subprocess.run(['osascript', '-e', applescript])
                elif len(key_char) == 1:
                    # Single character
                    applescript = f'tell application "System Events" to keystroke "{key_char}"'
                    if modifiers:
                        applescript = f'tell application "System Events" to keystroke "{key_char}" using {{{", ".join(modifiers)}}}'
                    logger.info(f"Sending AppleScript: {applescript}")
                    subprocess.run(['osascript', '-e', applescript])
                else:
                    # Special keys like return, space, etc.
                    special_keys = {
                        "return": 36, "enter": 36, "tab": 48, "space": 49,
                        "delete": 51, "escape": 53, "esc": 53,
                        "left": 123, "right": 124, "up": 126, "down": 125
                    }
                    if key_char.lower() in special_keys:
                        code = special_keys[key_char.lower()]
                        applescript = f'tell application "System Events" to key code {code}'
                        if modifiers:
                            applescript = f'tell application "System Events" to key code {code} using {{{", ".join(modifiers)}}}'
                        logger.info(f"Sending AppleScript: {applescript}")
                        subprocess.run(['osascript', '-e', applescript])
                    else:
                        # Try to send as text
                        applescript = f'tell application "System Events" to keystroke "{key_char}"'
                        if modifiers:
                            applescript = f'tell application "System Events" to keystroke "{key_char}" using {{{", ".join(modifiers)}}}'
                        logger.info(f"Sending AppleScript: {applescript}")
                        subprocess.run(['osascript', '-e', applescript])
                
                # Release modifiers
                for mod in reversed(key_parts[:-1]):
                    if mod in ["command", "shift", "option", "alt", "control", "ctrl"]:
                        mod_name = mod
                        if mod == "alt": mod_name = "option"
                        if mod == "ctrl": mod_name = "control"
                        subprocess.run(['osascript', '-e', f'tell application "System Events" to key up {mod_name}'])
        else:
            # Regular single keystroke
            if platform == "cursor":
                # Cursor uses pyautogui
                if pyautogui:
                    logger.info(f"Sending key press to {platform}: {key}")
                    pyautogui.press(key)
                else:
                    logger.error("pyautogui not available")
            elif platform == "windsurf":
                # Windsurf uses applescript
                # Check if it's a special key
                special_keys = {
                    "return": 36, "enter": 36, "tab": 48, "space": 49,
                    "delete": 51, "escape": 53, "esc": 53,
                    "left": 123, "right": 124, "up": 126, "down": 125
                }
                if key.lower() in special_keys:
                    code = special_keys[key.lower()]
                    applescript = f'tell application "System Events" to key code {code}'
                    logger.info(f"Sending AppleScript key code: {applescript}")
                    subprocess.run(['osascript', '-e', applescript])
                else:
                    applescript = f'tell application "System Events" to keystroke "{key}"'
                    logger.info(f"Sending AppleScript keystroke: {applescript}")
                    subprocess.run(['osascript', '-e', applescript])
            else:
                logger.error(f"Unsupported platform: {platform}")
                
    except Exception as e:
        logger.error(f"Error sending keystroke to {platform}: {e}")
        logger.exception("Full traceback:")
        
def activate_window(title):
    """
    Activate a window by its title
    Args:
        title: The window title to activate
    """
    try:
        logger.debug(f"Activating window: {title}")
        
        # Special case for Windsurf - check both capitalizations
        if title.lower() == "windsurf":
            windsurf_variants = ["Windsurf", "WindSurf", "windsurf", "WINDSURF"]
            logger.debug(f"Using multiple variants for Windsurf: {windsurf_variants}")
            
            # Try each variant
            for variant in windsurf_variants:
                try:
                    if OS_TYPE == "darwin":
                        activate_script = f'''
                        tell application "{variant}"
                            activate
                        end tell
                        '''
                        result = subprocess.run(['osascript', '-e', activate_script], 
                                            capture_output=True, check=False)
                        logger.debug(f"Tried to activate {variant}, result: {result.returncode}")
                        if result.returncode == 0:
                            logger.debug(f"Successfully activated {variant}")
                            title = variant
                            time.sleep(0.5)
                            break
                except Exception as e:
                    logger.debug(f"Failed to activate {variant}: {str(e)}")
                    continue
                    
        if OS_TYPE == "darwin":
            # On macOS, first activate the application directly
            activate_script = f'''
            tell application "{title}"
                activate
            end tell
            '''
            
            try:
                # Try to activate by exact application name
                logger.debug(f"Trying to activate application directly: {title}")
                subprocess.run(['osascript', '-e', activate_script], check=False)
                
                # Wait for application to come to foreground
                time.sleep(0.5)
                
                # Additional check if application is running
                is_running_script = f'''
                tell application "System Events"
                    set isRunning to (exists (processes where name is "{title}"))
                end tell
                '''
                result = subprocess.run(['osascript', '-e', is_running_script], 
                                       capture_output=True, text=True, check=False)
                
                # If application is running, we're good
                if "true" in result.stdout.lower():
                    logger.debug(f"Application {title} is running")
                else:
                    # Try to find by partial name match
                    logger.debug(f"Application not found by exact name, trying alternative approaches")
                    
                    # Try different variations of the name
                    possible_names = [title, title.lower(), title.upper(), title.title()]
                    for name in possible_names:
                        alt_script = f'''
                        tell application "System Events"
                            set appList to name of every application process
                            repeat with appName in appList
                                if appName contains "{name}" then
                                    tell process appName to set frontmost to true
                                    return appName
                                end if
                            end repeat
                            return ""
                        end tell
                        '''
                        result = subprocess.run(['osascript', '-e', alt_script], 
                                             capture_output=True, text=True, check=False)
                        found_app = result.stdout.strip()
                        if found_app:
                            logger.debug(f"Found and activated application: {found_app}")
                            break
            except Exception as e:
                logger.warning(f"Failed to activate {title}: {e}")
                # Continue with the basic approach as a fallback
                
            logger.debug(f"Application {title} should now be active")
        elif OS_TYPE == "windows":
            # On Windows, use win32gui to activate the window
            if win32gui and win32con:
                hwnd = win32gui.FindWindow(None, title)
                if hwnd:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    logger.debug(f"Activated {title} window on Windows")
                else:
                    logger.warning(f"Window '{title}' not found on Windows")
            else:
                logger.warning("win32gui not available")
        else:
            # On Linux, use xdotool if available
            try:
                subprocess.run(['xdotool', 'search', '--name', title, 'windowactivate'], check=False)
                logger.debug(f"Activated {title} window on Linux")
            except FileNotFoundError:
                logger.warning("xdotool not available")
    except Exception as e:
        logger.error(f"Error activating window: {e}")
        logger.exception("Full traceback:")

def send_keystroke_string(text, platform):
    """
    Send a string of text to the specified platform by typing it
    Args:
        text: The text to send
        platform: The platform to send the text to
    """
    try:
        # Check if sending is disabled via command line
        if args.no_send:
            logger.info(f"Sending text to {platform} skipped (--no-send enabled): {text[:100]}...")
            return
            
        logger.info(f"Sending text to {platform}: {text}")
        
        # Get platform configuration
        platform_config = config["platforms"].get(platform, {})
        if not platform_config:
            logger.error(f"No configuration found for platform {platform}")
            return
        
        # Get the window title from configuration, or use default
        window_title = platform_config.get("window_title", platform)
        
        # First try to activate the window
        try:
            activate_window(window_title)
            # Small delay to ensure window is active
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Failed to activate window, but will try to send keystrokes anyway: {e}")
        
        # Send the keystrokes
        if platform == "cursor":
            # Cursor uses pyautogui
            if pyautogui:
                # Split text by newlines and type each line with Enter after
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    pyautogui.write(line)
                    if i < len(lines) - 1:  # Don't press Enter after the last line
                        pyautogui.press('return')
                
                # Press Enter after the entire text
                time.sleep(0.2)
                pyautogui.press('return')
                logger.info("Pressed Enter after typing text")
            else:
                logger.error("pyautogui not available")
        elif platform == "windsurf":
            # For macOS, we need to handle newlines specially
            if OS_TYPE == "darwin":
                # Split text by newlines to handle them properly
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    # Escape double quotes in the line
                    escaped_line = line.replace('"', '\\"')
                    
                    # Build the AppleScript for the current line
                    line_script = f'''
                    tell application "System Events"
                        keystroke "{escaped_line}"
                    end tell
                    '''
                    
                    # Run the AppleScript for this line
                    subprocess.run(['osascript', '-e', line_script], check=False)
                    
                    # If not the last line, press Shift+Return for a newline
                    if i < len(lines) - 1:
                        # Use shift+return for newline instead of submitting
                        shift_return_script = '''
                        tell application "System Events"
                            key code 36 using {shift down}
                        end tell
                        '''
                        subprocess.run(['osascript', '-e', shift_return_script], check=False)
                        time.sleep(0.1)  # Small delay between lines
                
                # Press Return after the entire text to submit it
                time.sleep(0.3)  # Slightly longer delay before final Enter
                subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 36'], check=False)
                logger.info("Pressed Enter after typing text")
            else:
                # Non-macOS platforms may handle this differently
                logger.warning("Newline handling for non-macOS platforms not fully implemented")
        else:
            logger.error(f"Unsupported platform: {platform}")
    
    except Exception as e:
        logger.error(f"Error sending text to {platform}: {e}")
        logger.exception("Full traceback:")

if __name__ == "__main__":
    run_watcher()
