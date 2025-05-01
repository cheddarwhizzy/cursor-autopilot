import logging
import os

# ANSI color codes
COLORS = {
    'ensure_chat_window': '\033[36m',  # Cyan
    'kill_cursor': '\033[31m',         # Red
    'launch_platform': '\033[32m',     # Green
    'send_to_cursor': '\033[33m',      # Yellow
    'watcher': '\033[35m',             # Magenta
    'notice': '\033[34m',              # Blue
    'warning': '\033[93m',             # Light Yellow
    'error': '\033[91m',               # Light Red
    'debug': '\033[90m',               # Gray
    'info': '\033[37m',                # White
    'reset': '\033[0m'                 # Reset
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # Get the base logger name (first part before any dots)
        base_logger = record.name.split('.')[0]
        
        # Check if message contains a bracketed prefix
        message = record.msg
        if isinstance(message, str) and message.startswith('[') and ']' in message:
            prefix = message[1:message.index(']')]
            if prefix in COLORS:
                # Apply color to the bracketed prefix
                record.msg = f"{COLORS[prefix]}[{prefix}]{COLORS['reset']}{message[message.index(']')+1:]}"
            else:
                # Apply color based on logger name
                color = COLORS.get(base_logger, COLORS['info'])
                record.msg = f"{color}{message}{COLORS['reset']}"
        else:
            # Apply color based on logger name
            color = COLORS.get(base_logger, COLORS['info'])
            record.msg = f"{color}{message}{COLORS['reset']}"
        
        return super().format(record)

def setup_colored_logging(debug=False):
    # Create a handler that outputs to stdout
    handler = logging.StreamHandler()
    
    # Create formatter with timestamp and level
    formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set the formatter
    handler.setFormatter(formatter)
    
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Remove any existing handlers
    root_logger.handlers = []
    
    # Add our handler
    root_logger.addHandler(handler)
    
    # Set the logging level
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Return the root logger
    return root_logger 