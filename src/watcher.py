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
PLATFORM = []  # List of active platform names
PLATFORM_STATE = {} # Dict to hold state per platform: {platform_name: {'last_activity': 0.0, ...}}
WATCH_PATH = ""
INACTIVITY_DELAY = 0
last_global_prompt_time = 0.0 # Track time of the last prompt sent to any platform

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
TASK_FILE_PATH = "tasks.md"
LAST_README_MTIME = None
TASK_COMPLETED = False
slack_client = None

def load_config():
    """
    Load configuration from YAML file and initialize global variables, including PLATFORM_STATE
    Returns True if successful, False otherwise
    """
    try:
        global config, PLATFORM, PLATFORM_STATE, openai_client, GITIGNORE_PATTERNS, TASK_FILE_PATH
        
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
            
        # Determine active platforms
        active_platforms = []
        if args.platform:
            requested_platforms = [p.strip() for p in args.platform.split(',') if p.strip()]
            logger.info(f"Platform override from command line: {requested_platforms}")
            # Validate requested platforms against config
            valid_platforms = []
            invalid_platforms = []
            for p in requested_platforms:
                if p in config["platforms"]:
                    valid_platforms.append(p)
                else:
                    invalid_platforms.append(p)
            if invalid_platforms:
                 logger.error(f"Invalid platform(s) specified via --platform: {invalid_platforms}. Valid platforms in config: {list(config['platforms'].keys())}")
                 return False
            active_platforms = valid_platforms
        else:
            # Initialize platforms - check general.active_platforms first
            if config.get("general", {}).get("active_platforms"):
                cfg_active_platforms = config["general"]["active_platforms"]
                logger.debug(f"Using active_platforms from general section: {cfg_active_platforms}")
                # Filter the list to only include platforms that exist in the config
                active_platforms = [p for p in cfg_active_platforms if p in config["platforms"]]
            else:
                # Fallback to using all platforms defined
                logger.warning("general.active_platforms not set in config, activating ALL defined platforms.")
                active_platforms = list(config["platforms"].keys())
            
        PLATFORM = active_platforms # Set the global list of active platform names
        logger.debug(f"Final active platforms: {PLATFORM}")
        
        if not PLATFORM:
            logger.error("No platforms enabled or active")
            return False
            
        # Initialize OpenAI client if configured (remains global)
        if config.get("openai", {}).get("api_key"):
            logger.debug("Initializing OpenAI client")
            openai_client = OpenAI(api_key=config["openai"]["api_key"])
        else:
            logger.warning("OpenAI API key not configured")
            openai_client = None
            
        # Set global TASK_FILE_PATH (assuming it's shared or take first platform's)
        # This might need adjustment if it's truly per-platform
        first_platform_cfg = config["platforms"].get(PLATFORM[0], {})
        TASK_FILE_PATH = first_platform_cfg.get("task_file_path", "tasks.md")
        logger.debug(f"Set global TASK_FILE_PATH to: {TASK_FILE_PATH}")

        # Initialize PLATFORM_STATE for each active platform
        PLATFORM_STATE = {}
        all_project_paths = set() # To load gitignore patterns later
        
        for platform_name in PLATFORM:
            logger.debug(f"Initializing state for platform: {platform_name}")
            platform_config = config["platforms"].get(platform_name, {})
            if not platform_config:
                logger.error(f"Configuration missing for active platform {platform_name}")
                return False # Should not happen due to earlier checks, but safety first
                
            # Get project path - apply command line override if specified
            # Note: Command line --project-path applies to ALL active platforms currently
            if args.project_path:
                project_path = args.project_path
                logger.info(f"Using project path override from command line for {platform_name}: {project_path}")
                # Optionally update the main config dict? Not strictly necessary if PLATFORM_STATE holds the active path
                # config["platforms"][platform_name]["project_path"] = project_path 
            else:
                project_path = platform_config.get("project_path", "")
            
            logger.debug(f"Raw project path for {platform_name}: {project_path}")
            
            if not project_path:
                logger.error(f"Project path not configured for platform {platform_name}")
                return False
                
            # Expand user directory
            project_path = os.path.expanduser(project_path)
            logger.debug(f"Expanded project path for {platform_name}: {project_path}")
            
            if not os.path.exists(project_path):
                logger.error(f"Project path does not exist for platform {platform_name}: {project_path}")
                # Optionally allow script to continue if some paths exist? For now, fail.
                return False
                
            all_project_paths.add(project_path)

            # Get inactivity delay - apply command line override if specified
            # Note: Command line --inactivity-delay applies to ALL active platforms currently
            if args.inactivity_delay:
                inactivity_delay = args.inactivity_delay
                logger.info(f"Using inactivity delay override from command line for {platform_name}: {inactivity_delay}")
            else:
                # Use platform-specific delay, fallback to general, fallback to default
                inactivity_delay = platform_config.get("inactivity_delay", config.get("general", {}).get("inactivity_delay", 120))
                logger.debug(f"Using inactivity delay for {platform_name}: {inactivity_delay}")

            # Populate state for this platform
            PLATFORM_STATE[platform_name] = {
                "project_path": project_path,
                "inactivity_delay": inactivity_delay,
                "last_activity": time.time(), # Initialize activity time
                "last_prompt_time": 0.0,
                "watch_handler": None, # Placeholder for watchdog handler
                "observer": None, # Placeholder for watchdog observer
                # Add other per-platform state vars as needed (e.g., specific prompt files)
                "task_file_path": platform_config.get("task_file_path", TASK_FILE_PATH), # Use platform specific or global
                "continuation_prompt_file_path": platform_config.get("continuation_prompt_file_path", "continuation_prompt.txt"),
                "initial_prompt_file_path": platform_config.get("initial_prompt_file_path", None), # Optional
                "window_title": platform_config.get("window_title", None) # Important for activation
            }
            logger.debug(f"State for {platform_name}: {PLATFORM_STATE[platform_name]}")
            
        # Load gitignore patterns - Use patterns from *all* unique project paths?
        # For simplicity, let's use the first platform's path for now.
        # A more robust solution might merge patterns or handle ignores per-path.
        first_project_path = PLATFORM_STATE[PLATFORM[0]]["project_path"]
        logger.info(f"Loading gitignore patterns based on project path: {first_project_path}")
        GITIGNORE_PATTERNS = load_gitignore_patterns(first_project_path)
        
        # Log combined configuration overview
        logger.info("Configuration loaded successfully for multiple platforms:")
        for platform_name in PLATFORM:
             state = PLATFORM_STATE[platform_name]
             logger.info(f"  Platform: {platform_name}")
             logger.info(f"    Project Path: {state['project_path']}")
             logger.info(f"    Inactivity Delay: {state['inactivity_delay']}s")
             logger.info(f"    Window Title: {state.get('window_title', 'N/A')}")
             # Add more logged state vars if helpful
        logger.info(f"Loaded {len(GITIGNORE_PATTERNS)} gitignore patterns (from {first_project_path})")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True) # Add traceback
        return False

# Helper function to get config for a specific platform
def get_platform_config(platform_name: str) -> Dict:
    """
    Retrieve the static configuration for a given platform name.
    """
    if not config: # Ensure config is loaded
         logger.warning("Accessing platform config before load_config called.")
         return {}
    return config.get("platforms", {}).get(platform_name, {})

# Helper function to get state for a specific platform
def get_platform_state(platform_name: str) -> Dict:
    """
    Retrieve the dynamic state for a given platform name.
    """
    if not PLATFORM_STATE: # Ensure state is initialized
         logger.warning("Accessing platform state before load_config called.")
         return {}
    return PLATFORM_STATE.get(platform_name, {})

def check_vision_conditions(file_path, event_type, platform_name):
    """
    Check if vision analysis should be triggered for a file change
    Returns tuple of (question, keystrokes) if conditions are met, None otherwise
    """
    try:
        # Skip if OpenAI is not configured
        if not openai_client:
            logger.debug(f"[{platform_name}] Skipping vision analysis - OpenAI client not initialized")
            return None

        # Get platform-specific configuration and options
        platform_config = get_platform_config(platform_name)
        options = platform_config.get("options", {})
        vision_options = config.get("openai", {}).get("vision", {}) # Global vision config

        if not vision_options.get("enabled", False):
             logger.debug(f"[{platform_name}] Skipping vision analysis - Global OpenAI Vision not enabled.")
             return None

        # Check platform-specific vision conditions
        platform_vision_conditions = options.get("vision_conditions", [])
        if not platform_vision_conditions:
            logger.debug(f"[{platform_name}] Skipping vision analysis - No vision_conditions defined for this platform.")
            return None

        # Check if file exists (should normally exist for modify/create)
        if not os.path.exists(file_path):
            logger.warning(f"[{platform_name}] File does not exist for vision check: {file_path}")
            return None

        condition_met = None
        for condition in platform_vision_conditions:
            file_pattern = condition.get("file_type")
            action_trigger = condition.get("action") # e.g., "save" (maps to modify/create)

            # Check if action matches event type
            action_matches = False
            if action_trigger == "save" and event_type in ["modified", "created"]:
                action_matches = True
            # Add other action mappings if needed

            # Check if file pattern matches
            file_matches = False
            if file_pattern and fnmatch.fnmatch(os.path.basename(file_path), file_pattern):
                file_matches = True

            if action_matches and file_matches:
                condition_met = condition
                logger.debug(f"[{platform_name}] Vision condition met for {file_path}: {condition}")
                break # Use the first matching condition

        if not condition_met:
            logger.debug(f"[{platform_name}] No matching vision condition found for {file_path} and event {event_type}")
            return None

        # Get question and keystrokes from the matched condition
        question = condition_met.get("question")
        success_keystrokes = condition_met.get("success_keystrokes", []) # TODO: Actually use the vision result to decide success/failure
        # failure_keystrokes = condition_met.get("failure_keystrokes", [])

        if not question:
             logger.warning(f"[{platform_name}] Vision condition matched, but no 'question' defined: {condition_met}")
             return None # Or decide on default behavior

        # --- TODO: Implement actual vision call and result processing ---
        # 1. Take screenshot (using pyautogui or platform-specific tool)
        # 2. Encode screenshot
        # 3. Call OpenAI Vision API with screenshot and `question`
        # 4. Parse response - does it indicate success or failure based on the question?
        # 5. Return the appropriate keystrokes (success_keystrokes or failure_keystrokes)
        logger.info(f"[{platform_name}] Vision condition met. Question: '{question}'. Sending SUCCESS keystrokes for now.")
        # For now, assume success and return success_keystrokes
        if not success_keystrokes:
             logger.warning(f"[{platform_name}] Vision condition matched, but no 'success_keystrokes' defined: {condition_met}")
             return None

        return question, success_keystrokes # Returning question for logging, keystrokes for action

    except Exception as e:
        logger.error(f"[{platform_name}] Error checking vision conditions: {e}", exc_info=True)
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
    Main watcher loop: Sets up observers, handles initialization,
    and manages inactivity/staggered prompts for multiple platforms.
    """
    logger.debug("Starting run_watcher...")

    global CONFIG_MTIME, last_global_prompt_time

    # Load configuration
    if not load_config():
        logger.error("Failed to load initial configuration. Exiting.")
        return

    # --- Setup Watchdog Observers ---
    observers = []
    if not PLATFORM_STATE:
         logger.error("PLATFORM_STATE is empty after loading config. Exiting.")
         return

    for platform_name, state in PLATFORM_STATE.items():
        project_path = state.get("project_path")
        if not project_path or not os.path.isdir(project_path):
            logger.error(f"[{platform_name}] Invalid project path: {project_path}. Skipping observer setup.")
            continue

        logger.info(f"[{platform_name}] Setting up file watcher for path: {project_path}")
        event_handler = PlatformEventHandler(platform_name)
        observer = Observer()
        observer.schedule(event_handler, project_path, recursive=True)

        # Store observer and handler in state
        state["observer"] = observer
        state["watch_handler"] = event_handler # Might not be strictly needed if handler acts directly

        observers.append(observer) # Keep track for starting/stopping all
        logger.debug(f"[{platform_name}] Observer scheduled.")

    if not observers:
        logger.error("No valid observers could be scheduled. Exiting.")
        return

    # Start all observers
    for observer in observers:
        observer.start()
    logger.info(f"Started {len(observers)} file watcher observers.")


    # Initialize configuration tracking
    if os.path.exists(CONFIG_PATH):
        CONFIG_MTIME = os.path.getmtime(CONFIG_PATH)
        logger.debug(f"Initialized CONFIG_MTIME to {CONFIG_MTIME}")

    # Check if initial prompt has already been sent
    initial_prompt_sent = os.path.exists(INITIAL_PROMPT_SENT_FILE)
    logger.debug(f"Initial prompt sent file exists: {initial_prompt_sent}")

    # --- Send Initialization Keystrokes/Initial Prompt ---
    if not initial_prompt_sent:
        logger.info("Initial prompt file not found. Sending initial prompts/keystrokes...")
        for platform_name in PLATFORM: # Iterate through the active platforms
            platform_config = get_platform_config(platform_name)
            platform_state = get_platform_state(platform_name)
            if not platform_config or not platform_state: continue # Should not happen

            initialization = platform_config.get("initialization", [])
            options = platform_config.get("options", {}) # Platform specific options
            general_config = config.get("general", {}) # Global options

            # Get paths for prompt generation - use state for paths
            initial_prompt_file = platform_state.get("initial_prompt_file_path") # Already resolved in load_config? Check load_config. No, need resolve here.
            task_file = platform_state.get("task_file_path") # Already resolved in load_config? Yes.
            context_file = platform_state.get("additional_context_path") # Needs resolving

            project_path = platform_state.get("project_path")
            initial_prompt_file = os.path.join(project_path, initial_prompt_file) if initial_prompt_file else None
            context_file = os.path.join(project_path, context_file) if context_file else None
            task_file = os.path.join(project_path, task_file) # Ensure task_file is also absolute

            # Use global initial prompt setting from general config as default base
            # Platform-specific initial_prompt_file takes precedence
            default_initial_prompt_template = general_config.get("initial_prompt", DEFAULT_INITIAL_PROMPT)
            initial_prompt_template = read_prompt_from_file(initial_prompt_file) or default_initial_prompt_template
            logger.debug(f"[{platform_name}] Using initial prompt template (from file: {bool(initial_prompt_file)})")

            # Format the prompt
            try:
                # Make sure paths exist before formatting
                task_file_content = ""
                if task_file and os.path.exists(task_file):
                    # task_file_content = read file content - maybe just pass path?
                    pass # Keep path for now
                else:
                    logger.warning(f"[{platform_name}] Task file not found: {task_file}")
                    task_file = "" # Avoid formatting error

                context_file_content = ""
                if context_file and os.path.exists(context_file):
                     # context_file_content = read file content - maybe just pass path?
                     pass # Keep path for now
                else:
                     logger.warning(f"[{platform_name}] Context file not found: {context_file}")
                     context_file = "" # Avoid formatting error

                # Format prompt, providing empty string if files don't exist
                initial_prompt_content = initial_prompt_template.format(
                    task_file_path=task_file,
                    additional_context_path=context_file
                )
            except KeyError as e:
                logger.error(f"[{platform_name}] Error formatting initial prompt template (missing key {e}). Using raw template.")
                initial_prompt_content = initial_prompt_template # Send raw template if formatting fails

            logger.debug(f"[{platform_name}] Initialization config: {initialization}")
            logger.debug(f"[{platform_name}] Final initial_prompt content length: {len(initial_prompt_content)}")

            # Activate window first
            window_title = platform_state.get("window_title", platform_name)
            logger.info(f"[{platform_name}] Activating window for initialization: {window_title}")
            if not args.no_send: activate_window(window_title)
            time.sleep(1) # Give time for window activation

            # Send initialization keystrokes
            if initialization and not args.no_send:
                logger.info(f"[{platform_name}] Sending initialization keystrokes...")
                for keystroke in initialization:
                    keys = keystroke.get("keys", "")
                    delay_ms = keystroke.get("delay_ms", 0)
                    if keys:
                        logger.debug(f"[{platform_name}] Sending init key: {keys}")
                        if delay_ms > 0:
                            time.sleep(delay_ms / 1000.0)
                        send_keystroke(keys, platform_name) # Pass platform name
            elif initialization and args.no_send:
                logger.info(f"[{platform_name}] Skipping initialization keystrokes (--no-send enabled)")

            # Send initial prompt content
            if initial_prompt_content:
                 if not args.no_send:
                     logger.info(f"[{platform_name}] Sending initial prompt content...")
                     # Activate window again just in case
                     activate_window(window_title)
                     time.sleep(0.5)
                     send_keystroke_string(initial_prompt_content, platform_name) # Pass platform name
                     platform_state["last_activity"] = time.time() # Reset timer after sending prompt
                     platform_state["last_prompt_time"] = time.time()
                     last_global_prompt_time = time.time() # Update global time too
                 else:
                     logger.info(f"[{platform_name}] Skipping initial prompt content (--no-send enabled)")
                     platform_state["last_activity"] = time.time() # Reset timer anyway

        # Create the flag file after attempting for all platforms
        try:
            with open(INITIAL_PROMPT_SENT_FILE, 'w') as f:
                f.write("Initial prompt sent attempt at: " + datetime.now().isoformat())
            logger.info(f"Created initial prompt sent file: {INITIAL_PROMPT_SENT_FILE}")
            initial_prompt_sent = True # Update state
        except Exception as e:
            logger.error(f"Failed to create initial prompt sent file: {e}")
    else:
        logger.info("Initial prompt file found. Skipping initial prompts/keystrokes.")
        # Ensure initial activity time is set even if skipping prompts
        current_time = time.time()
        for state in PLATFORM_STATE.values():
             state["last_activity"] = current_time


    # --- Main Loop ---
    try:
        logger.info("Entering main watcher loop...")
        stagger_delay = config.get("general", {}).get("stagger_delay", 90) # Get stagger delay

        while True:
            current_time = time.time()

            # Check for configuration changes
            if os.path.exists(CONFIG_PATH):
                current_mtime = os.path.getmtime(CONFIG_PATH)
                if current_mtime > CONFIG_MTIME:
                    logger.info("Configuration file changed, reloading...")
                    # TODO: Handle observer restart/update if paths change
                    if not load_config():
                        logger.error("Failed to reload configuration, continuing with previous settings")
                    else:
                        CONFIG_MTIME = current_mtime
                        stagger_delay = config.get("general", {}).get("stagger_delay", 90) # Update stagger delay
                        # Need logic here to stop/remove/add/reschedule observers if project paths changed
                        logger.warning("Config reloaded, but observer paths might be stale. Restart recommended for path changes.")

            # --- Inactivity Check and Staggered Prompt Sending ---
            inactive_platforms = []
            for platform_name, state in PLATFORM_STATE.items():
                inactivity_delay = state.get("inactivity_delay", 120)
                last_activity = state.get("last_activity", current_time) # Default to now if not set
                elapsed_time = current_time - last_activity

                # Log countdown periodically
                time_remaining = inactivity_delay - elapsed_time
                if int(time_remaining) % 30 == 0 or time_remaining < 15: # Log every 30s or when close
                    logger.debug(f"[{platform_name}] Time until inactive: {time_remaining:.1f}s")

                if elapsed_time > inactivity_delay:
                    if initial_prompt_sent: # Only consider inactive if initial prompts were sent
                        logger.debug(f"[{platform_name}] Inactivity detected (elapsed: {elapsed_time:.1f}s > delay: {inactivity_delay}s)")
                        inactive_platforms.append({
                            "name": platform_name,
                            "last_activity": last_activity,
                            "state": state,
                            "config": get_platform_config(platform_name)
                        })
                    else:
                        # Reset activity time if initial prompt wasn't sent yet but inactivity detected
                        # This prevents sending continuation prompts before initialization is done
                        logger.debug(f"[{platform_name}] Inactivity detected but initial prompt not sent yet. Resetting timer.")
                        state["last_activity"] = current_time


            # --- Staggering Logic ---
            if inactive_platforms:
                logger.info(f"Inactive platforms: {[p['name'] for p in inactive_platforms]}")

                # Check if stagger delay has passed since the last global prompt
                time_since_last_global_prompt = current_time - last_global_prompt_time
                if time_since_last_global_prompt >= stagger_delay:
                    logger.info(f"Stagger delay ({stagger_delay}s) passed. Time since last prompt: {time_since_last_global_prompt:.1f}s")

                    # Select the platform that has been inactive the longest
                    inactive_platforms.sort(key=lambda p: p["last_activity"])
                    platform_to_prompt = inactive_platforms[0]
                    platform_name = platform_to_prompt["name"]
                    state = platform_to_prompt["state"]
                    platform_config = platform_to_prompt["config"]
                    general_config = config.get("general", {})

                    logger.info(f"Selected platform '{platform_name}' for continuation prompt (inactive longest).")

                    # Prepare continuation prompt for the selected platform
                    continuation_prompt_file = state.get("continuation_prompt_file_path") # Resolved path from state? Check load_config. No.
                    task_file = state.get("task_file_path") # Resolved path from state
                    context_file = state.get("additional_context_path") # Needs resolving path from state? No, it's in platform_config.

                    project_path = state.get("project_path")
                    continuation_prompt_file = os.path.join(project_path, continuation_prompt_file) if continuation_prompt_file else None
                    context_file = os.path.join(project_path, platform_config.get("additional_context_path")) if platform_config.get("additional_context_path") else None # Use config for context path name
                    task_file = os.path.join(project_path, task_file) if task_file else None # Ensure task_file is absolute

                    # Determine prompt template (File > General > Default)
                    continuation_prompt_template = read_prompt_from_file(continuation_prompt_file)
                    source = "file"
                    if not continuation_prompt_template:
                        continuation_prompt_template = general_config.get("inactivity_prompt")
                        source = "general config"
                    if not continuation_prompt_template:
                        continuation_prompt_template = DEFAULT_CONTINUATION_PROMPT
                        source = "default"
                    logger.debug(f"[{platform_name}] Using continuation prompt template from: {source}")

                    # Format the prompt
                    try:
                        # Ensure paths exist before formatting
                         task_file_content = ""
                         if task_file and os.path.exists(task_file):
                             pass # Keep path
                         else:
                             logger.warning(f"[{platform_name}] Task file not found for continuation prompt: {task_file}")
                             task_file = ""

                         context_file_content = ""
                         if context_file and os.path.exists(context_file):
                              pass # Keep path
                         else:
                              logger.warning(f"[{platform_name}] Context file not found for continuation prompt: {context_file}")
                              context_file = ""

                         continuation_prompt_content = continuation_prompt_template.format(
                             task_file_path=task_file,
                             additional_context_path=context_file
                         )
                    except KeyError as e:
                        logger.error(f"[{platform_name}] Error formatting continuation prompt template (missing key {e}). Using raw template.")
                        continuation_prompt_content = continuation_prompt_template

                    logger.debug(f"[{platform_name}] Sending continuation prompt content (length: {len(continuation_prompt_content)})...")

                    # Send the prompt if not in no-send mode
                    if not args.no_send:
                        window_title = state.get("window_title", platform_name)
                        activate_window(window_title)
                        time.sleep(0.5)
                        send_keystroke_string(continuation_prompt_content, platform_name)
                    else:
                        logger.info(f"[{platform_name}] Skipping continuation prompt (--no-send enabled)")

                    # Update timers for the prompted platform AND the global timer
                    current_time = time.time() # Get fresh time
                    state["last_activity"] = current_time
                    state["last_prompt_time"] = current_time
                    last_global_prompt_time = current_time
                    logger.info(f"[{platform_name}] Continuation prompt sent. Updated last_activity and last_global_prompt_time.")

                else:
                    logger.debug(f"Stagger delay ({stagger_delay}s) not yet passed. Time since last global prompt: {time_since_last_global_prompt:.1f}s. Waiting.")


            # Sleep for a short interval
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Watcher stopping due to user interrupt (Ctrl+C)")
    except Exception as e:
        logger.error(f"Unhandled error in watcher main loop: {e}", exc_info=True)
    finally:
        logger.info("Stopping watcher observers...")
        for observer in observers:
            try:
                observer.stop()
                logger.debug(f"Observer stopped: {observer}")
            except Exception as e:
                 logger.error(f"Error stopping observer {observer}: {e}")
        # Wait for observer threads to finish
        for observer in observers:
            try:
                observer.join()
                logger.debug(f"Observer joined: {observer}")
            except Exception as e:
                  logger.error(f"Error joining observer {observer}: {e}")
        logger.info("All watcher observers stopped and joined.")
        logger.info("Watcher finished.")

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

def send_prompt(prompt_text, platform_name=None, delay_ms=0):
    """
    Send a prompt (as a sequence of actions/keystrokes defined in config)
    Args:
        prompt_text: The logical name of the prompt action (e.g., "explain_code")
                     or the raw text if no mapping is found (legacy behavior - avoid).
                     *** THIS FUNCTION DOES NOT SEND THE TEXT DIRECTLY ***
                     It sends the keystrokes associated with the 'prompt_text' key
                     in the platform's 'keystrokes' config section.
                     Use send_keystroke_string to send raw text.
        platform_name: The platform to send the prompt action to.
        delay_ms: Delay in milliseconds before starting actions.
    """
    try:
        if not platform_name:
            if not PLATFORM:
                 logger.error("No active platforms configured to send prompt to.")
                 return
            platform_name = PLATFORM[0] # Default to first active platform

        logger.info(f"[{platform_name}] Attempting to send prompt action: '{prompt_text}'")

        if args.no_send:
            logger.info(f"[{platform_name}] Sending prompt action skipped (--no-send enabled): {prompt_text}")
            return

        platform_config = get_platform_config(platform_name)
        if not platform_config:
            logger.error(f"[{platform_name}] No configuration found.")
            return

        # --- IMPORTANT CHANGE: This function sends configured KEYSTROKES, not the prompt text itself ---
        # Look for the 'prompt_text' as a key in the 'keystrokes' section of the config
        # This allows defining complex actions like "open_chat", "submit", etc.
        platform_keystrokes_config = platform_config.get("keystrokes", []) # Should be a list of dicts {keys:..., delay_ms:...}
        
        # Find the specific action definition matching 'prompt_text' if it exists
        # This part is interpretation - assuming 'keystrokes' in config is a LIST of actions,
        # not a simple map. If it IS a map, adjust logic. Let's assume it's a list for now.
        # If 'prompt_text' is meant to be looked up in a dict like: keystrokes: { "explain": ["cmd+l", ...]}, adjust.
        # Reverting to simpler assumption: platform_config["keystrokes"] is the list of actions for *this* platform.
        # The 'prompt_text' argument seems misused here based on previous code.
        # Let's assume send_prompt is intended to send a series of configured keystrokes.
        # The 'prompt_text' argument seems out of place. Maybe it should be 'action_name'?
        # --> Sticking to original logic: treat 'prompt_text' as the literal keys to send.
        # This seems wrong, but follows the prior implementation. Refactor needed if intent differs.

        logger.warning(f"[{platform_name}] 'send_prompt' function currently sends the 'prompt_text' argument ({prompt_text}) directly as keystrokes. This might not be the intended behavior if 'prompt_text' refers to a named action in config.")

        # Activate window
        window_title = get_platform_state(platform_name).get("window_title", platform_name)
        activate_window(window_title)

        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

        # Send the prompt_text directly as keystrokes (legacy behavior)
        send_keystroke(prompt_text, platform_name) # This might fail if prompt_text contains '+' etc.

    except Exception as e:
        logger.error(f"[{platform_name}] Error sending prompt action '{prompt_text}': {e}", exc_info=True)

def send_keystroke(key_combo, platform_name):
    """
    Send a single keystroke or a combination (e.g., "command+shift+p")
    Args:
        key_combo: The keystroke(s) to send.
        platform_name: The target platform.
    """
    try:
        if args.no_send:
            logger.info(f"[{platform_name}] Sending keystroke skipped (--no-send): {key_combo}")
            return

        logger.info(f"[{platform_name}] Sending keystroke: {key_combo}")

        platform_state = get_platform_state(platform_name)
        if not platform_state:
            logger.error(f"[{platform_name}] Cannot send keystroke, platform state not found.")
            return

        window_title = platform_state.get("window_title", platform_name)
        if window_title:
            activate_window(window_title)
            # Add a small delay after activation, especially important before typing
            time.sleep(0.2)
        else:
             logger.warning(f"[{platform_name}] No window title found in state, sending keystroke without activation.")

        # --- Platform-specific sending logic ---
        current_os = platform.system() # Get OS ('Darwin', 'Windows', 'Linux')

        if current_os == "Darwin":
             # Use AppleScript for macOS
             # Handle combinations first
             if "+" in key_combo:
                 parts = key_combo.split('+')
                 key = parts[-1].strip()
                 modifiers = [mod.strip().lower() for mod in parts[:-1]]

                 apple_modifiers = []
                 for mod in modifiers:
                     if mod in ["command", "cmd"]: apple_modifiers.append("command down")
                     elif mod == "shift": apple_modifiers.append("shift down")
                     elif mod in ["option", "opt", "alt"]: apple_modifiers.append("option down")
                     elif mod in ["control", "ctrl"]: apple_modifiers.append("control down")
                     else: logger.warning(f"[{platform_name}] Unknown modifier '{mod}' in combo '{key_combo}'")

                 using_clause = ""
                 if apple_modifiers:
                     using_clause = f' using {{{", ".join(apple_modifiers)}}}'

                 # Determine if it's a key code or keystroke
                 special_key_codes = {
                     "return": 36, "enter": 36, "tab": 48, "space": 49,
                     "delete": 51, "backspace": 51, # Added backspace alias
                     "escape": 53, "esc": 53,
                     "f1": 122, "f2": 120, "f3": 99, "f4": 118, "f5": 96, "f6": 97,
                     "f7": 98, "f8": 100, "f9": 101, "f10": 109, "f11": 103, "f12": 111,
                     "left": 123, "right": 124, "down": 125, "up": 126,
                     # Add more key codes as needed
                 }

                 if key.lower() in special_key_codes:
                     code = special_key_codes[key.lower()]
                     applescript = f'tell application "System Events" to key code {code}{using_clause}'
                 elif len(key) == 1:
                     # Need to escape special characters for keystroke command
                     key_escaped = key.replace('\\', '\\\\').replace('"', '\\"')
                     applescript = f'tell application "System Events" to keystroke "{key_escaped}"{using_clause}'
                 else:
                      logger.error(f"[{platform_name}] Cannot send complex key '{key}' via AppleScript keystroke. Use key code if possible.")
                      return

                 logger.debug(f"[{platform_name}] Running AppleScript: {applescript}")
                 subprocess.run(['osascript', '-e', applescript], check=False, capture_output=True)

             else:
                 # Single key press
                 key = key_combo.strip().lower()
                 special_key_codes = {
                     "return": 36, "enter": 36, "tab": 48, "space": 49,
                     "delete": 51, "backspace": 51, # Added backspace alias
                     "escape": 53, "esc": 53,
                     "f1": 122, "f2": 120, "f3": 99, "f4": 118, "f5": 96, "f6": 97,
                     "f7": 98, "f8": 100, "f9": 101, "f10": 109, "f11": 103, "f12": 111,
                     "left": 123, "right": 124, "down": 125, "up": 126,
                 }
                 if key in special_key_codes:
                     code = special_key_codes[key]
                     applescript = f'tell application "System Events" to key code {code}'
                     logger.debug(f"[{platform_name}] Running AppleScript: {applescript}")
                     subprocess.run(['osascript', '-e', applescript], check=False, capture_output=True)
                 elif len(key) == 1:
                      key_escaped = key.replace('\\', '\\\\').replace('"', '\\"')
                      applescript = f'tell application "System Events" to keystroke "{key_escaped}"'
                      logger.debug(f"[{platform_name}] Running AppleScript: {applescript}")
                      subprocess.run(['osascript', '-e', applescript], check=False, capture_output=True)
                 else:
                      logger.error(f"[{platform_name}] Cannot send single complex key '{key}' via AppleScript. Use key code or standard characters.")
                      return

        elif current_os in ["Windows", "Linux"]:
            # Use pyautogui for Windows/Linux
            if not pyautogui:
                 logger.error(f"[{platform_name}] pyautogui not available, cannot send keystroke on {current_os}")
                 return

            if "+" in key_combo:
                parts = [p.strip().lower() for p in key_combo.split('+')]
                 # Map common cross-platform modifiers
                pyautogui_keys = []
                for part in parts:
                     if part in ["command", "cmd"] and current_os == "Windows": pyautogui_keys.append("ctrl")
                     elif part == "command" and current_os == "Linux": pyautogui_keys.append("ctrl") # Usually Ctrl on Linux too
                     elif part in ["option", "opt", "alt"]: pyautogui_keys.append("alt")
                     elif part == "control": pyautogui_keys.append("ctrl")
                     else: pyautogui_keys.append(part) # Includes shift, letters, numbers, f-keys etc.
                logger.debug(f"[{platform_name}] Sending pyautogui hotkey: {pyautogui_keys}")
                pyautogui.hotkey(*pyautogui_keys)
            else:
                 # Single key press
                 key = key_combo.strip().lower()
                 # Map common keys if needed (pyautogui uses lowercase names)
                 key_map = {"return": "enter", "esc": "escape", "backspace": "backspace", "delete": "delete"}
                 pyautogui_key = key_map.get(key, key)
                 logger.debug(f"[{platform_name}] Sending pyautogui press: {pyautogui_key}")
                 pyautogui.press(pyautogui_key)
        else:
             logger.error(f"[{platform_name}] Unsupported OS for sending keystrokes: {current_os}")

    except Exception as e:
        logger.error(f"[{platform_name}] Error sending keystroke '{key_combo}': {e}", exc_info=True)

def activate_window(title):
    """
    Activate a window by its title (or part of it).
    """
    if not title:
        logger.warning("activate_window called with empty title.")
        return
    try:
        logger.debug(f"Attempting to activate window containing title: '{title}'")
        current_os = platform.system()

        if current_os == "Darwin":
             # Try activating by finding a process containing the title
             script = f'''
             set targetTitle to "{title}"
             try
                 tell application "System Events"
                     set matchingProcesses to (processes whose name contains targetTitle or title contains targetTitle)
                     if (count of matchingProcesses) > 0 then
                         set targetProcess to item 1 of matchingProcesses
                         set frontmost of targetProcess to true
                         log "Activated process: " & name of targetProcess
                         return true -- Indicate success
                     else
                         log "No process found containing title: " & targetTitle
                         -- Fallback: Try activating app by name if title matches app name
                         try
                            tell application targetTitle to activate
                            log "Activated application by name: " & targetTitle
                            return true
                         on error errMsg number errNum
                             log "Fallback activation by name failed: " & errMsg
                             return false
                         end try
                     end if
                 end tell
             on error errMsg number errNum
                  log "Error activating window: " & errMsg
                  return false
             end try
             '''
             # Use capture_output=True to get logs from AppleScript
             result = subprocess.run(['osascript', '-e', script], check=False, capture_output=True, text=True)
             if result.returncode == 0 and "Activated" in result.stdout:
                  logger.debug(f"Successfully activated window/process containing '{title}'. Output: {result.stdout.strip()}")
             else:
                  logger.warning(f"Could not activate window/process containing '{title}'. Error: {result.stderr.strip()} Output: {result.stdout.strip()}")

        elif current_os == "Windows":
            if win32gui and win32con:
                try:
                    # Find window - potentially partial match needed? FindWindow is exact match.
                    # EnumWindows might be needed for partial match. Sticking to exact for now.
                    hwnd = win32gui.FindWindow(None, title)
                    if hwnd:
                        # Restore if minimized, then bring to front
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                        logger.debug(f"Activated window '{title}' on Windows (HWND: {hwnd})")
                    else:
                        logger.warning(f"Window '{title}' not found on Windows using exact match.")
                        # TODO: Implement EnumWindows fallback for partial title match if needed
                except Exception as e:
                     logger.error(f"Error activating window '{title}' on Windows: {e}")
            else:
                logger.warning("win32gui not available for window activation on Windows.")
        elif current_os == "Linux":
            try:
                # Use wmctrl or xdotool - prefer wmctrl as it's often more reliable
                # Activate by bringing window containing title to current desktop and raising
                cmd = ['wmctrl', '-a', title]
                result = subprocess.run(cmd, check=False, capture_output=True, text=True)
                if result.returncode == 0:
                     logger.debug(f"Activated window containing '{title}' on Linux using wmctrl.")
                else:
                     logger.warning(f"wmctrl activation failed (is wmctrl installed?). Error: {result.stderr.strip()}")
                     # Fallback to xdotool?
                     try:
                          cmd_xdo = ['xdotool', 'search', '--name', title, 'windowactivate', '%@']
                          result_xdo = subprocess.run(cmd_xdo, check=False, capture_output=True, text=True)
                          if result_xdo.returncode == 0:
                               logger.debug(f"Activated window containing '{title}' on Linux using xdotool.")
                          else:
                               logger.warning(f"xdotool activation also failed. Error: {result_xdo.stderr.strip()}")
                     except FileNotFoundError:
                          logger.warning("xdotool not found for Linux window activation fallback.")
            except FileNotFoundError:
                logger.warning("wmctrl not found. Cannot activate window on Linux.")
            except Exception as e:
                 logger.error(f"Error activating window '{title}' on Linux: {e}")
        else:
            logger.error(f"Unsupported OS for window activation: {current_os}")

    except Exception as e:
        logger.error(f"Error activating window with title '{title}': {e}", exc_info=True)

def send_keystroke_string(text, platform_name):
    """
    Send a string of text to the specified platform by typing it.
    Args:
        text: The text to send.
        platform_name: The target platform.
    """
    try:
        if args.no_send:
            logger.info(f"[{platform_name}] Sending text skipped (--no-send): {text[:50]}...")
            return

        logger.info(f"[{platform_name}] Sending text: {text[:50]}...")

        platform_state = get_platform_state(platform_name)
        if not platform_state:
            logger.error(f"[{platform_name}] Cannot send text, platform state not found.")
            return

        window_title = platform_state.get("window_title", platform_name)
        activate_window(window_title)
        time.sleep(0.5) # Crucial delay after activation before typing

        current_os = platform.system()

        if current_os == "Darwin":
             # Escape backslashes and double quotes for AppleScript `keystroke`
             escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
             script = f'tell application "System Events" to keystroke "{escaped_text}"'
             logger.debug(f"[{platform_name}] Running AppleScript for text: {script[:100]}...")
             subprocess.run(['osascript', '-e', script], check=False)
             # Send a final 'Return' keystroke after typing the text? Assumed yes based on prev logic.
             time.sleep(0.2)
             # Use key code 36 for Return
             subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 36'], check=False)
             logger.debug(f"[{platform_name}] Sent final Return key code after text.")

        elif current_os in ["Windows", "Linux"]:
            if not pyautogui:
                 logger.error(f"[{platform_name}] pyautogui not available, cannot send text on {current_os}")
                 return
            # pyautogui.write handles typing the string. Interval adds slight delay between chars.
            logger.debug(f"[{platform_name}] Sending text via pyautogui.write: {text[:50]}...")
            pyautogui.write(text, interval=0.01) # Small interval for reliability
            # Send final 'Enter' keystroke
            time.sleep(0.2)
            pyautogui.press('enter')
            logger.debug(f"[{platform_name}] Sent final Enter key press after text.")
        else:
            logger.error(f"[{platform_name}] Unsupported OS for sending text: {current_os}")

    except Exception as e:
        logger.error(f"[{platform_name}] Error sending text: {e}", exc_info=True)

# --- Watchdog Event Handler ---
class PlatformEventHandler(FileSystemEventHandler):
    """Handles file system events for a specific platform."""
    def __init__(self, platform_name):
        self.platform_name = platform_name
        logger.debug(f"Initialized event handler for platform: {self.platform_name}")

    def on_any_event(self, event):
        # Ignore directory events for simplicity, focus on file changes
        if event.is_directory:
            return

        src_path = event.src_path
        event_type = event.event_type # 'modified', 'created', 'deleted', 'moved'
        platform_state = get_platform_state(self.platform_name)
        platform_config = get_platform_config(self.platform_name)

        if not platform_state or not platform_config:
            logger.warning(f"[{self.platform_name}] State or config not found for event: {src_path}")
            return

        project_path = platform_state.get("project_path")
        if not project_path:
            logger.warning(f"[{self.platform_name}] Project path not found in state for event: {src_path}")
            return

        # Calculate relative path - ensure it's within the project path
        try:
            # Ensure src_path is absolute for relpath calculation if it isn't already
            abs_src_path = os.path.abspath(src_path)
            if not abs_src_path.startswith(os.path.abspath(project_path)):
                 logger.debug(f"[{self.platform_name}] Event path {abs_src_path} outside project path {project_path}")
                 return # Event is outside this platform's project directory
            rel_path = os.path.relpath(abs_src_path, project_path)
        except ValueError:
            logger.warning(f"[{self.platform_name}] Could not determine relative path for {src_path} against {project_path}")
            return

        # Check if the file should be ignored
        # TODO: Pass platform_name to should_ignore_file if ignores become platform-specific
        if should_ignore_file(abs_src_path, rel_path, project_path):
            logger.debug(f"[{self.platform_name}] Ignoring event for file: {rel_path}")
            return

        logger.info(f"[{self.platform_name}] File event {event_type}: {rel_path}")

        # Update last activity time for this platform
        current_time = time.time()
        platform_state["last_activity"] = current_time
        logger.debug(f"[{self.platform_name}] Updated last_activity to {current_time}")

        # Check vision conditions if file was modified or created
        if event_type in ['modified', 'created']:
            # TODO: Pass platform_name to check_vision_conditions
            vision_result = check_vision_conditions(abs_src_path, event_type, self.platform_name)
            if vision_result:
                question, keystrokes = vision_result
                logger.info(f"[{self.platform_name}] Vision analysis triggered for {rel_path}")
                logger.info(f"[{self.platform_name}] Vision Question: {question}") # Assuming question is just for logging/potential future use
                
                # Activate window before sending vision keystrokes
                window_title = platform_config.get("window_title", self.platform_name)
                logger.info(f"[{self.platform_name}] Activating window for vision keystrokes: {window_title}")
                activate_window(window_title)
                time.sleep(0.5) # Give time for activation

                logger.info(f"[{self.platform_name}] Sending vision result keystrokes...")
                for keystroke in keystrokes:
                     keys = keystroke.get("keys", "")
                     delay_ms = keystroke.get("delay_ms", 0)
                     if keys:
                         if delay_ms > 0:
                             time.sleep(delay_ms / 1000.0)
                         # Send keystroke needs platform context
                         send_keystroke(keys, self.platform_name)
                     else:
                          logger.warning(f"[{self.platform_name}] Vision keystroke entry missing 'keys': {keystroke}")

if __name__ == "__main__":
    run_watcher()
