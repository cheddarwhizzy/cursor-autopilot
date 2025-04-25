import os
import openai
import logging
from utils.colored_logging import setup_colored_logging

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
