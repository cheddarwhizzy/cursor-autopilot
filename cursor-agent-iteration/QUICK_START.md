# Quick Start Guide - Cursor Agent Iteration System

Get up and running with the Cursor Agent Iteration System in under 5 minutes.

## 🚀 Installation (30 seconds)

```bash
# One-liner installation
curl -fsSL https://raw.githubusercontent.com/your-repo/cursor-autopilot/main/cursor-agent-iteration/install-curl.sh | bash
```

## ⚡ Quick Start (2 minutes)

```bash
# 1. Initialize the system
make iterate-init

# 2. Start working on tasks
make iterate
```

## 📋 Essential Commands

| Command | What it does | Example |
|---------|--------------|---------|
| `make iterate-init` | Sets up the iteration system | `make iterate-init` |
| `make iterate` | Runs the next task | `make iterate` |
| `make iterate-custom` | Runs with custom focus | `make iterate-custom PROMPT="Work on security tasks"` |
| `make tasks-update` | Adds new tasks | `make tasks-update PROMPT="Add authentication tasks"` |

## 🎯 Common Use Cases

### Daily Development
```bash
# Start your day with
make iterate

# Add tasks as they come up
make tasks-update PROMPT="Add task for fixing the login bug"
```

### Feature Development
```bash
# Add comprehensive feature tasks
make tasks-update PROMPT="Add tasks for implementing user dashboard: API endpoints, frontend components, authentication, and testing"

# Work on the feature
make iterate
```

### Code Quality
```bash
# Focus on quality improvements
make iterate-custom PROMPT="Work on the next code quality task - could be typing, testing, or refactoring"
```

## 🔧 Troubleshooting

### cursor-agent not found?
```bash
curl https://cursor.com/install -fsS | bash
export PATH="$HOME/.local/bin:$PATH"
```

### Need to start over?
```bash
make iterate-init
```

### Quality gates failing?
```bash
make iterate-custom PROMPT="Diagnose why quality gates are failing and fix the issues"
```

## 📚 Next Steps

1. **Read the full documentation**: `CURSOR_ITERATION_README.md`
2. **See examples**: `EXAMPLES.md`
3. **Customize for your needs**: Use `make tasks-update` to add your specific tasks

---

**That's it!** You're now ready to use the Cursor Agent Iteration System. The system will automatically detect your repository structure and create relevant tasks for you to work on.
