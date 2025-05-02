import os
import openai
import logging
import time
import fnmatch
from src.utils.colored_logging import setup_colored_logging

# Configure logging
setup_colored_logging(debug=os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('openai_vision')

def is_chat_window_open(screenshot_path):
    """
    Uses OpenAI Vision API to check if the chat window is open in the screenshot.
    Returns True if chat window is open, False if closed.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not found in environment. Skipping vision check.")
        logger.info("Note: The chat window should be closed when Cursor initially opens.")
        logger.info("Will wait for the configured delay before proceeding.")
        return False
    
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        
        with open(screenshot_path, "rb") as image_file:
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Is the chat window open in this screenshot? Answer with just 'yes' or 'no'."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_file.read().hex()}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.lower().strip()
            logger.debug(f"Vision API response: {answer}")
            return answer == "yes"
            
    except Exception as e:
        logger.error(f"Error checking chat window: {e}")
        logger.info("Note: The chat window should be closed when Cursor initially opens.")
        logger.info("Will wait for the configured delay before proceeding.")
        return False

def check_vision_conditions(file_path, event_type, platform_name):
    """
    Check if vision analysis should be triggered for a file change
    Returns tuple of (question, keystrokes) if conditions are met, None otherwise
    """
    try:
        # Skip if OpenAI API key is not set
        if not os.environ.get("OPENAI_API_KEY"):
            logger.debug(f"[{platform_name}] Skipping vision analysis - OPENAI_API_KEY not set in environment")
            return None
        
        # Get config from the ConfigManager
        # In a real implementation, this would be passed in or accessed through a singleton
        from src.config.loader import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.config
        
        if not config:
            logger.warning(f"[{platform_name}] Skipping vision analysis - Config not loaded")
            return None
            
        # Get platform-specific configuration and options
        platform_config = config_manager.get_platform_config(platform_name)
        options = platform_config.get("options", {})
        vision_options = config.get("openai", {}).get("vision", {})  # Global vision config
            
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
            action_trigger = condition.get("action")  # e.g., "save" (maps to modify/create)

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
                break  # Use the first matching condition

        if not condition_met:
            logger.debug(f"[{platform_name}] No matching vision condition found for {file_path} and event {event_type}")
            return None
        
        # Get question and keystrokes from the matched condition
        question = condition_met.get("question")
        success_keystrokes = condition_met.get("success_keystrokes", [])
        # failure_keystrokes = condition_met.get("failure_keystrokes", [])

        if not question:
            logger.warning(f"[{platform_name}] Vision condition matched, but no 'question' defined: {condition_met}")
            return None

        # TODO: Implement actual vision call and result processing
        # For now, assume success and return success_keystrokes
        logger.info(f"[{platform_name}] Vision condition met. Question: '{question}'. Sending SUCCESS keystrokes.")
        if not success_keystrokes:
            logger.warning(f"[{platform_name}] Vision condition matched, but no 'success_keystrokes' defined: {condition_met}")
            return None
        
        return question, success_keystrokes  # Returning question for logging, keystrokes for action
        
    except Exception as e:
        logger.error(f"[{platform_name}] Error checking vision conditions: {e}", exc_info=True)
        return None
