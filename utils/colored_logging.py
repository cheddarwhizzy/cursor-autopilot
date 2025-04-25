import logging
import json
import time
from datetime import datetime

# ANSI color codes
COLORS = {
    'ensure_chat_window': '\033[36m',  # Cyan
    'kill_cursor': '\033[31m',         # Red
    'launch_platform': '\033[32m',     # Green
    'notice': '\033[94m',              # Blue
    'screenshot': '\033[35m',          # Purple
    'send_to_cursor': '\033[33m',      # Yellow
    'slack_bot': '\033[36m',           # Cyan
    'watcher': '\033[32m',             # Green
    'RESET': '\033[0m'                 # Reset
}

class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', use_json=False):
        super().__init__(fmt, datefmt, style)
        self.use_json = use_json

    def format(self, record):
        if self.use_json:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            if record.exc_info:
                log_entry['exception'] = self.formatException(record.exc_info)
            return json.dumps(log_entry)
        else:
            # Get the color for this logger
            color = COLORS.get(record.name, '')
            reset = COLORS['RESET']
            
            # Format the message with color
            record.msg = f"{color}{record.msg}{reset}"
            
            return super().format(record)

def setup_colored_logging(debug=False, use_json=False):
    """Set up colored logging for the application."""
    # Create a handler that outputs to stdout
    handler = logging.StreamHandler()
    
    # Set the formatter
    if use_json:
        formatter = ColoredFormatter(use_json=True)
    else:
        formatter = ColoredFormatter(
            fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    root_logger.addHandler(handler)
    
    # Remove any existing handlers to avoid duplicate output
    for h in root_logger.handlers[:]:
        if h is not handler:
            root_logger.removeHandler(h) 