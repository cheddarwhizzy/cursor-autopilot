# Quick Start Guide - Cursor Agent Iteration System

Get up and running with the Cursor Agent Iteration System in under 5 minutes.

## 🚀 Installation (30 seconds)

```bash
# One-liner installation
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/install-curl.sh | bash
```

## ⚡ Quick Start (2 minutes)

```bash
# 1. Initialize the system
cursor-iter iterate-init

# 2. Start working on tasks
cursor-iter iterate
```

## 📋 Essential Commands

| Command | What it does | Example |
|---------|--------------|---------|
| `cursor-iter iterate-init` | Sets up the iteration system | `cursor-iter iterate-init` |
| `cursor-iter iterate` | Runs the next task | `cursor-iter iterate --max-in-progress 10` |
| `cursor-iter iterate-loop` | Runs until all tasks complete | `cursor-iter iterate-loop --max-in-progress 10` |
| `cursor-iter add-feature` | Adds new features/tasks | `cursor-iter add-feature --prompt "Add authentication tasks"` |
| `cursor-iter task-status` | Shows current task status | `cursor-iter task-status` |

**Key Features:**
- **Task Continuation**: In-progress tasks automatically continue until completed
- **Automatic Retry**: Failed or incomplete tasks are retried automatically
- **Concurrency Control**: Use `--max-in-progress` to limit concurrent tasks (default: 10)

## 🎯 Common Use Cases

### Daily Development
```bash
# Start your day with
cursor-iter iterate

# Add tasks as they come up
cursor-iter add-feature --prompt "Add task for fixing the login bug"
```

### Feature Development
```bash
# Add comprehensive feature tasks
cursor-iter add-feature --prompt "Add tasks for implementing user dashboard: API endpoints, frontend components, authentication, and testing"

# Work on the feature
cursor-iter iterate
```

### Code Quality
```bash
# Focus on quality improvements
cursor-iter iterate
```

## 🔧 Troubleshooting

### cursor-agent not found?
```bash
curl https://cursor.com/install -fsS | bash
export PATH="$HOME/.local/bin:$PATH"
```

### Need to start over?
```bash
cursor-iter iterate-init
```

### Quality gates failing?
```bash
cursor-iter iterate
```

## 📚 Next Steps

1. **Read the full documentation**: `CURSOR_ITERATION_README.md`
2. **See examples**: `EXAMPLES.md`
3. **Customize for your needs**: Use `cursor-iter add-feature` to add your specific tasks

---

**That's it!** You're now ready to use the Cursor Agent Iteration System. The system will automatically detect your repository structure and create relevant tasks for you to work on.
