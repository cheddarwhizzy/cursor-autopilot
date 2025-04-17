from flask import Flask, request
from state import set_mode, get_mode
from actions.send_to_cursor import send_prompt
from actions.screenshot import capture_chat_screenshot

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

    elif text.strip().startswith("send "):
        prompt = text.replace("send ", "", 1)
        send_prompt(prompt)
        return f"Sent to Cursor: {prompt}"

    elif text.strip() == "screenshot":
        file = capture_chat_screenshot()
        return f"Screenshot saved: {file}"

    elif text.strip() == "status":
        return f"Mode: {get_mode()}"

    return "Unknown command."
