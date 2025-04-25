# Cursor Autopilot

An autonomous development assistant that automatically implements features by following a structured task list, using Cursor or Windsurf as its interface. It reads tasks from a task list, understands project context and documentation, and autonomously implements each feature one by one.

## TL;DR

1. Install dependencies: `pip install -r requirements.txt`
2. Configure `config.json`:
   - Set `project_path` to your project directory
   - Set `platform` to either "cursor" or "windsurf"
   - Optionally set `initial_prompt_file_path` and `continuation_prompt_file_path` for custom prompts
3. Create the following files in your project directory:
   - [`tasks.md`](./tasks.md): Your feature implementation list
   - [`docs.md`](./docs.md): Additional project documentation and links
   - [`context.md`](./context.md): Project documentation and architecture details
4. Run: `./run.sh --auto --debug`

> 💡 **Tip**: Use ChatGPT to help generate your `tasks.md`, `docs.md`, and `context.md` files. It can help structure your tasks and documentation based on your project's needs.

## Features

- Autonomous feature implementation following a structured task list
- Reads and understands project documentation and architecture
- Automatically detects code changes and progress
- Configurable inactivity delay before sending prompts
- Supports custom initial and continuation prompts via config.json
- Detailed logging with color-coded output
- Vision API integration for screenshots (optional)

## Configuration

The `config.json` file supports the following options:

```json
{
  "project_path": "/path/to/your/project",
  "task_file_path": "tasks.md",
  "additional_context_path": "context.md",
  "initial_delay": 10,
  "send_message": true,
  "platform": "cursor",
  "use_vision_api": false,
  "debug": true,
  "inactivity_delay": 120,
  "initial_prompt_file_path": "path/to/initial_prompt.txt",
  "continuation_prompt_file_path": "path/to/continuation_prompt.txt"
}
```

### Configuration Options

- `project_path`: Path to your project directory
- `task_file_path`: Path to your task list file (default: "tasks.md")
- `additional_context_path`: Path to your project documentation (default: "context.md")
- `initial_delay`: Delay in seconds before sending the first prompt
- `send_message`: Whether to send messages to Cursor/Windsurf
- `platform`: Either "cursor" or "windsurf"
- `use_vision_api`: Whether to use the Vision API for screenshots
- `debug`: Enable debug logging
- `inactivity_delay`: Delay in seconds of inactivity before sending a prompt
- `initial_prompt_file_path`: Path to a custom initial prompt file (optional)
- `continuation_prompt_file_path`: Path to a custom continuation prompt file (optional)

## Custom Prompts

You can customize both the initial and continuation prompts by creating your own prompt files and specifying their paths in `config.json`:

1. Create your custom prompt files:
   - `initial_prompt.txt`: For the first message in a new chat
   - `continuation_prompt.txt`: For follow-up messages

2. Add their paths to `config.json`:
   ```json
   {
     "initial_prompt_file_path": "path/to/initial_prompt.txt",
     "continuation_prompt_file_path": "path/to/continuation_prompt.txt"
   }
   ```

If these paths are not specified, the tool will use its default prompts.

## Usage

1. **Automatic Mode**:
   ```bash
   ./run.sh --auto
   ```
   This will:
   - Start the watcher
   - Send initial prompt if needed
   - Monitor for changes
   - Send prompts on inactivity

2. **Manual Mode**:
   ```bash
   ./run.sh
   ```
   This will:
   - Start the watcher
   - Wait for manual trigger
   - Send prompts when triggered

3. **Debug Mode**:
   ```bash
   ./run.sh --auto --debug
   ```
   This enables detailed logging.

## File Structure

- `tasks.md`: Your feature implementation list
- `context.md`: Project documentation and architecture details
- `docs.md`: Additional project documentation and links
- `initial_prompt.txt`: Generated initial prompt
- `.initial_prompt_sent`: Marker file indicating initial prompt was sent

## Logging

The tool provides detailed logging with color-coded output:
- Blue: Notice messages
- Green: Success messages
- Yellow: Warning messages
- Red: Error messages

Debug logging can be enabled via the `--debug` flag or by setting `debug: true` in `config.json`.

## License

MIT

---

## 📚 Documentation

- [Setup Guide](./docs/SETUP.md)
- [Configuration Options](./docs/CONFIGURATION.md)
- [Installation & Environment](./docs/INSTALLATION.md)
- [Slack Bot Usage](./docs/SLACK_BOT.md)
- [Automation & AppleScript](./docs/AUTOMATION.md)
