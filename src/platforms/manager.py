#!/usr/bin/env python3
import os
import time
import logging
from typing import Dict, List, Optional, Any
from src.config.loader import load_gitignore_patterns

logger = logging.getLogger('watcher.platforms')

class PlatformManager:
    """
    Class to manage platform states and operations
    """
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.platform_names = []  # List of active platform names
        self.platform_states = {}  # Dict to hold state per platform
        self.last_global_prompt_time = 0.0  # Track time of the last prompt sent to any platform
    
    def initialize_platforms(self, args) -> bool:
        """
        Initialize platforms based on config and command line args
        Returns True if successful, False otherwise
        """
        try:
            # Get active platforms
            self.platform_names = self.config_manager.get_active_platforms(args)
            if not self.platform_names:
                logger.error("No valid platforms to initialize")
                return False
            
            logger.debug(f"Final active platforms: {self.platform_names}")
            
            # Initialize state for each active platform
            self.platform_states = {}
            all_project_paths = set()  # To load gitignore patterns later
            
            for platform_name in self.platform_names:
                logger.debug(f"Initializing state for platform: {platform_name}")
                platform_config = self.config_manager.get_platform_config(platform_name)
                if not platform_config:
                    logger.error(f"Configuration missing for active platform {platform_name}")
                    return False
                
                # Get project path - apply command line override if specified
                if args.project_path:
                    project_path = args.project_path
                    logger.info(f"Using project path override from command line for {platform_name}: {project_path}")
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
                    return False
                
                all_project_paths.add(project_path)
                
                # Get inactivity delay - apply command line override if specified
                if args.inactivity_delay:
                    inactivity_delay = args.inactivity_delay
                    logger.info(f"Using inactivity delay override from command line for {platform_name}: {inactivity_delay}")
                else:
                    # Use platform-specific delay, fallback to general, fallback to default
                    inactivity_delay = platform_config.get(
                        "inactivity_delay", 
                        self.config_manager.config.get("general", {}).get("inactivity_delay", 120)
                    )
                    logger.debug(f"Using inactivity delay for {platform_name}: {inactivity_delay}")
                
                # Populate state for this platform
                self.platform_states[platform_name] = {
                    "project_path": project_path,
                    "inactivity_delay": inactivity_delay,
                    "last_activity": time.time(),  # Initialize activity time
                    "last_prompt_time": 0.0,
                    "watch_handler": None,  # Placeholder for watchdog handler
                    "observer": None,  # Placeholder for watchdog observer
                    # Add other per-platform state vars as needed
                    "task_file_path": platform_config.get("task_file_path", "tasks.md"),
                    "continuation_prompt_file_path": platform_config.get("continuation_prompt_file_path", "continuation_prompt.txt"),
                    "initial_prompt_file_path": platform_config.get("initial_prompt_file_path", None),  # Optional
                    "window_title": platform_config.get("window_title", None)  # Important for activation
                }
                logger.debug(f"State for {platform_name}: {self.platform_states[platform_name]}")
            
            # Load gitignore patterns from first platform's path
            # A more robust solution might merge patterns or handle ignores per-path
            first_project_path = self.platform_states[self.platform_names[0]]["project_path"]
            logger.info(f"Loading gitignore patterns based on project path: {first_project_path}")
            self.config_manager.gitignore_patterns = load_gitignore_patterns(first_project_path)
            
            # Log combined configuration overview
            logger.info("Configuration loaded successfully for multiple platforms:")
            for platform_name in self.platform_names:
                state = self.platform_states[platform_name]
                logger.info(f"  Platform: {platform_name}")
                logger.info(f"    Project Path: {state['project_path']}")
                logger.info(f"    Inactivity Delay: {state['inactivity_delay']}s")
                logger.info(f"    Window Title: {state.get('window_title', 'N/A')}")
            
            logger.info(f"Loaded {len(self.config_manager.gitignore_patterns)} gitignore patterns (from {first_project_path})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing platforms: {e}", exc_info=True)
            return False
    
    def get_platform_state(self, platform_name: str) -> Dict:
        """
        Retrieve the dynamic state for a given platform name
        """
        if not self.platform_states:
            logger.warning("Accessing platform state before initialization")
            return {}
        return self.platform_states.get(platform_name, {})
    
    def update_activity(self, platform_name: str) -> None:
        """
        Update the last activity time for a platform
        """
        if platform_name in self.platform_states:
            self.platform_states[platform_name]["last_activity"] = time.time()
            logger.debug(f"Updated last_activity for {platform_name}")
    
    def update_prompt_time(self, platform_name: str) -> None:
        """
        Update the last prompt time for a platform and the global prompt time
        """
        current_time = time.time()
        if platform_name in self.platform_states:
            self.platform_states[platform_name]["last_prompt_time"] = current_time
            self.last_global_prompt_time = current_time
            logger.debug(f"Updated prompt times for {platform_name} and global")
    
    def get_inactive_platforms(self) -> List[Dict]:
        """
        Get a list of platforms that have been inactive for longer than their inactivity delay
        Returns a list of dicts with platform details
        """
        current_time = time.time()
        inactive_platforms = []
        
        for platform_name, state in self.platform_states.items():
            inactivity_delay = state.get("inactivity_delay", 120)
            last_activity = state.get("last_activity", current_time)
            elapsed_time = current_time - last_activity
            
            if elapsed_time > inactivity_delay:
                logger.debug(f"[{platform_name}] Inactivity detected (elapsed: {elapsed_time:.1f}s > delay: {inactivity_delay}s)")
                inactive_platforms.append({
                    "name": platform_name,
                    "last_activity": last_activity,
                    "state": state,
                    "config": self.config_manager.get_platform_config(platform_name)
                })
        
        return inactive_platforms
    
    def should_send_prompt(self, stagger_delay: int) -> Optional[Dict]:
        """
        Check if a prompt should be sent based on stagger delay and inactive platforms
        Returns platform to prompt if conditions are met, None otherwise
        """
        inactive_platforms = self.get_inactive_platforms()
        
        if not inactive_platforms:
            return None
        
        logger.info(f"Inactive platforms: {[p['name'] for p in inactive_platforms]}")
        
        # Check if stagger delay has passed since the last global prompt
        current_time = time.time()
        time_since_last_global_prompt = current_time - self.last_global_prompt_time
        
        if time_since_last_global_prompt >= stagger_delay:
            logger.info(f"Stagger delay ({stagger_delay}s) passed. Time since last prompt: {time_since_last_global_prompt:.1f}s")
            
            # Select the platform that has been inactive the longest
            inactive_platforms.sort(key=lambda p: p["last_activity"])
            platform_to_prompt = inactive_platforms[0]
            logger.info(f"Selected platform '{platform_to_prompt['name']}' for continuation prompt (inactive longest).")
            
            return platform_to_prompt
        else:
            logger.debug(f"Stagger delay ({stagger_delay}s) not yet passed. Time since last global prompt: {time_since_last_global_prompt:.1f}s. Waiting.")
            return None 