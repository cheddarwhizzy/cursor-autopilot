import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
INITIAL_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "initial_prompt.txt")
INITIAL_PROMPT_SENT_PATH = os.path.join(os.path.dirname(__file__), ".initial_prompt_sent")

INITIAL_PROMPT = '''You are working in a pre-existing TypeScript application. 
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

CONTINUATION_PROMPT = '''Continue working on the tasks in {task_file_path}. Remember to reference the documentation in {additional_context_path} as needed. Maintain the same development practices of updating documentation, writing tests, and marking completed features.'''

def main():
    if not os.path.exists(CONFIG_PATH):
        print(f"Config file not found at {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    task_file_path = config.get("task_file_path", "tasks.md")
    additional_context_path = config.get("additional_context_path", "context.md")
    
    # Check if initial prompt has already been sent
    is_new_chat = not os.path.exists(INITIAL_PROMPT_SENT_PATH)
    if is_new_chat:
        print("📝 Initial prompt has not been sent yet, using INITIAL_PROMPT")
    else:
        print("📝 Initial prompt was already sent, using CONTINUATION_PROMPT")

    prompt_template = INITIAL_PROMPT if is_new_chat else CONTINUATION_PROMPT
    prompt = prompt_template.format(task_file_path=task_file_path, additional_context_path=additional_context_path)

    with open(INITIAL_PROMPT_PATH, "w") as f:
        f.write(prompt)
    print(f"📝 Wrote {'initial' if is_new_chat else 'continuation'} prompt to {INITIAL_PROMPT_PATH}")

    # If this was an initial prompt, create the marker file
    if is_new_chat:
        with open(INITIAL_PROMPT_SENT_PATH, "w") as f:
            f.write("This file indicates that the initial prompt has been sent.")
        print("📝 Created .initial_prompt_sent marker file")

if __name__ == "__main__":
    main()
