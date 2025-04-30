import yaml
import os

STATE_FILE = ".cursor_mode"

# Set initial mode from environment if state file does not exist
def get_mode():
    if not os.path.exists(STATE_FILE):
        auto_env = os.environ.get("CURSOR_AUTOPILOT_AUTO_MODE", "0")
        return "auto" if auto_env == "1" else "code"
    return open(STATE_FILE).read().strip()

def set_mode(mode):
    with open(STATE_FILE, "w") as f:
        f.write(mode)

def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Could not read config: {e}")
        return {}
