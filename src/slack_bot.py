#!/usr/bin/env python3.13
from flask import Flask, request
from src.state import set_mode, get_mode
from src.actions.send_to_cursor import send_prompt
from src.actions.screenshot import capture_chat_screenshot
import logging

# Configure logging
logger = logging.getLogger('slack_bot')

app = Flask(__name__)

@app.route("/cursor", methods=["POST"])
def slack_command():
    text = request.form.get("text", "")
    user = request.form.get("user_name", "someone")

    if text.strip() == "code":
        set_mode("code")
        return f"Mode set to CODE — you're now in control, {user}!"

    elif text.strip() == "auto":
        set_mode("auto")
        return "Mode set to AUTO — Cursor will continue on its own."

    elif text.strip().startswith("send"):
        prompt = text.replace("send", "", 1).strip()
        try:
            send_prompt(prompt)
            return f"Sent to Cursor: {prompt}"
        except Exception as e:
            logger.error(f"Error sending prompt: {e}")
            return f"Error sending prompt: {e}"

    elif text.strip() == "screenshot":
        try:
            file = capture_chat_screenshot()
            return f"Screenshot saved: {file}"
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return f"Error taking screenshot: {e}"

    elif text.strip() == "status":
        return f"Mode: {get_mode()}"

    return "Unknown command."
