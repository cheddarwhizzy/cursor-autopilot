# Configuration Guide

All major settings are controlled via `config.json` in the project root.

## Example `config.json`

```json
{
  "project_path": "~/cheddar/mushattention/mushattention",
  "task_readme_path": "src/notifications/README.md",
  "important_llm_docs_path": "docs/structure/*.md",
  "initial_delay": 10,
  "send_message": true,
  "platform": "cursor",
  "use_vision_api": false
}
```

## Configuration Options

| Option                  | Type    | Description                                                                                 |
|-------------------------|---------|---------------------------------------------------------------------------------------------|
| `project_path`          | string  | Path to the project directory to watch and open with the editor.                            |
| `task_readme_path`      | string  | Path to the README file that contains your feature/task list for tracking completion.        |
| `important_llm_docs_path` | string | Glob path to important documentation files to provide to the LLM for additional context.     |
| `initial_delay`         | number  | Initial delay (in seconds) before starting automation (default: 10).                        |
| `send_message`          | boolean | Whether to send the initial prompt automatically after launching (default: true).            |
| `platform`              | string  | Editor automation target. Use `cursor` (default) or `windsurf`.                             |
| `use_vision_api`        | boolean | Whether to use the Vision API for chat window detection (default: false).                   |

See [SETUP.md](./SETUP.md) for how to use these options in practice.
