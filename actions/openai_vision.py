import os
import openai
import base64

def is_chat_window_open(screenshot_path):
    """
    Uses OpenAI GPT-4.1-mini to check if the screenshot shows a chat window.
    Returns True if a chat window is detected, False otherwise.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found in environment. Skipping vision check.")
        print("Note: The chat window should be closed when Cursor initially opens.")
        print("Will wait for the configured delay before proceeding.")
        return False
        
    try:
        # Read and encode image
        with open(screenshot_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        openai.api_key = api_key
        
        response = openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Does this screenshot show a Cursor chat window on the right side of the window? Answer with just 'yes' or 'no'."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=10
        )
        
        answer = response.choices[0].message.content.lower().strip()
        print(f"Vision API response: {answer}")
        return answer == "yes"
        
    except Exception as e:
        print(f"Error checking chat window: {e}")
        print("Note: The chat window should be closed when Cursor initially opens.")
        print("Will wait for the configured delay before proceeding.")
        return False
