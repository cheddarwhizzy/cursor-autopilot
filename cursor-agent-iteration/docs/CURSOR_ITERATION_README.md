# Cursor Agent Iteration System

A self-managing engineering loop for any repository type using Cursor Agent CLI. Automatically detects your technology stack and creates tailored tasks with appropriate quality gates.

## 🚀 Installation

```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash
```

## ⚡ Quick Start

```bash
# 1. Initialize the system (analyzes your repo)
make iterate-init

# 2. Start working on tasks
make iterate
```

## 🔧 Supported Technologies

The system automatically detects and supports:

| Technology | Quality Gates | Test Framework |
|------------|---------------|----------------|
| **Python** | `ruff`, `black`, `mypy`, `pytest` | pytest, hypothesis |
| **TypeScript/JavaScript** | `tsc`, `eslint`, `jest` | jest, vitest, playwright |
| **Go** | `go vet`, `golangci-lint`, `gofmt` | go test, testify |
| **Rust** | `cargo clippy`, `cargo fmt`, `cargo audit` | cargo test, proptest |
| **Java** | `mvn spotbugs`, `mvn checkstyle`, `mvn pmd` | JUnit, TestNG |
| **Infrastructure** | `terraform validate`, `ansible-lint`, `dockerfile-lint` | terratest, molecule |
| **Shell** | `shellcheck`, `bashate` | bats, shunit2 |

## 📋 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `make iterate-init` | Initialize and analyze repository | `make iterate-init` |
| `make iterate` | Run the next task | `make iterate` |
| `make iterate-custom` | Run with custom focus | `make iterate-custom PROMPT="Work on security"` |
| `make tasks-update` | Add new tasks | `make tasks-update PROMPT="Add API tasks"` |

## 🎯 How It Works

1. **Repository Analysis**: Detects languages, frameworks, and structure
2. **Task Generation**: Creates realistic, technology-specific tasks
3. **Quality Gates**: Enforces appropriate standards for each detected stack
4. **Iteration Loop**: Runs Plan → Implement → Test → Validate → Document → Commit
5. **Progress Tracking**: Updates control files automatically

## 📁 Generated Files

After `make iterate-init`:
- `prompts/iterate.md` - Tailored iteration prompt
- `tasks.md` - Technology-specific task backlog
- `architecture.md` - System architecture documentation
- `progress.md` - Progress tracking and evidence
- `decisions.md` - Architectural Decision Records
- `test_plan.md` - Test coverage plans
- `qa_checklist.md` - Quality assurance checklist
- `CHANGELOG.md` - Conventional commits log

## 🚨 Troubleshooting

### cursor-agent not found?
```bash
curl https://cursor.com/install -fsS | bash
export PATH="$HOME/.local/bin:$PATH"
```

### Need to reanalyze repository?
```bash
make iterate-init
```

### Quality gates failing?
```bash
make iterate-custom PROMPT="Diagnose and fix quality gate failures"
```

## 📚 Examples

### Go Project
```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash
make iterate-init  # Detects Go, creates Go-specific tasks
make iterate       # Runs Go quality gates (go vet, golangci-lint, go test)
```

### Rust Project
```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash
make iterate-init  # Detects Rust, creates Rust-specific tasks
make iterate       # Runs Rust quality gates (cargo clippy, cargo test, cargo fmt)
```

### Infrastructure Project
```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash
make iterate-init  # Detects Terraform/Ansible, creates infrastructure tasks
make iterate       # Runs infrastructure quality gates (terraform validate, ansible-lint)
```

---

**Ready to start?** Run the bootstrap command and begin iterating!
