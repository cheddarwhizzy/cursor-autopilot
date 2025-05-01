import os
import json
import yaml
import logging
import time
from src.utils.colored_logging import setup_colored_logging

# Configure logging
setup_colored_logging(debug=os.environ.get("CURATOR_AUTOPILOT_DEBUG") == "true")
logger = logging.getLogger('generate_initial_prompt')

# Constants
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
INITIAL_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "initial_prompt.txt")
INITIAL_PROMPT_SENT_PATH = os.path.join(os.path.dirname(__file__), ".initial_prompt_sent")

DEFAULT_INITIAL_PROMPT = '''You are working in a pre-existing application. 
Before implementing any feature, always reference and update!!.

Before implementing any feature:
1. Architecture & Documentation:
   - Carefully review all relevant documentation in {additional_context_path}
   - Understand the existing architecture, components, and file responsibilities
   - Document any architectural decisions or trade-offs made

2. Code Organization:
   - Use existing files and components whenever possible
   - Only create new files if no suitable file exists (check repomix-output.xml)
   - Keep files under 600-1000 lines; refactor if needed
   - Follow the project's established patterns and conventions

3. Development Process:
   - Use {task_file_path} as your task list
   - Implement features one by one
   - After each feature:
     * Update {task_file_path} with new files/components
     * Write comprehensive tests (unit, integration, e2e)
     * Test the feature end-to-end
     * Mark the feature as completed
     * Update repomix-output.xml if available

4. Code Quality:
   - Write clean, maintainable code
   - Add appropriate comments and documentation
   - Follow TypeScript best practices
   - Handle edge cases and error conditions
   - Consider performance implications

5. Tools & Capabilities:
   - You have access to code search, file reading, and editing tools
   - You can run terminal commands when needed
   - You can analyze the codebase structure
   - You can read and write files
   - You can execute tests and verify functionality

Remember to:
- Think step by step before implementing
- Consider security implications
- Maintain backward compatibility
- Document any assumptions or limitations
- Ask for clarification if requirements are unclear
'''

DEFAULT_CONTINUATION_PROMPT = '''Continue working on the tasks in {task_file_path}. 

For each task:
1. Review the current state of the codebase
2. Check for any new context in {additional_context_path}
3. Implement the next logical step
4. Verify your changes work as expected
5. Update documentation and tests as needed

Maintain the same high standards of:
- Code quality and organization
- Testing and verification
- Documentation and comments
- Error handling and edge cases
- Performance considerations

If you encounter any blockers or need clarification, document them in the task file.'''

def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not read config: {e}")
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
