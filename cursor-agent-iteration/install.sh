#!/usr/bin/env bash
# Cursor Agent Iteration System - Installation Script
# This script installs the polyglot iteration system for any repository

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Installing Cursor Agent Iteration System${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository. Please run this script from your project root.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${CYAN}📁 Creating directory structure...${NC}"
mkdir -p prompts
mkdir -p scripts

# Copy core files
echo -e "${CYAN}📄 Installing core iteration files...${NC}"

# Create the initialization prompt
cat > prompts/initialize-iteration-polyglot.md << 'EOF'
SYSTEM
You are a staff‑level engineer configuring a **self‑managing engineering loop** for a polyglot repository that is primarily **Python** with some **TypeScript (Payload CMS)**. Generate two files:
1) `prompts/iterate.md` — the recurring iteration prompt.
2) `tasks.md` — an initial backlog seeded from what you detect in THIS repository.

Hard requirements
- Auto‑detect languages, frameworks, package managers, and folder layout (e.g., `apps/`, `packages/`, `services/`, `src/`, `backend/`, `frontend/`).
- Treat Python as **first‑class**. Enforce typing and quality gates:
  - Typing: `mypy` (strict if feasible), `pyright` if present; PEP 561 for typed packages.
  - Tests: `pytest` (+ `pytest-cov`), optional property testing with `hypothesis`.
  - Lint/format: `ruff` (lint + import sort), `black` (format), `isort` if used.
  - Packaging/runtime: `uv`/`pip`/`poetry`/`pip-tools` — detect and note commands.
- Treat TypeScript (Payload CMS) with appropriate guardrails:
  - `tsc --noEmit` under `strict` where possible.
  - Tests: `vitest` or `jest` if present; E2E via `playwright`/`cypress` if present.
  - Runtime validation at boundaries with `zod` (or note gap if absent).
- Respect **client/server boundary**: secrets server‑side only; no env leakage into client bundles.
- Always read and maintain the control files on each run: `architecture.md`, `tasks.md`, `progress.md`, `decisions.md`, `test_plan.md`, `qa_checklist.md`, `CHANGELOG.md`.
- Use existing code first; if creating a new file is necessary, write an ADR in `decisions.md`.
- Output repository‑specific content: name actual paths, modules, commands you discover. No boilerplate.

Deliverables this run
- Patches that create `prompts/iterate.md` and `tasks.md`.
- A short summary of detected stacks (Python and TS), test commands, and coverage targets.

Specification for `prompts/iterate.md`
- On EVERY invocation it must:
  1) Read the control files above.
  2) Pick the next **unchecked** task in `tasks.md`.
  3) Plan → Implement → Test → Validate → Document → Commit.
  4) Update: mark task done, add evidence (test names, logs) in `progress.md`, add/adjust `test_plan.md`, append ADRs when decisions happen, and update `CHANGELOG.md` with Conventional Commits.
  5) Keep edits minimal and focused; prefer refactors over rewrites.
- Validation gates by stack:
  - Python: run `ruff`, `black --check`, `mypy`, and `pytest -q --maxfail=1 --disable-warnings --cov` (tune to repo). Fail the task if any gate fails; fix then continue.
  - TypeScript: run `tsc --noEmit`, `eslint`/`biome` if present, and unit/E2E tests.
- Output format (for the assistant message):
  - Summary of control files state and the selected task
  - Proposed plan
  - Patch blocks (code + tests)
  - Results of typecheck/lint/tests
  - Control files updates (snippets of changes)

Specification for `tasks.md` generation
- Create if missing; otherwise merge additively.
- Include 4–8 realistic, **repo‑specific** tasks spanning Python and TS. Examples (adapt them to this repo):
  - Python: add/strengthen type hints and `mypy` config for `src/**`, convert dynamic dicts to TypedDict/dataclasses/pydantic models, add hypothesis property tests for parsers, improve logging/metrics, harden error handling and retries for external calls.
  - TS/Payload: add `zod` schemas at API boundaries, ensure `tsc --noEmit` under `strict`, add integration tests for server actions, and ensure no secrets in client bundles.
  - CI: add quality gates (ruff/black/mypy/pytest/coverage, tsc/eslint/tests), cache deps, artifact test reports.
  - Observability: add structured logging and minimal tracing where appropriate.
- Each task must have: Context, Acceptance Criteria (checkboxes), Tests (unit/integration/E2E), Expected files to touch, and an unchecked box.
- Include a first task named **"Setup Verification: Run the loop end‑to‑end"** to prove the system works.

Repository analysis checklist (to inform both files)
- Python env: detect `pyproject.toml`, `poetry.lock`, `requirements*.txt`, `uv.lock`, `setup.cfg`.
- Test layout: `tests/` packages, fixtures, markers, coverage config.
- Lint/format configs: `ruff.toml`, `.ruff.toml`, `pyproject` sections; `black` line length.
- TS env: `package.json` scripts, `tsconfig*.json`, test runners.
- Workflows: `.github/workflows/*.yml`, `Jenkinsfile`, `gitlab-ci.yml`.
- Data/infra: Postgres, Qdrant, Redis, S3/bunny, Prometheus/Loki, etc.

Output format for THIS run
1) Short stack summary (Python + TS findings).
2) **Patches** for `prompts/iterate.md` and `tasks.md`.
3) "Next Steps" instructions (how to start iteration via `cursor-cli`).
END SYSTEM

USER
Goal: Create `prompts/iterate.md` and an initial `tasks.md` tailored to this Python‑heavy, TS‑partial repository. Ensure the iteration prompt enforces Python typing/testing gates (mypy/pytest/ruff/black) and TS gates (tsc/jest|vitest, zod at boundaries). Keep everything repository‑specific and wire updates into the control files on every run.
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

PROMPT_FILE="./prompts/initialize-iteration-polyglot.md"
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

echo "⚙️  Generating prompts/iterate.md + tasks.md (polyglot aware)"
cursor-agent --print --force --model "$MODEL" "$(cat "$PROMPT_FILE")"

echo "✅ Created/updated: prompts/iterate.md, tasks.md"
echo "➡️  Start the loop with:"
echo "   cursor-agent --print --force --prompt prompts/iterate.md"
EOF

# Make the script executable
chmod +x scripts/init-iterate.sh

# Create Makefile targets
echo -e "${CYAN}📝 Adding Makefile targets...${NC}"

# Check if Makefile exists, if not create one
if [[ ! -f "Makefile" ]]; then
    echo -e "${YELLOW}⚠️  No Makefile found. Creating a new one...${NC}"
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

EOF
fi

# Add iteration targets to existing Makefile
cat >> Makefile << 'EOF'

## iterate-init: Initialize polyglot iteration system (Python + TypeScript)
iterate-init:
	@echo "Initializing polyglot iteration system..."
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

# Create comprehensive README
echo -e "${CYAN}📚 Creating documentation...${NC}"
cat > CURSOR_ITERATION_README.md << 'EOF'
# Cursor Agent Iteration System

A self-managing engineering loop for polyglot repositories (Python + TypeScript) using Cursor Agent CLI.

## 🚀 Quick Start

### 1. Initialize the System
```bash
make iterate-init
```

### 2. Start Iterating
```bash
make iterate
```

## 📋 Available Commands

### Core Commands
- `make iterate-init` - Initialize the iteration system
- `make iterate` - Run the next task in the backlog
- `make iterate-custom PROMPT="..."` - Run with custom prompt
- `make tasks-update PROMPT="..."` - Update task list

### Examples

**Standard Iteration:**
```bash
make iterate
```

**Custom Iteration:**
```bash
make iterate-custom PROMPT="Work on the next security-related task"
```

**Update Tasks:**
```bash
make tasks-update PROMPT="Add a new task for implementing user authentication"
```

## 📁 Generated Files

After running `make iterate-init`, you'll get:
- `prompts/iterate.md` - Recurring iteration prompt
- `tasks.md` - Task backlog
- `architecture.md` - Architecture documentation
- `progress.md` - Progress tracking
- `decisions.md` - Architectural Decision Records
- `test_plan.md` - Test coverage plans
- `qa_checklist.md` - Quality assurance checklist
- `CHANGELOG.md` - Conventional commits log

## 🎯 How It Works

1. **Read Control Files** - The system reads all control files to understand current state
2. **Select Next Task** - Picks the first unchecked task from `tasks.md`
3. **Plan → Implement → Test → Validate → Document → Commit**
4. **Update Control Files** - Marks task complete and updates progress

## 🔧 Quality Gates

### Python Stack
- `ruff` - Linting
- `black --check` - Code formatting
- `mypy` - Type checking
- `pytest` - Testing with coverage

### TypeScript Stack
- `tsc --noEmit` - Type checking
- `eslint` - Linting
- `jest`/`vitest` - Testing
- `zod` - Runtime validation at API boundaries

## 📚 Advanced Usage

### Model Selection
```bash
# Use specific model for initialization
MODEL="gpt-4o" make iterate-init

# Use specific model for iteration
MODEL="gpt-4o" make iterate
```

### Task Management
```bash
# Add new tasks
make tasks-update PROMPT="Add tasks for implementing GraphQL API"

# Work on specific task types
make iterate-custom PROMPT="Find and work on the next 'database' related task"
```

## 🚨 Troubleshooting

### Common Issues

**1. cursor-agent not found:**
```bash
# Install cursor-agent
curl https://cursor.com/install -fsS | bash
export PATH="$HOME/.local/bin:$PATH"
```

**2. Tasks.md not found:**
```bash
make iterate-init
```

**3. Quality gates failing:**
```bash
make iterate-custom PROMPT="Diagnose why quality gates are failing"
```

## 📈 Best Practices

1. **Regular Runs** - Use `make iterate` daily for steady progress
2. **Quality First** - Never skip quality gates
3. **Document Everything** - Let the system update control files automatically
4. **Review Progress** - Check `progress.md` regularly for insights

## 🎯 Success Metrics

The system tracks:
- ✅ Task Completion Rate
- ✅ Quality Gate Pass Rate  
- ✅ Test Coverage
- ✅ Documentation Coverage
- ✅ Commit Quality

---

**Ready to start?** Run `make iterate-init` and begin the engineering iteration loop!
EOF

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo -e "${CYAN}📋 Next Steps:${NC}"
echo -e "   1. ${YELLOW}make iterate-init${NC}     # Initialize the iteration system"
echo -e "   2. ${YELLOW}make iterate${NC}          # Start working on tasks"
echo ""
echo -e "${CYAN}📚 Documentation:${NC}"
echo -e "   - Read ${YELLOW}CURSOR_ITERATION_README.md${NC} for detailed usage"
echo -e "   - Check ${YELLOW}prompts/iterate.md${NC} after initialization"
echo -e "   - Review ${YELLOW}tasks.md${NC} for your task backlog"
echo ""
echo -e "${GREEN}🎉 Happy iterating!${NC}"
