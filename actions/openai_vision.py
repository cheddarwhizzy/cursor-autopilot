import os
import openai

def is_chat_window_open(image_path, api_key=None):
    """
    Uses OpenAI Vision API to determine if the Cursor chat window is open in the screenshot.
    Returns: 'open', 'closed', or None if uncertain.
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env variable or pass as argument.")
    openai.api_key = api_key
    with open(image_path, "rb") as img:
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": "Is the Cursor chat window open in this screenshot? Reply only with 'open' or 'closed'."},
                    {"type": "image_url", "image_url": "attachment://cursor_window.png"}
                ]}
            ],
            files=[img]
        )
    result = response.choices[0].message.content.strip().lower()
    if "open" in result:
        return "open"
    elif "closed" in result:
        return "closed"
    else:
        return None
