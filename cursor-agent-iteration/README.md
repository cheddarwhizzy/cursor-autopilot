# Cursor Agent Iteration System

A self-managing engineering loop for any repository type using Cursor Agent CLI. This system automatically detects your technology stack (Python, TypeScript, Go, Rust, Java, Infrastructure, etc.), creates tailored tasks, and runs appropriate quality gates.

## 🚀 Installation

### One-liner (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash
```

### Go Install (Latest)
```bash
go install github.com/cheddarwhizzy/cursor-autopilot/cursor-agent-iteration/cmd/cursor-iter@latest
```

### Manual Installation
```bash
# Clone or download this repository
git clone https://github.com/cheddarwhizzy/cursor-autopilot.git
cd cursor-autopilot/cursor-agent-iteration

# Build and install
go build -o cursor-iter ./cmd/cursor-iter
sudo mv cursor-iter /usr/local/bin/
```

## 🎯 Quick Start

**⚠️ Having issues?** See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common problems and solutions.

### 1. Initialize the System
```bash
cursor-iter iterate-init --model auto
```

This will:
- Analyze your repository structure
- Detect all technologies (Python, TypeScript, Go, Rust, Java, Infrastructure, etc.)
- Generate `prompts/iterate.md` tailored to your repo
- Create an initial `tasks.md` with technology-specific tasks

### 2. Start Iterating

For single task iteration:
```bash
cursor-iter iterate
```

For continuous iteration with safe concurrency:
```bash
cursor-iter iterate-loop --max-in-progress 3
```

**Recommended concurrency:**
- Low-resource machines: `--max-in-progress 2`
- Standard machines: `--max-in-progress 3-5`
- High-performance machines: `--max-in-progress 10`

This will:
- Read all control files
- Select the next unchecked task
- Implement, test, validate, and commit changes
- Update progress documentation

## 📋 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `cursor-iter` | Show all available commands and help | `cursor-iter` |
| `cursor-iter iterate-init` | Initialize the iteration system | `cursor-iter iterate-init --model auto` |
| `cursor-iter iterate-init --codex` | Initialize using Codex CLI | `cursor-iter iterate-init --codex --model gpt-5-codex` |
| `cursor-iter iterate` | Run the next task in backlog | `cursor-iter iterate --max-in-progress 10` |
| `cursor-iter iterate --codex` | Run iteration using Codex CLI | `cursor-iter iterate --codex` |
| `cursor-iter iterate-loop` | Run iterations until all tasks complete | `cursor-iter iterate-loop --max-in-progress 10` |
| `cursor-iter iterate-loop --codex` | Run iterations using Codex CLI | `cursor-iter iterate-loop --codex --max-in-progress 5` |
| `cursor-iter add-feature` | Add new feature/requirements | `cursor-iter add-feature` |
| `cursor-iter add-feature --codex` | Add feature using Codex CLI | `cursor-iter add-feature --codex` |
| `cursor-iter run-agent` | Send ad-hoc request to cursor-agent/codex | `cursor-iter run-agent --prompt "your request"` |
| `cursor-iter run-agent --codex` | Send ad-hoc request using Codex CLI | `cursor-iter run-agent --codex --prompt "your request"` |
| `cursor-iter archive-completed` | Archive completed tasks | `cursor-iter archive-completed` |
| `cursor-iter task-status` | Show current task status and progress | `cursor-iter task-status` |
| `cursor-iter validate-tasks` | Validate/fix tasks.md structure | `cursor-iter validate-tasks --fix` |
| `cursor-iter reset` | Remove all control files | `cursor-iter reset` |

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

### After `cursor-iter iterate-init`:
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

### Shell Scripts
- **Linting**: `shellcheck`, `bashate`
- **Testing**: `bats`, `shunit2`

### Security
- **Client/Server Boundary**: Ensures secrets never reach client bundles
- **Environment Variables**: Only `NEXT_PUBLIC_*` allowed in client code

## 🎯 How It Works

1. **Repository Analysis**: Detects languages, frameworks, and structure
2. **Task Generation**: Creates realistic, repo-specific tasks
3. **Quality Gates**: Enforces appropriate standards for each detected stack
4. **Iteration Loop**: Runs the engineering cycle:
   - Plan → Implement → Test → Validate → Document → Commit
5. **Progress Tracking**: Updates control files with evidence and decisions
6. **Completion Detection**: Automatically detects when all tasks are completed

## 🔄 Continuous Loop Mode

For fully automated development, use the continuous loop mode with **parallel execution**:

```bash
cursor-iter iterate-loop
```

This will:
- **Run up to 10 tasks in parallel** by default (configurable)
- Show real-time completion status for each task
- Automatically start new tasks as others complete
- Stop automatically when all tasks are done
- Update control files with completion status
- Provide safety limits to prevent infinite loops

### 🚀 Parallel Execution

The iterate-loop now supports **concurrent task execution**, allowing multiple cursor-agent processes to run simultaneously:

```bash
# Run up to 10 tasks in parallel (default)
cursor-iter iterate-loop

# Run up to 5 tasks in parallel
cursor-iter iterate-loop --max-in-progress 5

# Use with codex
cursor-iter iterate-loop --codex --max-in-progress 3
```

**Key Features:**
- ✅ **Parallel Processing**: Run multiple tasks concurrently for faster completion
- ✅ **Dynamic Scheduling**: Automatically starts new tasks as capacity becomes available
- ✅ **Real-time Monitoring**: See when each task starts and completes
- ✅ **Smart Resource Management**: Configurable concurrency limits
- ✅ **Race Condition Prevention**: Automatic 3-second staggering between task starts prevents config file conflicts
- ✅ **Automatic Retry**: Failed or incomplete tasks are automatically retried
- ✅ **Progress Tracking**: Live updates showing active tasks and completion status

**Example Output with Parallel Execution:**
```
[10:30:15] 🚀 Starting iterate-loop with parallel execution (max concurrent: 10)
[10:30:15] 📝 Starting new task: 'Add user authentication'
[10:30:15] 🚀 Starting cursor-agent for task: 'Add user authentication' (active: 1/10)
[10:30:18] 📝 Starting new task: 'Implement API rate limiting'
[10:30:18] 🚀 Starting cursor-agent for task: 'Implement API rate limiting' (active: 2/10)
[10:30:21] 📝 Starting new task: 'Add logging middleware'
[10:30:21] 🚀 Starting cursor-agent for task: 'Add logging middleware' (active: 3/10)
[10:35:42] ✅ cursor-agent completed for task 'Add user authentication' (duration: 5m27s)
[10:35:42] ✅ Task marked as completed: Add user authentication
[10:35:43] 📝 Starting new task: 'Add password reset functionality'
[10:35:43] 🚀 Starting cursor-agent for task: 'Add password reset functionality' (active: 3/10)
[10:38:15] ✅ cursor-agent completed for task 'Implement API rate limiting' (duration: 7m59s)
[10:38:15] ✅ Task marked as completed: Implement API rate limiting
[10:38:15] 📊 Progress: 2 completed, 8 in-progress, 15 pending (active: 2/10)
```

**Performance Benefits:**
- 🚀 **10x Faster**: Complete 10 tasks in parallel instead of sequentially
- ⚡ **Efficient Resource Usage**: Maximize CPU and API throughput
- 📊 **Better Visibility**: See all active tasks and their progress
- 🔄 **Continuous Flow**: New tasks start immediately when capacity is available

### Debug Mode & Comprehensive Logging

Enable detailed logging to track every step of task execution:

```bash
# Enable debug mode with --debug flag
cursor-iter iterate --debug
cursor-iter iterate-loop --debug
cursor-iter add-feature --debug

# Or use environment variable
DEBUG=1 cursor-iter iterate
```

**Debug logging includes:**
- 📖 File reads from `tasks.md` and `progress.md` (with byte counts)
- 🔍 Task selection and matching logic
- 📋 Task detail extraction from tasks.md
- 📝 Progress marking in progress.md
- 🤖 Cursor-agent process start/duration/completion
- 🔍 Status rechecking after cursor-agent completion
- 💡 Retry logic when tasks aren't complete

**Example debug output:**
```
[14:32:15] 📖 Reading tasks from: tasks.md
[14:32:15] ✅ Successfully read tasks.md (2543 bytes)
[14:32:15] 📖 Reading progress from: progress.md
[14:32:15] ✅ Successfully read progress.md (1234 bytes)
[14:32:15] 🔍 Checking for in-progress tasks...
[14:32:15] 🎯 Selected in-progress task to continue: 'Implement user authentication'
[14:32:15] 🚀 Sending task to cursor-agent: 'Implement user authentication'
[14:32:15] 🤖 Starting cursor-agent process...
[14:38:42] ✅ cursor-agent process completed successfully (duration: 6m27s)
[14:38:42] 🔍 Rechecking task status after cursor-agent completion...
[14:38:42] ⚠️ Task not yet complete - will retry on next iteration
```

For more details, see [docs/LOGGING.md](docs/LOGGING.md).

### Task Status Overview

Get detailed task status and progress:
```bash
cursor-iter task-status
```

This will show:
- Total number of tasks
- Number of completed tasks
- Number of in-progress tasks
- Number of pending tasks
- Currently working on
- Next pending task
- Completion status

## 🎯 Ad-hoc Agent Requests

Send ad-hoc requests directly to cursor-agent/codex without going through the task iteration system. This is perfect for quick updates, policy changes, or one-off requests:

```bash
cursor-iter run-agent --prompt "your request here"
```

This will:
- Send your request directly to cursor-agent or codex
- Automatically include references to all control files
- Ensure the agent understands the repository context
- Apply quality gates and best practices
- Update control files as needed

### Example Ad-hoc Requests

```bash
# Update build requirements
cursor-iter run-agent --prompt "add to our control files that pnpm build should succeed before marking any tasks as completed. Fix any issues during build and retry until it builds successfully before marking as complete"

# Add a new policy
cursor-iter run-agent --prompt "add a policy to qa_checklist.md that all API endpoints must have rate limiting"

# Quick refactoring
cursor-iter run-agent --prompt "refactor all logging to use structured logging with JSON format"

# Update documentation
cursor-iter run-agent --prompt "update architecture.md to document our new caching strategy using Redis"

# Use with Codex CLI
cursor-iter run-agent --codex --prompt "add error handling middleware to all API routes"
```

### When to Use `run-agent` vs `add-feature`

- **Use `run-agent`** for:
  - Quick policy or requirement changes
  - Updating control files
  - Small refactoring tasks
  - Documentation updates
  - One-off fixes or improvements

- **Use `add-feature`** for:
  - New features requiring architecture design
  - Multi-task implementations
  - Complex features needing planning
  - Features requiring multiple iterations

For more examples and detailed documentation, see [docs/RUN_AGENT_EXAMPLES.md](docs/RUN_AGENT_EXAMPLES.md).

## 🚀 Feature Addition Workflow

Add new features and requirements to your project:

```bash
cursor-iter add-feature
```

This will:
- Prompt you for multiline feature description
- Analyze current codebase structure
- Design architecture for the new feature
- Create detailed implementation tasks
- Update all relevant control files
- Plan testing and integration requirements

### Example Feature Addition

```bash
cursor-iter add-feature
# Enter your feature description (multiline, press Ctrl+D when done):
# 
# Implement a real-time notification system with WebSockets
# - Support multiple notification types (email, push, in-app)
# - Scalable architecture with Redis for message queuing
# - Authentication and authorization for notifications
# - Real-time delivery with fallback mechanisms
# - Admin dashboard for notification management
# 
# The system will then analyze your codebase and create comprehensive tasks.
```

### Task Management

Keep your `tasks.md` focused on current work:

```bash
cursor-iter archive-completed
```

This will:
- Move completed tasks to `completed_tasks/` folder
- Keep `tasks.md` minimal and current
- Update progress tracking
- Maintain task history for reference

### Task Structure Validation

Ensure your `tasks.md` has the correct structure:

```bash
# Validate tasks.md structure
cursor-iter validate-tasks

# Fix common structure issues automatically
cursor-iter validate-tasks --fix
```

This will:
- Check for required `## Current Tasks` section header
- Validate task format and structure
- Fix missing section headers automatically
- Ensure compatibility with `task-status` command

## 📚 Advanced Usage

### Model Selection

#### Cursor Agent (Default)
```bash
# Use specific model for initialization
cursor-iter iterate-init --model gpt-4o

# Use specific model for iteration (set via environment variable)
MODEL="gpt-4o" cursor-iter iterate
```

#### Codex CLI Support
```bash
# Install Codex CLI first
npm i -g @openai/codex

# Initialize using Codex with gpt-5-codex model
cursor-iter iterate-init --codex --model gpt-5-codex

# Run iterations using Codex
cursor-iter iterate --codex

# Run continuous loop using Codex
cursor-iter iterate-loop --codex

# Add features using Codex
cursor-iter add-feature --codex --prompt "Implement user authentication"
```

### Codex vs Cursor Agent

| Feature | Cursor Agent | Codex CLI |
|---------|-------------|-----------|
| **Default Model** | auto/gpt-4o | gpt-5-codex |
| **Installation** | `curl https://cursor.com/install -fsS \| bash` | `npm i -g @openai/codex` |
| **Command** | `cursor-agent --model <model> <prompt>` | `codex --model gpt-5-codex exec "<prompt>"` |
| **Use Case** | General development tasks | Agentic coding tasks |
| **Integration** | Built-in with Cursor IDE | Standalone CLI tool |

### Task Management
```bash
# Add new tasks
cursor-iter add-feature --prompt "Add tasks for implementing user authentication with OAuth2"

# Refine existing tasks
cursor-iter add-feature --prompt "Update the logging task to include structured logging with correlation IDs"
```

## 🚨 Troubleshooting

### Common Issues

**1. cursor-agent not found**
```bash
# Install cursor-agent
curl https://cursor.com/install -fsS | bash
export PATH="$HOME/.local/bin:$PATH"
```

**2. codex CLI not found**
```bash
# Install codex CLI
npm i -g @openai/codex
# Or use cursor-agent instead
cursor-iter iterate --model auto
```

**3. Tasks.md not found**
```bash
cursor-iter iterate-init
# Or with Codex
cursor-iter iterate-init --codex
```

**4. Quality gates failing**
```bash
cursor-iter iterate
# Or with Codex
cursor-iter iterate --codex
```

**5. Control files out of sync**
```bash
# Reset and regenerate
cursor-iter reset
cursor-iter iterate-init
# Or with Codex
cursor-iter iterate-init --codex
```

**6. Model selection issues**
```bash
# Use specific model with cursor-agent
cursor-iter iterate --model gpt-4o

# Use specific model with codex (defaults to gpt-5-codex)
cursor-iter iterate --codex --model gpt-5-codex
```

### Getting Help
```bash
# Check what the system detected
cursor-iter task-status

# Get task recommendations
cursor-iter add-feature --prompt "Review the current tasks.md and suggest improvements or additional tasks"
```

## 📈 Best Practices

### Task Management
1. **Be Specific**: Use detailed acceptance criteria and expected files
2. **Prioritize**: Order tasks by business value and dependencies
3. **Test-Driven**: Include test requirements in every task
4. **Incremental**: Break large tasks into smaller, manageable pieces

### Iteration Strategy
1. **Regular Runs**: Use `cursor-iter iterate` daily for steady progress
2. **Quality First**: Never skip quality gates
3. **Document Everything**: Let the system update control files automatically
4. **Review Progress**: Check `progress.md` regularly for insights

### Repository Maintenance
1. **Update Tasks**: Use natural language to add/modify tasks as requirements change
2. **Regenerate When Needed**: Re-run `cursor-iter iterate-init` if repository structure changes significantly
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

### Fully Automated with Cursor Agent (Recommended)
```bash
# 1. Install the system
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash

# 2. Initialize for your repository
cursor-iter iterate-init --model auto

# 3. Run until all tasks are completed
cursor-iter iterate-loop
```

### Fully Automated with Codex CLI
```bash
# 1. Install the system
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash

# 2. Install Codex CLI
npm i -g @openai/codex

# 3. Initialize for your repository using Codex
cursor-iter iterate-init --codex --model gpt-5-codex

# 4. Run until all tasks are completed using Codex
cursor-iter iterate-loop --codex
```

### Adding New Features
```bash
# 1. Add a new feature
cursor-iter add-feature
# Enter your feature description (multiline)

# 2. Run iterations until all tasks complete
cursor-iter iterate-loop

# 3. Archive completed tasks (optional)
cursor-iter archive-completed
```

### Manual Control
```bash
# 1. Install the system
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash

# 2. Initialize for your repository
cursor-iter iterate-init --model auto

# 3. Check task status and progress
cursor-iter task-status

# 4. Run individual iterations
cursor-iter iterate

# 5. Add new features as needed
cursor-iter add-feature

# 6. Continue iterating
cursor-iter iterate

# 7. Reset when needed
cursor-iter reset
```

## 📊 Current Status

| Component               | Status             | Coverage | Features                                                  |
| ----------------------- | ------------------ | -------- | --------------------------------------------------------- |
| **Universal Detection** | ✅ Production Ready | 100%     | Python, TypeScript, Go, Rust, Java, Infrastructure, Shell |
| **Quality Gates**       | ✅ Production Ready | 100%     | Linting, formatting, testing, security                    |
| **Task Management**     | ✅ Production Ready | 100%     | Create, track, archive, status reporting                  |
| **Continuous Loop**     | ✅ Production Ready | 100%     | Automated iteration until completion                      |
| **Feature Addition**    | ✅ Production Ready | 100%     | Natural language feature requests                         |
| **Progress Tracking**   | ✅ Production Ready | 100%     | Real-time status and completion tracking                  |
| **Agent Support**       | ✅ Production Ready | 100%     | Cursor Agent and Codex CLI integration                    |

## 🎯 Key Features

- **🧠 Universal Technology Detection**: Automatically detects and supports Python, TypeScript, Go, Rust, Java, Infrastructure, and Shell projects
- **🔧 Quality Gates**: Enforces appropriate standards for each detected technology stack
- **📋 Smart Task Management**: Creates, tracks, and manages task backlogs with detailed status reporting
- **🔄 Continuous Automation**: Runs iterations until all tasks are completed with safety limits
- **🚀 Feature Addition**: Natural language feature request processing with architecture analysis
- **📊 Progress Tracking**: Real-time status reporting and completion tracking
- **🛡️ Safety Features**: Prevents infinite loops and maintains system integrity
- **🤖 Dual Agent Support**: Supports both Cursor Agent and Codex CLI for maximum flexibility

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
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash
```
