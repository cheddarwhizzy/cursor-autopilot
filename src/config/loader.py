#!/usr/bin/env python3
import os
import yaml
import logging
import fnmatch
from typing import Dict, List, Optional, Set

logger = logging.getLogger('watcher.config')

def find_config_file() -> str:
    """
    Try to find config file in parent directory first, then current directory
    Returns the path to the config file
    """
    root_config = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "config.yaml")
    src_config = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

    if os.path.exists(root_config):
        config_path = root_config
        logger.debug(f"Using root config file: {os.path.abspath(config_path)}")
    elif os.path.exists(src_config):
        config_path = src_config
        logger.debug(f"Using src config file: {os.path.abspath(config_path)}")
    else:
        config_path = root_config  # Default to root even if it doesn't exist
        logger.debug(f"No config file found, defaulting to: {os.path.abspath(config_path)}")
    
    return config_path

def load_gitignore_patterns(project_path: str) -> Set[str]:
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

class ConfigManager:
    """
    Class to manage configuration for the application
    """
    def __init__(self):
        self.config = {}
        self.config_path = find_config_file()
        self.exclude_dirs = {"node_modules", ".git", "dist", "__pycache__", ".idea", "venv", ".env"}
        self.exclude_files = {'*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.exe', '*.tmp', '*.log', '*.swp', '*.swo'}
        self.gitignore_patterns = set()
        self.use_gitignore = True  # Default to True for backward compatibility
        self.last_modified = 0

    def load_config(self, args) -> bool:
        """
        Load configuration from YAML file
        Returns True if successful
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self.config = yaml.safe_load(f)
                    self.last_modified = os.path.getmtime(self.config_path)

                    # Load gitignore patterns if enabled
                    self.use_gitignore = self.config.get("general", {}).get(
                        "use_gitignore", True
                    )
                    if self.use_gitignore:
                        self.gitignore_patterns = self._load_gitignore_patterns()
                        logger.debug(
                            f"Loaded {len(self.gitignore_patterns)} gitignore patterns"
                        )
                    else:
                        logger.debug("Gitignore patterns disabled")

                    return True
            else:
                logger.warning(f"Config file not found at {self.config_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False

    def _load_gitignore_patterns(self) -> Set[str]:
        """
        Load patterns from .gitignore file
        Returns set of patterns
        """
        patterns = set()
        gitignore_path = os.path.join(os.path.dirname(self.config_path), ".gitignore")

        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.add(line)
                logger.debug(f"Loaded {len(patterns)} patterns from {gitignore_path}")
            except Exception as e:
                logger.error(f"Error loading .gitignore: {e}")
        else:
            logger.debug(f"No .gitignore file found at {gitignore_path}")

        return patterns

    def check_config_changed(self) -> bool:
        """
        Check if config file has been modified
        Returns True if changed
        """
        if os.path.exists(self.config_path):
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self.last_modified:
                logger.debug("Config file has been modified")
                return True
        return False

    def get_platform_config(self, platform_name: str) -> Optional[Dict[str, any]]:
        """
        Get configuration for a specific platform
        """
        return self.config.get("platforms", {}).get(platform_name)

    def get_active_platforms(self, args) -> List[str]:
        """
        Determine which platforms should be active based on config and command line args
        """
        # Determine active platforms
        if args.platform:
            requested_platforms = [p.strip() for p in args.platform.split(',') if p.strip()]
            logger.info(f"Platform override from command line: {requested_platforms}")
            # Validate requested platforms against config
            valid_platforms = []
            invalid_platforms = []
            for p in requested_platforms:
                if p in self.config["platforms"]:
                    valid_platforms.append(p)
                else:
                    invalid_platforms.append(p)
            # Check for invalid platforms
            if invalid_platforms:
                logger.error(f"Invalid platform(s) specified via --platform: {invalid_platforms}. Valid platforms in config: {list(self.config['platforms'].keys())}")
                return []
            return valid_platforms
        else:
            # Initialize platforms - check general.active_platforms first
            if self.config.get("general", {}).get("active_platforms"):
                cfg_active_platforms = self.config["general"]["active_platforms"]
                logger.debug(f"Using active_platforms from general section: {cfg_active_platforms}")
                # Filter the list to only include platforms that exist in the config
                return [p for p in cfg_active_platforms if p in self.config["platforms"]]
            else:
                # Fallback to using all platforms defined
                logger.warning("general.active_platforms not set in config, activating ALL defined platforms.")
                return list(self.config["platforms"].keys())
