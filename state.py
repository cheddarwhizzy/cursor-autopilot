import os

STATE_FILE = ".cursor_mode"

def get_mode():
    if not os.path.exists(STATE_FILE):
        return "auto"
    return open(STATE_FILE).read().strip()

def set_mode(mode):
    with open(STATE_FILE, "w") as f:
        f.write(mode)
