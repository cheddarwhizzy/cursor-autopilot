# Cursor Agent Iteration System

A self-managing engineering loop for any repository type using Cursor Agent CLI. This system automatically detects your technology stack (Python, TypeScript, Go, Rust, Java, Infrastructure, etc.), creates tailored tasks, and runs appropriate quality gates.

## 🚀 Installation

### One-liner (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/cursor-cli-headleess-agent/cursor-agent-iteration/install-curl.sh | bash
```

### Option 2: Manual Installation
```bash
# Clone or download this repository
git clone https://github.com/cheddarwhizzy/cursor-autopilot.git
cd cursor-autopilot/cursor-agent-iteration

# Copy files to your project
cp -r * /path/to/your/project/
cd /path/to/your/project

# Run installation
chmod +x install.sh
./install.sh
```

## 🎯 Quick Start

### 1. Initialize the System
```bash
make iterate-init
```

This will:
- Analyze your repository structure
- Detect all technologies (Python, TypeScript, Go, Rust, Java, Infrastructure, etc.)
- Generate `prompts/iterate.md` tailored to your repo
- Create an initial `tasks.md` with technology-specific tasks

### 2. Start Iterating
```bash
make iterate
```

This will:
- Read all control files
- Select the next unchecked task
- Implement, test, validate, and commit changes
- Update progress documentation

## 📋 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `make iterate-init` | Initialize the iteration system | `make iterate-init` |
| `make iterate` | Run the next task in backlog | `make iterate` |
| `make iterate-custom` | Run with custom prompt | `make iterate-custom PROMPT="Work on security tasks"` |
| `make tasks-update` | Update task list | `make tasks-update PROMPT="Add GraphQL API tasks"` |

## 📁 Generated Files

### During Bootstrap (curl command):
- `prompts/initialize-iteration-universal.md` - Universal initialization prompt
- `scripts/init-iterate.sh` - Initialization script
- `architecture.md` - System architecture documentation (initial)
- `progress.md` - Progress tracking (initial)
- `decisions.md` - Architectural Decision Records (initial)
- `test_plan.md` - Test coverage plans (initial)
- `qa_checklist.md` - Quality assurance checklist (initial)
- `CHANGELOG.md` - Conventional commits log (initial)
- `context.md` - Project context (if not existing)

### After `make iterate-init`:
- `prompts/iterate.md` - Tailored iteration prompt (auto-generated)
- `tasks.md` - Task backlog with acceptance criteria

| File | Purpose |
|------|---------|
| `prompts/iterate.md` | Recurring iteration prompt (auto-generated) |
| `tasks.md` | Task backlog with acceptance criteria |
| `architecture.md` | High-level system architecture |
| `progress.md` | Session summaries and completion evidence |
| `decisions.md` | Architectural Decision Records (ADRs) |
| `test_plan.md` | Test coverage plans and targets |
| `qa_checklist.md` | Quality assurance checklist |
| `CHANGELOG.md` | Conventional commits log |

## 🔧 Quality Gates

The system enforces quality gates based on detected technologies:

### Python Stack
- **Linting**: `ruff check .`
- **Formatting**: `black --check .`
- **Type Checking**: `mypy .` (strict mode)
- **Testing**: `pytest` with coverage reporting

### TypeScript/JavaScript Stack
- **Type Checking**: `tsc --noEmit` (strict mode)
- **Linting**: `eslint .`
- **Testing**: `jest` or `vitest`
- **Runtime Validation**: `zod` schemas at API boundaries

### Go Stack
- **Linting**: `golangci-lint`
- **Formatting**: `gofmt`
- **Type Checking**: `go vet`
- **Testing**: `go test -race -cover`

### Rust Stack
- **Linting**: `cargo clippy`
- **Formatting**: `cargo fmt`
- **Security**: `cargo audit`
- **Testing**: `cargo test`

### Java Stack
- **Linting**: `mvn spotbugs:check`, `mvn checkstyle:check`, `mvn pmd:check`
- **Testing**: `mvn test`
- **Dependencies**: `mvn dependency:analyze`

### Infrastructure Stack
- **Terraform**: `terraform validate`, `terraform plan`
- **Ansible**: `ansible-lint`
- **Docker**: `dockerfile-lint`
- **Kubernetes**: `kubectl apply --dry-run`

### Security
- **Client/Server Boundary**: Ensures secrets never reach client bundles
- **Environment Variables**: Only `NEXT_PUBLIC_*` allowed in client code

## 🎯 How It Works

1. **Repository Analysis**: Detects languages, frameworks, and structure
2. **Task Generation**: Creates realistic, repo-specific tasks
3. **Iteration Loop**: Runs the engineering cycle:
   - Plan → Implement → Test → Validate → Document → Commit
4. **Progress Tracking**: Updates control files with evidence and decisions

## 📚 Advanced Usage

### Model Selection
```bash
# Use specific model for initialization
MODEL="gpt-4o" make iterate-init

# Use specific model for iteration
MODEL="gpt-4o" make iterate
```

### Custom Prompts
```bash
# Work on specific task types
make iterate-custom PROMPT="Find and implement the next database-related task"

# Focus on specific components
make iterate-custom PROMPT="Work on the next API endpoint task"
```

### Task Management
```bash
# Add new tasks
make tasks-update PROMPT="Add tasks for implementing user authentication with OAuth2"

# Refine existing tasks
make tasks-update PROMPT="Update the logging task to include structured logging with correlation IDs"
```

## 🚨 Troubleshooting

### Common Issues

**1. cursor-agent not found**
```bash
# Install cursor-agent
curl https://cursor.com/install -fsS | bash
export PATH="$HOME/.local/bin:$PATH"
```

**2. Tasks.md not found**
```bash
make iterate-init
```

**3. Quality gates failing**
```bash
make iterate-custom PROMPT="Diagnose why the Python quality gates are failing. Check mypy, ruff, black, and pytest outputs."
```

**4. Control files out of sync**
```bash
# Reset and regenerate
rm -f architecture.md progress.md decisions.md test_plan.md qa_checklist.md CHANGELOG.md
make iterate  # Will recreate them
```

### Getting Help
```bash
# Check what the system detected
make iterate-custom PROMPT="Analyze the current repository structure and explain what was detected"

# Get task recommendations
make iterate-custom PROMPT="Review the current tasks.md and suggest improvements or additional tasks"
```

## 📈 Best Practices

### Task Management
1. **Be Specific**: Use detailed acceptance criteria and expected files
2. **Prioritize**: Order tasks by business value and dependencies
3. **Test-Driven**: Include test requirements in every task
4. **Incremental**: Break large tasks into smaller, manageable pieces

### Iteration Strategy
1. **Regular Runs**: Use `make iterate` daily for steady progress
2. **Quality First**: Never skip quality gates
3. **Document Everything**: Let the system update control files automatically
4. **Review Progress**: Check `progress.md` regularly for insights

### Repository Maintenance
1. **Update Tasks**: Use natural language to add/modify tasks as requirements change
2. **Regenerate When Needed**: Re-run `make iterate-init` if repository structure changes significantly
3. **Keep Control Files**: Don't manually edit control files; let the system manage them
4. **Monitor Quality**: Use the quality gates to maintain code standards

## 🎯 Success Metrics

The system tracks:
- ✅ **Task Completion Rate**: Tasks completed vs. total tasks
- ✅ **Quality Gate Pass Rate**: Successful runs vs. total iterations
- ✅ **Test Coverage**: Automated coverage reporting
- ✅ **Documentation Coverage**: Control files completeness
- ✅ **Commit Quality**: Conventional commits adherence

## 🔄 Example Workflow

```bash
# 1. Install the system
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/cursor-cli-headleess-agent/cursor-agent-iteration/install-curl.sh | bash

# 2. Initialize for your repository
make iterate-init

# 3. Start working on tasks
make iterate

# 4. Add new tasks as needed
make tasks-update PROMPT="Add tasks for implementing real-time notifications with WebSockets"

# 5. Continue iterating
make iterate
```

## 🤝 Contributing

This system is designed to be easily extensible. To contribute:

1. Fork the repository
2. Make your changes to the `cursor-agent-iteration/` folder
3. Test with different repository types
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Ready to start?** Run the one-liner installer and begin the engineering iteration loop!

```bash
curl -fsSL https://raw.githubusercontent.com/your-repo/cursor-autopilot/main/cursor-agent-iteration/install-curl.sh | bash
```
