import os
import json
import logging
from utils.colored_logging import setup_colored_logging

# Configure logging
setup_colored_logging(debug=os.environ.get("CURSOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('generate_initial_prompt')

# Constants
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
INITIAL_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "initial_prompt.txt")
INITIAL_PROMPT_SENT_PATH = os.path.join(os.path.dirname(__file__), ".initial_prompt_sent")

# Default prompts
DEFAULT_INITIAL_PROMPT = '''You are working in a pre-existing TypeScript application. 
Before implementing any feature, always reference and update!!.

Before implementing any feature:
- Carefully review all relevant documentation in {additional_context_path} to understand the existing architecture, components, and file responsibilities.
- Use existing files and components whenever possible; only create new files if no suitable file exists - See repomix-output.xml if it exists.
- Keep each file under 600–1000 lines if possible. If a file grows too large, refactor by using subdirectories and splitting logic into separate, well-named files.

It contains documentation on existing components, API routes, utility files, and their responsibilities. 
Do not create a file if it already exists — search  first.

Use the {task_file_path} as your task list. Implement each feature one by one, and after each one:
- Update {task_file_path} to reflect any new files or components.
- Write tests for the feature.
- Test it end-to-end.
- Mark the feature as completed inside {task_file_path}.

If a file doesn't exist, document it before creating it.

Rerun repomix command to update the repomix-output.xml file after each feature. If the command isn't stalled, fail gracefully.
'''

DEFAULT_CONTINUATION_PROMPT = '''Continue working on the tasks in {task_file_path}. Remember to reference the documentation in {additional_context_path} as needed. Maintain the same development practices of updating documentation, writing tests, and marking completed features.'''

def get_config():
    """Get the configuration from config.json."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Config file not found at {CONFIG_PATH}")
        return {}

def read_prompt_from_file(file_path):
    """Read a prompt from a file if it exists."""
    if not file_path:
        return None
    
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except Exception as e:
        logger.warning(f"Could not read prompt file {file_path}: {e}")
        return None

def generate_prompt():
    """Generate the appropriate prompt based on whether initial prompt was sent."""
    config = get_config()
    
    task_file_path = config.get("task_file_path", "tasks.md")
    additional_context_path = config.get("additional_context_path", "context.md")
    
    # Check if initial prompt was sent
    is_new_chat = not os.path.exists(INITIAL_PROMPT_SENT_PATH)
    
    if is_new_chat:
        logger.info("Initial prompt has not been sent yet")
        # Try to read custom initial prompt from file
        custom_initial_prompt = read_prompt_from_file(config.get("initial_prompt_file_path"))
        prompt_template = custom_initial_prompt if custom_initial_prompt else DEFAULT_INITIAL_PROMPT
        logger.info("Using custom initial prompt" if custom_initial_prompt else "Using default initial prompt")
    else:
        logger.info("Initial prompt was already sent")
        # Try to read custom continuation prompt from file
        custom_continuation_prompt = read_prompt_from_file(config.get("continuation_prompt_file_path"))
        prompt_template = custom_continuation_prompt if custom_continuation_prompt else DEFAULT_CONTINUATION_PROMPT
        logger.info("Using custom continuation prompt" if custom_continuation_prompt else "Using default continuation prompt")
    
    prompt = prompt_template.format(task_file_path=task_file_path, additional_context_path=additional_context_path)
    
    # Write prompt to file
    with open(INITIAL_PROMPT_PATH, "w") as f:
        f.write(prompt)
    
    logger.info(f"Wrote {'initial' if is_new_chat else 'continuation'} prompt to {INITIAL_PROMPT_PATH}")
    
    # Create marker file if this is a new chat
    if is_new_chat:
        with open(INITIAL_PROMPT_SENT_PATH, "w") as f:
            f.write("This file indicates that the initial prompt has been sent.")
        logger.info("Created .initial_prompt_sent marker file")
    
    return prompt

if __name__ == "__main__":
    generate_prompt()
