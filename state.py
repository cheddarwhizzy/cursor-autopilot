import os

STATE_FILE = ".cursor_mode"

# Set initial mode from environment if state file does not exist
def get_mode():
    if not os.path.exists(STATE_FILE):
        auto_env = os.environ.get("CURSOR_AUTOPILOT_AUTO", "0")
        return "auto" if auto_env == "1" else "code"
    return open(STATE_FILE).read().strip()

def set_mode(mode):
    with open(STATE_FILE, "w") as f:
        f.write(mode)
