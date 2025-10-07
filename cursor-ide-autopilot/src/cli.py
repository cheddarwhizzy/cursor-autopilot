#!/usr/bin/env python3
import argparse
import os
import sys
import yaml
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found, using defaults")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        sys.exit(1)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Cursor Autopilot - Automated IDE Assistant",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Project settings
    project_group = parser.add_argument_group("Project Settings")
    project_group.add_argument(
        "--project-path",
        type=str,
        help="Path to the project directory"
    )
    project_group.add_argument(
        "--no-project-check",
        action="store_true",
        help="Skip project directory existence check"
    )
    
    # Platform settings
    platform_group = parser.add_argument_group("Platform Settings")
    platform_group.add_argument(
        "--platform",
        type=str,
        choices=["cursor", "windsurf"],
        help="Specify active platform(s) (comma-separated, e.g., 'cursor,windsurf')"
    )
    platform_group.add_argument(
        "--no-kill-existing",
        action="store_true",
        help="Don't kill existing application instances"
    )
    
    # Timing settings
    timing_group = parser.add_argument_group("Timing Settings")
    timing_group.add_argument(
        "--inactivity-delay",
        type=int,
        help="Override inactivity delay in seconds"
    )
    timing_group.add_argument(
        "--poll-interval",
        type=int,
        help="Override file system polling interval in seconds"
    )
    
    # Message settings
    message_group = parser.add_argument_group("Message Settings")
    message_group.add_argument(
        "--send-message",
        action="store_true",
        default=None,
        help="Enable message sending"
    )
    message_group.add_argument(
        "--no-send-message",
        action="store_false",
        dest="send_message",
        help="Disable message sending"
    )
    message_group.add_argument(
        "--auto-mode",
        action="store_true",
        default=None,
        help="Enable automatic message sending"
    )
    message_group.add_argument(
        "--no-auto-mode",
        action="store_false",
        dest="auto_mode",
        help="Disable automatic message sending"
    )
    
    # Debug settings
    debug_group = parser.add_argument_group("Debug Settings")
    debug_group.add_argument(
        "--debug",
        action="store_true",
        default=None,
        help="Enable debug mode"
    )
    debug_group.add_argument(
        "--log-file",
        type=str,
        help="Path to log file"
    )
    
    # Config file
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to config file"
    )
    config_group.add_argument(
        "--show-config",
        action="store_true",
        help="Show final configuration and exit"
    )
    
    return parser.parse_args()

def merge_configs(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """Merge command line arguments with config file settings."""
    merged = config.copy()
    
    # Initialize platforms if not present
    if "platforms" not in merged:
        merged["platforms"] = {}
    
    # Get list of platforms to update
    platforms = []
    if args.platform:
        platforms = [p.strip() for p in args.platform.split(",")]
    else:
        platforms = list(merged.get("platforms", {}).keys())
    
    # Update project path for each platform
    if args.project_path:
        for platform in platforms:
            if platform not in merged["platforms"]:
                merged["platforms"][platform] = {}
            merged["platforms"][platform]["project_path"] = args.project_path
    
    # Update platform list
    if args.platform:
        merged["platform"] = platforms
    elif "platform" not in merged:
        merged["platform"] = list(merged["platforms"].keys())
    
    # Update other settings
    if args.inactivity_delay is not None:
        merged["inactivity_delay"] = args.inactivity_delay
    if args.poll_interval is not None:
        merged["poll_interval"] = args.poll_interval
    if args.send_message is not None:
        merged["send_message"] = args.send_message
    if args.auto_mode is not None:
        merged["auto_mode"] = args.auto_mode
    if args.debug is not None:
        merged["debug"] = args.debug
    if args.no_kill_existing:
        merged["no_kill_existing"] = True
    if args.no_project_check:
        merged["no_project_check"] = True
    if args.log_file:
        merged["log_file"] = args.log_file
    
    return merged

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate the merged configuration."""
    # Check required fields
    if "platform" not in config:
        logger.error("Missing required field: platform")
        return False
    
    # Validate platform(s)
    platforms = config["platform"] if isinstance(config["platform"], list) else [config["platform"]]
    valid_platforms = ["cursor", "windsurf"]
    for platform in platforms:
        if platform not in valid_platforms:
            logger.error(f"Invalid platform: {platform}")
            return False
    
    # Validate project paths
    if not config.get("no_project_check"):
        if "platforms" not in config:
            logger.error("No platform configurations found")
            return False
            
        for platform in platforms:
            if platform not in config["platforms"]:
                logger.error(f"No configuration found for platform: {platform}")
                return False
                
            platform_config = config["platforms"][platform]
            if "project_path" not in platform_config:
                logger.error(f"Project path not configured for platform: {platform}")
                return False
                
            project_path = platform_config["project_path"]
            if not os.path.isdir(project_path):
                logger.error(f"Project path does not exist for platform {platform}: {project_path}")
                return False
    
    return True

def main() -> int:
    """Main entry point for the CLI."""
    # Parse command line arguments
    args = parse_args()
    logger.debug(f"Parsed arguments: {args}")
    
    # Load config file
    config = load_config(args.config)
    logger.debug(f"Loaded config: {config}")
    
    # Merge with CLI args
    try:
        merged_config = merge_configs(config, args)
        logger.debug(f"Merged config: {merged_config}")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    # Validate configuration
    if not validate_config(merged_config):
        logger.error("Configuration validation failed")
        return 1
    
    # Set debug logging if enabled
    if merged_config.get("debug", False):
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Configure logging to file if specified
    if "log_file" in merged_config:
        file_handler = logging.FileHandler(merged_config["log_file"])
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)
    
    # Log final configuration
    logger.info("Using configuration:")
    for key, value in merged_config.items():
        if key not in ["api_key", "webhook_url"]:  # Skip sensitive fields
            logger.info(f"  {key}: {value}")
    
    # Show config and exit if requested
    if args.show_config:
        return 0
    
    # Get the first platform's project path
    if not merged_config.get("platform"):
        logger.error("No platform specified")
        return 1
        
    first_platform = merged_config["platform"][0]
    if first_platform not in merged_config.get("platforms", {}):
        logger.error(f"Platform {first_platform} not found in configuration")
        return 1
        
    platform_config = merged_config["platforms"][first_platform]
    if "project_path" not in platform_config:
        logger.error(f"Project path not configured for platform {first_platform}")
        return 1
        
    project_path = platform_config["project_path"]
    logger.debug(f"Using project path: {project_path}")
    
    # Set environment variables for run.sh
    os.environ["CURSOR_AUTOPILOT_PLATFORM"] = ",".join(merged_config["platform"])
    os.environ["CURSOR_AUTOPILOT_PROJECT_PATH"] = project_path
    os.environ["CURSOR_AUTOPILOT_INACTIVITY_DELAY"] = str(merged_config.get("inactivity_delay", 120))
    os.environ["CURSOR_AUTOPILOT_DEBUG"] = "true" if merged_config.get("debug", False) else "false"
    
    logger.debug("Environment variables set:")
    logger.debug(f"  CURSOR_AUTOPILOT_PLATFORM: {os.environ['CURSOR_AUTOPILOT_PLATFORM']}")
    logger.debug(f"  CURSOR_AUTOPILOT_PROJECT_PATH: {os.environ['CURSOR_AUTOPILOT_PROJECT_PATH']}")
    logger.debug(f"  CURSOR_AUTOPILOT_INACTIVITY_DELAY: {os.environ['CURSOR_AUTOPILOT_INACTIVITY_DELAY']}")
    logger.debug(f"  CURSOR_AUTOPILOT_DEBUG: {os.environ['CURSOR_AUTOPILOT_DEBUG']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 