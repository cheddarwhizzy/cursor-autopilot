#!/usr/bin/env bash
# Cursor Agent Iteration System - Bootstrap Script
# Usage: curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/cursor-cli-headleess-agent/cursor-agent-iteration/bootstrap.sh | bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Bootstrap Cursor Agent Iteration System${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository. Please run this script from your project root.${NC}"
    exit 1
fi

# Ensure cursor-agent is installed
if ! command -v cursor-agent >/dev/null 2>&1; then
  echo -e "${YELLOW}📦 Installing cursor-agent...${NC}"
  curl https://cursor.com/install -fsS | bash
  echo -e "${YELLOW}Note: You may need to add ~/.local/bin to PATH and restart your shell${NC}"
  export PATH="$HOME/.local/bin:$PATH"
fi

# Create necessary directories
echo -e "${CYAN}📁 Creating directory structure...${NC}"
mkdir -p prompts
mkdir -p scripts

# Create the universal initialization prompt
cat > prompts/initialize-iteration-universal.md << 'EOF'
SYSTEM
You are a staff‑level engineer configuring a **self‑managing engineering loop** for any repository type. Generate two files:
1) `prompts/iterate.md` — the recurring iteration prompt.
2) `tasks.md` — an initial backlog seeded from what you detect in THIS repository.

Hard requirements
- Auto‑detect languages, frameworks, package managers, and folder layout (e.g., `apps/`, `packages/`, `services/`, `src/`, `backend/`, `frontend/`, `cmd/`, `pkg/`, `internal/`).
- Treat detected technologies with appropriate quality gates:
  - **Python**: `mypy` (strict if feasible), `pytest` (+ `pytest-cov`), `ruff` (lint + import sort), `black` (format)
  - **TypeScript/JavaScript**: `tsc --noEmit` under `strict`, `eslint`/`biome`, `jest`/`vitest`, `zod` for runtime validation
  - **Go**: `go vet`, `golangci-lint`, `go test -race -cover`, `gofmt`, `go mod tidy`
  - **Rust**: `cargo clippy`, `cargo test`, `cargo fmt`, `cargo audit`
  - **Java**: `mvn test`, `mvn spotbugs:check`, `mvn checkstyle:check`, `mvn pmd:check`
  - **Infrastructure**: `terraform validate`, `terraform plan`, `ansible-lint`, `dockerfile-lint`, `helm lint`
  - **Shell**: `shellcheck`, `bashate`
- Respect **client/server boundary**: secrets server‑side only; no env leakage into client bundles.
- Always read and maintain the control files on each run: `architecture.md`, `tasks.md`, `progress.md`, `decisions.md`, `test_plan.md`, `qa_checklist.md`, `CHANGELOG.md`.
- Use existing code first; if creating a new file is necessary, write an ADR in `decisions.md`.
- Output repository‑specific content: name actual paths, modules, commands you discover. No boilerplate.

Deliverables this run
- Patches that create `prompts/iterate.md` and `tasks.md`.
- A short summary of detected stacks, test commands, and coverage targets.

Specification for `prompts/iterate.md`
- On EVERY invocation it must:
  1) Read the control files above.
  2) Pick the next **unchecked** task in `tasks.md`.
  3) Plan → Implement → Test → Validate → Document → Commit.
  4) Update: mark task done, add evidence (test names, logs) in `progress.md`, add/adjust `test_plan.md`, append ADRs when decisions happen, and update `CHANGELOG.md` with Conventional Commits.
  5) Keep edits minimal and focused; prefer refactors over rewrites.
- Validation gates by detected stack:
  - **Python**: `ruff`, `black --check`, `mypy`, `pytest -q --maxfail=1 --disable-warnings --cov`
  - **TypeScript/JavaScript**: `tsc --noEmit`, `eslint`, unit/E2E tests
  - **Go**: `go vet`, `golangci-lint`, `go test -race -cover`, `gofmt`, `go mod tidy`
  - **Rust**: `cargo clippy`, `cargo test`, `cargo fmt`, `cargo audit`
  - **Java**: `mvn test`, `mvn spotbugs:check`, `mvn checkstyle:check`
  - **Infrastructure**: `terraform validate`, `terraform plan`, `ansible-lint`, `dockerfile-lint`
  - **Shell**: `shellcheck`, `bashate`
- Fail the task if any gate fails; fix then continue.
- Output format (for the assistant message):
  - Summary of control files state and the selected task
  - Proposed plan
  - Patch blocks (code + tests)
  - Results of typecheck/lint/tests
  - Control files updates (snippets of changes)

Specification for `tasks.md` generation
- Create if missing; otherwise merge additively.
- Include 4–8 realistic, **repo‑specific** tasks spanning detected technologies. Examples (adapt them to this repo):
  - **Python**: add/strengthen type hints and `mypy` config, convert dynamic dicts to TypedDict/dataclasses/pydantic models, add hypothesis property tests, improve logging/metrics, harden error handling
  - **TypeScript/JavaScript**: add `zod` schemas at API boundaries, ensure `tsc --noEmit` under `strict`, add integration tests, ensure no secrets in client bundles
  - **Go**: add comprehensive error handling, improve logging with structured logs, add benchmarks, implement graceful shutdown, add integration tests
  - **Rust**: improve error handling with `thiserror`/`anyhow`, add comprehensive tests, implement proper logging, add performance benchmarks
  - **Java**: improve exception handling, add comprehensive unit tests, implement proper logging, add integration tests
  - **Infrastructure**: add validation, improve security scanning, add comprehensive testing, implement proper monitoring
  - **CI/CD**: add quality gates, cache deps, artifact test reports, security scanning
  - **Observability**: add structured logging, minimal tracing, metrics collection
- Each task must have: Context, Acceptance Criteria (checkboxes), Tests (unit/integration/E2E), Expected files to touch, and an unchecked box.
- Include a first task named **"Setup Verification: Run the loop end‑to‑end"** to prove the system works.

Repository analysis checklist (to inform both files)
- **Languages**: detect `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, `requirements.txt`, `Gemfile`, `composer.json`
- **Test layout**: `tests/`, `test/`, `*_test.go`, `*_test.rs`, `src/test/`, `__tests__/`, fixtures, markers, coverage config
- **Lint/format configs**: `ruff.toml`, `.eslintrc`, `golangci.yml`, `clippy.toml`, `checkstyle.xml`, `.terraform/`, `ansible.cfg`
- **Workflows**: `.github/workflows/*.yml`, `Jenkinsfile`, `gitlab-ci.yml`, `.circleci/`, `azure-pipelines.yml`
- **Infrastructure**: `Dockerfile`, `docker-compose.yml`, `terraform/`, `ansible/`, `k8s/`, `helm/`
- **Data/infra**: Postgres, Redis, MongoDB, S3, Prometheus, Grafana, etc.

Output format for THIS run
1) Short stack summary (detected technologies and findings).
2) **Patches** for `prompts/iterate.md` and `tasks.md`.
3) "Next Steps" instructions (how to start iteration via `cursor-agent`).
END SYSTEM

USER
Goal: Create `prompts/iterate.md` and an initial `tasks.md` tailored to this repository. Auto-detect all technologies (Python, TypeScript, Go, Rust, Java, Infrastructure, etc.) and enforce appropriate quality gates for each detected stack. Keep everything repository‑specific and wire updates into the control files on every run.
Constraints:
- Do not reorganize the repo; use existing files and conventions.
- Prefer minimal, incremental diffs.
- If assumptions are needed, mark TODOs with how to verify.
Deliverables:
- Patches for both files.
- Short summary + Next Steps.
EOF

# Create the initialization script
cat > scripts/init-iterate.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

PROMPT_FILE="./prompts/initialize-iteration-universal.md"
TARGET_DIR="${1:-.}"
MODEL="${MODEL:-gpt-4o-mini}"   # override with: MODEL="gpt-4o" ./scripts/init-iterate.sh

if ! command -v cursor-agent >/dev/null 2>&1; then
  echo "Installing cursor-agent..."
  curl https://cursor.com/install -fsS | bash
  echo "Note: You may need to add ~/.local/bin to PATH and restart your shell"
  export PATH="$HOME/.local/bin:$PATH"
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "❌ Missing prompt file: $PROMPT_FILE"
  exit 1
fi

echo "⚙️  Generating prompts/iterate.md + tasks.md (universal detection)"
cursor-agent --print --force --model "$MODEL" "$(cat "$PROMPT_FILE")"

echo "✅ Created/updated: prompts/iterate.md, tasks.md"
echo "➡️  Start the loop with:"
echo "   cursor-agent --print --force --prompt prompts/iterate.md"
EOF

# Make the script executable
chmod +x scripts/init-iterate.sh

# Check if Makefile exists, if not create one
if [[ ! -f "Makefile" ]]; then
    echo -e "${YELLOW}📝 Creating Makefile...${NC}"
    cat > Makefile << 'EOF'
# Makefile for Cursor Agent Iteration System

.PHONY: help iterate-init iterate iterate-custom tasks-update

## help: Show this help message
help:
	@echo "Cursor Agent Iteration System"
	@echo ""
	@echo "Available targets:"
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'
	@echo ""
	@echo "Examples:"
	@echo "  make iterate-init    # Initialize the iteration system"
	@echo "  make iterate         # Run the next task"
	@echo "  make iterate-custom  # Run with custom prompt"

## iterate-init: Initialize universal iteration system
iterate-init:
	@echo "Initializing universal iteration system..."
	@./scripts/init-iterate.sh
	@echo "Iteration system ready! Run 'make iterate' to start the engineering loop."

## iterate: Run the self-managing engineering iteration loop
iterate:
	@echo "Starting engineering iteration loop..."
	@cursor-agent --print --force "Please execute the engineering iteration loop as defined in prompts/iterate.md. Read the control files (architecture.md, tasks.md, progress.md, decisions.md, test_plan.md, qa_checklist.md, CHANGELOG.md) and select the first unchecked task from tasks.md. Then implement, test, validate, document, and commit the changes following the quality gates specified in the iteration prompt."
	@echo "Iteration complete! Check progress.md for details."

## iterate-custom: Run iteration with custom prompt
iterate-custom:
	@echo "Starting custom iteration..."
	@cursor-agent --print --force "$(PROMPT)"
	@echo "Custom iteration complete!"

## tasks-update: Update task list with natural language
tasks-update:
	@echo "Updating task list..."
	@cursor-agent --print --force "Update tasks.md based on: $(PROMPT)"
	@echo "Task list updated!"
EOF
else
    echo -e "${CYAN}📝 Adding Makefile targets...${NC}"
    # Add iteration targets to existing Makefile
    cat >> Makefile << 'EOF'

## iterate-init: Initialize universal iteration system
iterate-init:
	@echo "Initializing universal iteration system..."
	@./scripts/init-iterate.sh
	@echo "Iteration system ready! Run 'make iterate' to start the engineering loop."

## iterate: Run the self-managing engineering iteration loop
iterate:
	@echo "Starting engineering iteration loop..."
	@cursor-agent --print --force "Please execute the engineering iteration loop as defined in prompts/iterate.md. Read the control files (architecture.md, tasks.md, progress.md, decisions.md, test_plan.md, qa_checklist.md, CHANGELOG.md) and select the first unchecked task from tasks.md. Then implement, test, validate, document, and commit the changes following the quality gates specified in the iteration prompt."
	@echo "Iteration complete! Check progress.md for details."

## iterate-custom: Run iteration with custom prompt
iterate-custom:
	@echo "Starting custom iteration..."
	@cursor-agent --print --force "$(PROMPT)"
	@echo "Custom iteration complete!"

## tasks-update: Update task list with natural language
tasks-update:
	@echo "Updating task list..."
	@cursor-agent --print --force "Update tasks.md based on: $(PROMPT)"
	@echo "Task list updated!"
EOF
fi

# Create initial control files
echo -e "${CYAN}📋 Creating control files...${NC}"

# Create architecture.md
cat > architecture.md << 'EOF'
# Architecture Documentation

This file will be automatically updated by the iteration system as the project evolves.

## Current State
- Repository structure detected during bootstrap
- Technology stack analysis pending

## Components
- To be populated by iteration system

## Data Flow
- To be documented during development

## Dependencies
- To be analyzed and documented

---
*This file is managed by the Cursor Agent Iteration System*
EOF

# Create progress.md
cat > progress.md << 'EOF'
# Progress Tracking

This file tracks the progress of the iteration system.

## Bootstrap Completed
- **Date**: $(date)
- **Repository**: $(pwd)
- **Git Branch**: $(git branch --show-current 2>/dev/null || echo "unknown")
- **Status**: Bootstrap completed successfully

## Tasks Completed
- [x] Bootstrap iteration system
- [x] Initialize control files
- [x] Set up directory structure

## Next Steps
1. Run `make iterate-init` to analyze repository and generate tasks
2. Run `make iterate` to start working on tasks

---
*This file is automatically updated by the iteration system*
EOF

# Create decisions.md
cat > decisions.md << 'EOF'
# Architectural Decision Records (ADRs)

This file tracks important architectural decisions made during development.

## ADR-001: Cursor Agent Iteration System
- **Date**: $(date)
- **Status**: Accepted
- **Context**: Implemented self-managing engineering loop using Cursor Agent CLI
- **Decision**: Use cursor-agent for automated code generation and iteration
- **Consequences**: 
  - Automated task management and execution
  - Quality gate enforcement
  - Progress tracking and documentation

---
*This file is automatically updated by the iteration system*
EOF

# Create test_plan.md
cat > test_plan.md << 'EOF'
# Test Plan

This file tracks test coverage plans and requirements.

## Coverage Targets
- **Python**: ≥ 70% line coverage (pytest)
- **TypeScript/JavaScript**: ≥ 80% line coverage (jest/vitest)
- **Go**: ≥ 80% line coverage (go test)
- **Rust**: ≥ 80% line coverage (cargo test)
- **Java**: ≥ 70% line coverage (JUnit/TestNG)
- **Infrastructure**: Validation and security scanning

## Test Strategy
- Unit tests for all business logic
- Integration tests for API endpoints
- E2E tests for critical user flows
- Security tests for authentication and authorization

---
*This file is automatically updated by the iteration system*
EOF

# Create qa_checklist.md
cat > qa_checklist.md << 'EOF'
# Quality Assurance Checklist

This file tracks quality gates and validation criteria.

## Code Quality Gates
- [ ] **Linting**: All code passes linting rules
- [ ] **Formatting**: Code is properly formatted
- [ ] **Type Checking**: All types are properly defined
- [ ] **Testing**: Adequate test coverage
- [ ] **Security**: No security vulnerabilities
- [ ] **Documentation**: Code is properly documented

## Technology-Specific Gates
- **Python**: ruff, black, mypy, pytest
- **TypeScript/JavaScript**: tsc, eslint, jest/vitest
- **Go**: go vet, golangci-lint, go test
- **Rust**: cargo clippy, cargo test, cargo fmt
- **Java**: mvn spotbugs, mvn checkstyle, mvn test
- **Infrastructure**: terraform validate, ansible-lint, dockerfile-lint

---
*This file is automatically updated by the iteration system*
EOF

# Create CHANGELOG.md
cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Cursor Agent Iteration System bootstrap
- Universal technology detection
- Quality gate enforcement
- Progress tracking and documentation

---
*This file is automatically updated by the iteration system*
EOF

# Create context.md (if it doesn't exist)
if [[ ! -f "context.md" ]]; then
cat > context.md << 'EOF'
# Project Context

This file provides context about the project for the iteration system.

## Project Overview
- **Repository**: $(pwd)
- **Primary Languages**: To be detected during initialization
- **Frameworks**: To be detected during initialization
- **Infrastructure**: To be detected during initialization

## Development Environment
- **OS**: $(uname -s)
- **Shell**: $(basename $SHELL)
- **Git**: $(git --version 2>/dev/null || echo "Not available")

## Key Files
- To be populated during repository analysis

---
*This file is automatically updated by the iteration system*
EOF
fi

# Create comprehensive README
echo -e "${CYAN}📚 Creating documentation...${NC}"
cat > CURSOR_ITERATION_README.md << 'EOF'
# Cursor Agent Iteration System

A self-managing engineering loop for any repository type using Cursor Agent CLI. Automatically detects your technology stack and creates tailored tasks with appropriate quality gates.

## 🚀 Installation

```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/cursor-cli-headleess-agent/cursor-agent-iteration/bootstrap.sh | bash
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
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/cursor-cli-headleess-agent/cursor-agent-iteration/bootstrap.sh | bash
make iterate-init  # Detects Go, creates Go-specific tasks
make iterate       # Runs Go quality gates (go vet, golangci-lint, go test)
```

### Rust Project
```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/cursor-cli-headleess-agent/cursor-agent-iteration/bootstrap.sh | bash
make iterate-init  # Detects Rust, creates Rust-specific tasks
make iterate       # Runs Rust quality gates (cargo clippy, cargo test, cargo fmt)
```

### Infrastructure Project
```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/cursor-cli-headleess-agent/cursor-agent-iteration/bootstrap.sh | bash
make iterate-init  # Detects Terraform/Ansible, creates infrastructure tasks
make iterate       # Runs infrastructure quality gates (terraform validate, ansible-lint)
```

---

**Ready to start?** Run the bootstrap command and begin iterating!
EOF

echo ""
echo -e "${GREEN}✅ Bootstrap complete!${NC}"
echo ""
echo -e "${CYAN}📋 Created Files:${NC}"
echo -e "   - ${YELLOW}prompts/initialize-iteration-universal.md${NC} - Universal initialization prompt"
echo -e "   - ${YELLOW}scripts/init-iterate.sh${NC} - Initialization script"
echo -e "   - ${YELLOW}architecture.md${NC} - Architecture documentation"
echo -e "   - ${YELLOW}progress.md${NC} - Progress tracking"
echo -e "   - ${YELLOW}decisions.md${NC} - Architectural Decision Records"
echo -e "   - ${YELLOW}test_plan.md${NC} - Test coverage plans"
echo -e "   - ${YELLOW}qa_checklist.md${NC} - Quality assurance checklist"
echo -e "   - ${YELLOW}CHANGELOG.md${NC} - Conventional commits log"
echo -e "   - ${YELLOW}context.md${NC} - Project context (if not existing)"
echo ""
echo -e "${CYAN}📋 Next Steps:${NC}"
echo -e "   1. ${YELLOW}make iterate-init${NC}     # Initialize and analyze your repository"
echo -e "   2. ${YELLOW}make iterate${NC}          # Start working on tasks"
echo ""
echo -e "${CYAN}📚 Documentation:${NC}"
echo -e "   - Read ${YELLOW}CURSOR_ITERATION_README.md${NC} for detailed usage"
echo -e "   - Check ${YELLOW}prompts/iterate.md${NC} after initialization"
echo -e "   - Review ${YELLOW}tasks.md${NC} for your technology-specific task backlog"
echo ""
echo -e "${GREEN}🎉 Happy iterating!${NC}"
