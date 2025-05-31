#!/usr/bin/env python3
import os
import logging
import fnmatch
import hashlib
from typing import Dict, List, Tuple, Set, Any

logger = logging.getLogger('watcher.file_filters')

class FileFilter:
    """
    Class to handle file filtering based on gitignore patterns and exclusion rules
    """
    def __init__(self, exclude_dirs: Set[str], exclude_files: Set[str], gitignore_patterns: Set[str]):
        self.exclude_dirs = exclude_dirs
        self.exclude_files = exclude_files
        self.gitignore_patterns = gitignore_patterns
        self.file_mtimes = {}  # For tracking file modifications
    
    def should_ignore_file(self, file_path: str, rel_path: str, platform_path: str) -> bool:
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
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in file_path.split(os.sep):
                return True
        
        # Skip excluded file types
        for pattern in self.exclude_files:
            if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
        
        # Skip gitignore patterns
        for pattern in self.gitignore_patterns:
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
    
    def hash_folder_state(self, platform_paths: Dict[str, str]) -> Tuple[str, List[Tuple[str, str]], int]:
        """
        Scan directory for changes and return:
        - A hash representing the current state
        - List of files that changed since last scan
        - Total number of files being watched
        
        Args:
            platform_paths: Dict mapping platform names to their project paths
            
        Returns:
            Tuple containing:
                - hash: A hash string representing the current state
                - changed_files: List of (platform, rel_path) tuples for changed files
                - total_files: Total number of files being watched
        """
        sha = hashlib.sha256()
        changed_files = []
        total_files = 0
        watched_files = []
        
        if not platform_paths:
            logger.error("No valid platform paths found")
            return None, [], 0
        
        # Walk through each platform's directory
        for platform, watch_path in platform_paths.items():
            for root, dirs, files in os.walk(watch_path):
                # Filter out excluded directories in-place to prevent walking them
                dirs[:] = [d for d in dirs if d not in self.exclude_dirs and not any(fnmatch.fnmatch(d, pat) for pat in self.gitignore_patterns)]
                
                # Process files
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, watch_path)
                    
                    # Skip ignored files
                    if self.should_ignore_file(file_path, rel_path, watch_path):
                        continue
                    
                    # Get file stats
                    try:
                        stat = os.stat(file_path)
                        mtime = stat.st_mtime
                        size = stat.st_size
                        
                        # Update hash
                        sha.update(f"{rel_path}:{mtime}:{size}".encode())
                        
                        # Check if file changed
                        if rel_path in self.file_mtimes:
                            if self.file_mtimes[rel_path] != mtime:
                                changed_files.append((platform, rel_path))
                        else:
                            # Only log new files if we're not on first run
                            if self.file_mtimes:
                                logger.debug(f"New file: {rel_path}")
                            changed_files.append((platform, rel_path))
                        
                        # Update mtime cache
                        self.file_mtimes[rel_path] = mtime
                        watched_files.append((platform, rel_path))
                        total_files += 1
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
        
        # Calculate final hash
        current_hash = sha.hexdigest()
        
        # Return results
        return current_hash, changed_files, total_files 