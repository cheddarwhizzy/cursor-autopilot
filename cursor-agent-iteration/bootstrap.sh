#!/usr/bin/env bash
# Cursor Agent Iteration System - Bootstrap Script
# Usage: curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash

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

echo "⚙️  Analyzing codebase and generating prompts/iterate.md (universal detection)"
cursor-agent --print --force --model "$MODEL" "$(cat "$PROMPT_FILE")"

echo "✅ Created/updated: prompts/iterate.md"
echo "📋 Control files populated with codebase analysis"
echo "➡️  Next steps:"
echo "   make add-feature  # Add new feature/requirements to architect and create tasks"
echo "   make task-status  # Show current task status (will be empty until features added)"
EOF

# Make the script executable
chmod +x scripts/init-iterate.sh

# Create the completion check script
cat > scripts/check-complete.sh << 'EOF'
#!/usr/bin/env bash
# Check if all tasks are completed

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if tasks.md exists
if [[ ! -f "tasks.md" ]]; then
    echo -e "${RED}❌ tasks.md not found. Run 'make iterate-init' first.${NC}"
    exit 1
fi

# Count total tasks and completed tasks
TOTAL_TASKS=$(grep -c "^- \[" tasks.md 2>/dev/null || echo "0")
COMPLETED_TASKS=$(grep -c "^- \[x\]" tasks.md 2>/dev/null || echo "0")

# Ensure we have valid numbers for arithmetic
if [[ ! "$TOTAL_TASKS" =~ ^[0-9]+$ ]]; then
    TOTAL_TASKS=0
fi
if [[ ! "$COMPLETED_TASKS" =~ ^[0-9]+$ ]]; then
    COMPLETED_TASKS=0
fi

REMAINING_TASKS=$((TOTAL_TASKS - COMPLETED_TASKS))

echo -e "${CYAN}📊 Task Status:${NC}"
echo -e "   Total tasks: ${YELLOW}$TOTAL_TASKS${NC}"
echo -e "   Completed: ${GREEN}$COMPLETED_TASKS${NC}"
echo -e "   Remaining: ${RED}$REMAINING_TASKS${NC}"

if [[ $REMAINING_TASKS -eq 0 && $TOTAL_TASKS -gt 0 ]]; then
    echo -e "${GREEN}✅ All tasks completed!${NC}"
    echo -e "${CYAN}🎉 Project iteration cycle is complete!${NC}"
    
    # Update progress.md with completion
    if [[ -f "progress.md" ]]; then
        echo "" >> progress.md
        echo "## 🎉 All Tasks Completed" >> progress.md
        echo "- **Date**: $(date)" >> progress.md
        echo "- **Status**: All $TOTAL_TASKS tasks completed successfully" >> progress.md
        echo "- **Next Steps**: Project ready for next phase or new feature development" >> progress.md
    fi
    
    # Update CHANGELOG.md with completion
    if [[ -f "CHANGELOG.md" ]]; then
        # Add completion entry to CHANGELOG
        sed -i.tmp '/## \[Unreleased\]/a\
\
### Completed\
- All iteration tasks completed successfully\
- Project ready for next development phase' CHANGELOG.md
        rm -f CHANGELOG.md.tmp
    fi
    
    exit 0
else
    echo -e "${YELLOW}⏳ Tasks remaining. Continue with:${NC}"
    echo -e "   ${CYAN}make iterate${NC}       # Run next single task"
    echo -e "   ${CYAN}make iterate-loop${NC}  # Run continuously until all tasks complete"
    exit 1
fi
EOF

# Create the continuous loop script
cat > scripts/iterate-loop.sh << 'EOF'
#!/usr/bin/env bash
# Continuous iteration loop until all tasks are completed

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

ITERATION_COUNT=0
MAX_ITERATIONS=50  # Safety limit to prevent infinite loops

echo -e "${BLUE}🔄 Starting continuous iteration loop${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop at any time${NC}"
echo ""

# Trap Ctrl+C to show final status
trap 'echo -e "\n${YELLOW}🛑 Stopped by user${NC}"; ./scripts/check-complete.sh; exit 0' INT

while true; do
    ITERATION_COUNT=$((ITERATION_COUNT + 1))
    
    echo -e "${CYAN}🔄 Iteration #$ITERATION_COUNT${NC}"
    echo "=================================="
    
    # Check if we've hit the safety limit
    if [[ $ITERATION_COUNT -gt $MAX_ITERATIONS ]]; then
        echo -e "${RED}⚠️  Maximum iterations ($MAX_ITERATIONS) reached. Stopping for safety.${NC}"
        echo -e "${YELLOW}If tasks are still remaining, you may need to run 'make iterate' manually.${NC}"
        break
    fi
    
    # Check completion status first
    if ./scripts/check-complete.sh; then
        echo -e "${GREEN}🎉 All tasks completed! Loop finished successfully.${NC}"
        break
    fi
    
    echo ""
    echo -e "${CYAN}⚡ Running iteration...${NC}"
    
    # Run the iteration
    if make iterate; then
        echo -e "${GREEN}✅ Iteration #$ITERATION_COUNT completed successfully${NC}"
    else
        echo -e "${RED}❌ Iteration #$ITERATION_COUNT failed${NC}"
        echo -e "${YELLOW}⚠️  Stopping loop due to iteration failure${NC}"
        echo -e "${CYAN}💡 You may need to fix issues manually and run 'make iterate' again${NC}"
        break
    fi
    
    echo ""
    echo -e "${CYAN}📊 Current status:${NC}"
    ./scripts/check-complete.sh || true
    echo ""
    
    # Small delay between iterations
    sleep 2
done

echo ""
echo -e "${BLUE}🏁 Iteration loop finished${NC}"
echo -e "${CYAN}📊 Final status:${NC}"
./scripts/check-complete.sh || true
EOF

# Create the add-feature script
cat > scripts/add-feature.sh << 'EOF'
#!/usr/bin/env bash
# Add new feature/requirements to the project

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Add New Feature/Requirements${NC}"
echo ""

# Check if cursor-agent is available
if ! command -v cursor-agent >/dev/null 2>&1; then
    echo -e "${RED}❌ cursor-agent not found. Please install it first.${NC}"
    echo -e "${YELLOW}Run: curl https://cursor.com/install -fsS | bash${NC}"
    exit 1
fi

# Check if tasks.md exists
if [[ ! -f "tasks.md" ]]; then
    echo -e "${RED}❌ tasks.md not found. Run 'make iterate-init' first.${NC}"
    exit 1
fi

echo -e "${CYAN}📝 Please describe the new feature/requirements:${NC}"
echo -e "${YELLOW}(You can use multiple lines. Press Ctrl+D when finished)${NC}"
echo ""

# Read multiline input
FEATURE_DESCRIPTION=$(cat)

if [[ -z "$FEATURE_DESCRIPTION" ]]; then
    echo -e "${RED}❌ No feature description provided.${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}🔍 Analyzing current codebase and designing architecture...${NC}"

# Create a comprehensive prompt for feature analysis
FEATURE_PROMPT="
SYSTEM
You are a staff-level engineer tasked with adding a new feature to an existing project. Your job is to:

1. Analyze the current codebase structure and technology stack
2. Design the architecture for the new feature
3. Plan the integration with existing components
4. Create detailed implementation tasks
5. Identify testing requirements
6. Consider security, performance, and maintainability

NEW FEATURE REQUIREMENTS:
$FEATURE_DESCRIPTION

DELIVERABLES:
1. Update architecture.md with new feature design
2. Add comprehensive tasks to tasks.md for implementing this feature
3. Update test_plan.md with testing requirements
4. Add any new dependencies to decisions.md as ADRs

REQUIREMENTS:
- Analyze the existing codebase structure first
- Design the feature to integrate seamlessly with existing architecture
- Break down implementation into logical, testable tasks
- Include acceptance criteria for each task
- Consider edge cases and error handling
- Plan for testing (unit, integration, e2e as appropriate)
- Update documentation appropriately

CONTEXT:
Current repository structure, existing technologies, and current tasks are available in the control files.

USER
Please analyze the codebase and add the new feature: $FEATURE_DESCRIPTION

Design the architecture, create implementation tasks, and update all relevant control files.
"

echo -e "${CYAN}⚡ Generating feature architecture and tasks...${NC}"

# Run cursor-agent with the feature prompt
cursor-agent --print --force "$FEATURE_PROMPT"

echo ""
echo -e "${GREEN}✅ Feature added successfully!${NC}"
echo ""
echo -e "${CYAN}📋 Next Steps:${NC}"
echo -e "   1. ${YELLOW}make iterate-complete${NC}     # Check current task status"
echo -e "   2. ${YELLOW}make iterate-loop${NC}         # Run iterations until all tasks complete"
echo -e "   3. ${YELLOW}make archive-completed${NC}    # Archive completed tasks (optional)"
echo ""
echo -e "${CYAN}📚 Updated Files:${NC}"
echo -e "   - ${YELLOW}architecture.md${NC} - Updated with new feature design"
echo -e "   - ${YELLOW}tasks.md${NC} - Added new implementation tasks"
echo -e "   - ${YELLOW}test_plan.md${NC} - Updated with testing requirements"
echo -e "   - ${YELLOW}decisions.md${NC} - Added architectural decisions"
EOF

# Create the archive-completed script
cat > scripts/archive-completed.sh << 'EOF'
#!/usr/bin/env bash
# Archive completed tasks to keep tasks.md minimal

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Archiving Completed Tasks${NC}"
echo ""

# Check if tasks.md exists
if [[ ! -f "tasks.md" ]]; then
    echo -e "${RED}❌ tasks.md not found.${NC}"
    exit 1
fi

# Create completed_tasks directory if it doesn't exist
mkdir -p completed_tasks

# Get current date for archive file
ARCHIVE_DATE=$(date +"%Y-%m-%d_%H-%M-%S")
ARCHIVE_FILE="completed_tasks/completed_${ARCHIVE_DATE}.md"

# Count completed tasks
COMPLETED_TASKS=$(grep -c "^- \[x\]" tasks.md || echo "0")

if [[ $COMPLETED_TASKS -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  No completed tasks found to archive.${NC}"
    exit 0
fi

echo -e "${CYAN}📊 Found $COMPLETED_TASKS completed tasks to archive${NC}"

# Extract completed tasks
echo "# Completed Tasks - $ARCHIVE_DATE" > "$ARCHIVE_FILE"
echo "" >> "$ARCHIVE_FILE"
echo "Archived from tasks.md on $(date)" >> "$ARCHIVE_FILE"
echo "" >> "$ARCHIVE_FILE"
grep -A 20 "^- \[x\]" tasks.md >> "$ARCHIVE_FILE" || true

# Remove completed tasks from tasks.md
# This is more complex - we need to remove the completed task and all its content until the next task
TEMP_FILE=$(mktemp)

# Process tasks.md line by line
in_completed_task=false
task_content=()

while IFS= read -r line; do
    if [[ $line =~ ^- \[x\] ]]; then
        # Start of completed task
        in_completed_task=true
        task_content=("$line")
    elif [[ $line =~ ^- \[ \] ]] && [[ $in_completed_task == true ]]; then
        # Start of new incomplete task - end of completed task
        in_completed_task=false
        # Don't include this line in task_content, it belongs to the next task
    elif [[ $in_completed_task == true ]]; then
        # Part of completed task
        task_content+=("$line")
    else
        # Not part of a completed task
        if [[ $in_completed_task == false ]]; then
            echo "$line" >> "$TEMP_FILE"
        fi
    fi
done < tasks.md

# Handle case where the last task was completed
if [[ $in_completed_task == true ]]; then
    # Don't add anything to TEMP_FILE - the completed task is already archived
    true
fi

# Replace tasks.md with the filtered version
mv "$TEMP_FILE" tasks.md

echo -e "${GREEN}✅ Archived $COMPLETED_TASKS completed tasks to $ARCHIVE_FILE${NC}"
echo -e "${CYAN}📁 Archive location: completed_tasks/${NC}"

# Update progress.md
if [[ -f "progress.md" ]]; then
    echo "" >> progress.md
    echo "## 📦 Task Archive - $ARCHIVE_DATE" >> progress.md
    echo "- **Tasks Archived**: $COMPLETED_TASKS" >> progress.md
    echo "- **Archive File**: $ARCHIVE_FILE" >> progress.md
    echo "- **Reason**: Keep tasks.md focused on current work" >> progress.md
fi

# Show remaining tasks
REMAINING_TASKS=$(grep -c "^- \[ \]" tasks.md || echo "0")
echo -e "${CYAN}📊 Remaining tasks: $REMAINING_TASKS${NC}"
EOF

# Make the scripts executable
chmod +x scripts/check-complete.sh scripts/iterate-loop.sh scripts/add-feature.sh scripts/archive-completed.sh

# Check if Makefile exists, if not create one
# Note: If Makefile exists, we check for existing targets to avoid duplicates
# We also ensure all cursor-agent-iteration targets are present
if [[ ! -f "Makefile" ]]; then
    echo -e "${YELLOW}📝 Creating Makefile...${NC}"
    cat > Makefile << 'EOF'
# Makefile for Cursor Agent Iteration System

.PHONY: help iterate-init iterate iterate-complete iterate-loop add-feature archive-completed task-status

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
	@echo "  make iterate-loop    # Run iterations until all tasks complete"
	@echo "  make add-feature     # Add new feature/requirements"
	@echo "  make archive-completed # Archive completed tasks"
	@echo "  make iterate-complete # Check if all tasks are completed"
	@echo "  make task-status      # Show current task status and progress"

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


## iterate-complete: Check if all tasks are completed
iterate-complete:
	@echo "Checking completion status..."
	@./scripts/check-complete.sh

## iterate-loop: Run iterations until all tasks are completed
iterate-loop:
	@echo "Starting continuous iteration loop..."
	@echo "Press Ctrl+C to stop at any time"
	@./scripts/iterate-loop.sh

## add-feature: Add new feature/requirements to the project
add-feature:
	@echo "Adding new feature/requirements..."
	@./scripts/add-feature.sh

## archive-completed: Move completed tasks to archive
archive-completed:
	@echo "Archiving completed tasks..."
	@./scripts/archive-completed.sh
EOF
else
    echo -e "${CYAN}📝 Updating existing Makefile with cursor-agent-iteration targets...${NC}"
    
    # Define all cursor-agent-iteration targets
    CURSOR_TARGETS=("iterate-init" "iterate" "iterate-complete" "iterate-loop" "add-feature" "archive-completed" "task-status")
    
    # Check if any cursor-agent-iteration targets exist
    CURSOR_TARGETS_EXIST=false
    for target in "${CURSOR_TARGETS[@]}"; do
        if grep -q "## $target:" Makefile; then
            CURSOR_TARGETS_EXIST=true
            break
        fi
    done
    
    if [[ "$CURSOR_TARGETS_EXIST" == "true" ]]; then
        echo -e "${YELLOW}🔄 Found existing cursor-agent-iteration targets${NC}"
        echo -e "${CYAN}📝 Removing old targets and adding fresh ones...${NC}"
        
        # Create a backup
        cp Makefile Makefile.backup
        echo -e "${CYAN}📁 Created backup: Makefile.backup${NC}"
        
        # Remove existing cursor-agent-iteration targets using simple approach
        # Find the first cursor target line and remove everything from there to the end
        
        # Find the first cursor target line
        FIRST_CURSOR_LINE=$(grep -n "^## iterate-init:" Makefile | head -1 | cut -d: -f1)
        
        if [[ -n "$FIRST_CURSOR_LINE" ]]; then
            echo -e "${CYAN}🗑️  Found cursor targets starting at line $FIRST_CURSOR_LINE${NC}"
            
            # Remove everything from the first cursor target to the end
            head -n $((FIRST_CURSOR_LINE - 1)) Makefile > Makefile.temp
            mv Makefile.temp Makefile
            
            echo -e "${GREEN}✅ Removed cursor targets from line $FIRST_CURSOR_LINE onwards${NC}"
        else
            echo -e "${CYAN}ℹ️  No existing cursor targets found${NC}"
        fi
        
        echo -e "${GREEN}✅ Removed old cursor-agent-iteration targets${NC}"
    else
        echo -e "${CYAN}📝 No existing cursor-agent-iteration targets found${NC}"
    fi
    
    # Add fresh cursor-agent-iteration targets
    echo -e "${CYAN}📝 Adding fresh cursor-agent-iteration targets...${NC}"
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


## iterate-complete: Check if all tasks are completed
iterate-complete:
	@echo "Checking completion status..."
	@./scripts/check-complete.sh

## iterate-loop: Run iterations until all tasks are completed
iterate-loop:
	@echo "Starting continuous iteration loop..."
	@echo "Press Ctrl+C to stop at any time"
	@./scripts/iterate-loop.sh

## add-feature: Add new feature/requirements to the project
add-feature:
	@echo "Adding new feature/requirements..."
	@./scripts/add-feature.sh

## archive-completed: Move completed tasks to archive
archive-completed:
	@echo "Archiving completed tasks..."
	@./scripts/archive-completed.sh

## task-status: Show current task status and progress
task-status:
	@echo "📊 Task Status Overview"
	@echo "======================"
	@if [ -f "tasks.md" ]; then \
		echo ""; \
		echo "📋 Current Tasks:"; \
		echo "----------------"; \
		echo "✅ Completed tasks:"; \
		grep -c "^- \[x\]" tasks.md 2>/dev/null || echo "   0"; \
		echo "🔄 In-progress tasks:"; \
		grep -c "^- \[ \] 🔄" tasks.md 2>/dev/null || echo "   0"; \
		echo "⏳ Pending tasks:"; \
		grep -c "^- \[ \]" tasks.md 2>/dev/null || echo "   0"; \
		echo ""; \
		echo "📝 Task Details:"; \
		echo "---------------"; \
		grep "^# " tasks.md | head -5 || echo "   No tasks found"; \
		echo ""; \
		if grep -q "^- \[ \]" tasks.md; then \
			echo "🎯 Next Task:"; \
			grep -A 3 "^- \[ \]" tasks.md | head -4; \
		else \
			echo "🎉 All tasks completed!"; \
		fi; \
	else \
		echo "❌ No tasks.md found. Run 'make iterate-init' first."; \
	fi
EOF
    echo -e "${GREEN}✅ Added fresh cursor-agent-iteration targets to Makefile${NC}"
fi

# Note: Control files (architecture.md, decisions.md, test_plan.md, etc.) are created
# by 'make iterate-init' with project-specific analysis, not by bootstrap.sh
echo -e "${CYAN}📋 Control files are managed by 'make iterate-init' - preserving existing project analysis${NC}"

# Create comprehensive README
echo -e "${CYAN}📚 Creating documentation...${NC}"
cat > CURSOR_ITERATION_README.md << 'EOF'
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

# 2. Add features with proper architecture analysis
make add-feature

# 3. Check task status
make task-status

# 4. Start working on tasks
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
| `make help` | Show all available commands | `make help` |
| `make iterate-init` | Initialize and analyze repository | `make iterate-init` |
| `make add-feature` | Add new feature with architecture analysis | `make add-feature` |
| `make task-status` | Show current task status and progress | `make task-status` |
| `make iterate` | Run the next task | `make iterate` |
| `make iterate-loop` | Run iterations until all tasks complete | `make iterate-loop` |
| `make iterate-complete` | Check if all tasks are completed | `make iterate-complete` |
| `make archive-completed` | Archive completed tasks | `make archive-completed` |

## 🎯 How It Works

1. **Repository Analysis**: Detects languages, frameworks, and structure
2. **Feature Architecture**: Add features with proper codebase analysis and design
3. **Task Creation**: Creates realistic, technology-specific tasks from features
4. **Quality Gates**: Enforces appropriate standards for each detected stack
5. **Iteration Loop**: Runs Plan → Implement → Test → Validate → Document → Commit
6. **Progress Tracking**: Updates control files automatically

## 📁 Generated Files

After `make iterate-init`:
- `prompts/iterate.md` - Tailored iteration prompt
- `architecture.md` - System architecture documentation
- `progress.md` - Progress tracking and evidence
- `decisions.md` - Architectural Decision Records
- `test_plan.md` - Test coverage plans
- `qa_checklist.md` - Quality assurance checklist
- `CHANGELOG.md` - Conventional commits log

After `make add-feature`:
- `tasks.md` - Technology-specific task backlog (created from features)

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
make add-feature  # Add a new feature to trigger fresh analysis
```

## 📚 Examples

### Go Project
```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash
make iterate-init  # Detects Go, analyzes codebase
make add-feature   # Add features with Go-specific architecture
make iterate       # Runs Go quality gates (go vet, golangci-lint, go test)
```

### Rust Project
```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash
make iterate-init  # Detects Rust, analyzes codebase
make add-feature   # Add features with Rust-specific architecture
make iterate       # Runs Rust quality gates (cargo clippy, cargo test, cargo fmt)
```

### Infrastructure Project
```bash
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash
make iterate-init  # Detects Terraform/Ansible, analyzes codebase
make add-feature   # Add features with infrastructure architecture
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
echo -e "   - ${YELLOW}scripts/check-complete.sh${NC} - Completion checker"
echo -e "   - ${YELLOW}scripts/iterate-loop.sh${NC} - Continuous loop script"
echo -e "   - ${YELLOW}scripts/add-feature.sh${NC} - Feature addition script"
echo -e "   - ${YELLOW}scripts/archive-completed.sh${NC} - Task archiving script"
echo -e "   - ${YELLOW}Makefile${NC} - Updated with cursor-agent-iteration targets"
echo -e "   - ${YELLOW}CURSOR_ITERATION_README.md${NC} - Complete documentation"
echo ""
echo -e "${CYAN}📋 Control Files (created by 'make iterate-init'):${NC}"
echo -e "   - ${YELLOW}architecture.md${NC} - Architecture documentation"
echo -e "   - ${YELLOW}progress.md${NC} - Progress tracking"
echo -e "   - ${YELLOW}decisions.md${NC} - Architectural Decision Records"
echo -e "   - ${YELLOW}test_plan.md${NC} - Test coverage plans"
echo -e "   - ${YELLOW}qa_checklist.md${NC} - Quality assurance checklist"
echo -e "   - ${YELLOW}CHANGELOG.md${NC} - Conventional commits log"
echo -e "   - ${YELLOW}context.md${NC} - Project context"
echo ""
echo -e "${CYAN}📋 Next Steps:${NC}"
echo -e "   ${YELLOW}make help${NC}              # Show all available commands"
echo -e "   ${YELLOW}make iterate-init${NC}      # Initialize and analyze your repository"
echo -e "   ${YELLOW}make add-feature${NC}       # Add new feature/requirements (analyzes codebase first)"
echo -e "   ${YELLOW}make task-status${NC}       # Show current task status and progress"
echo -e "   ${YELLOW}make iterate${NC}           # Run the next task in the backlog"
echo -e "   ${YELLOW}make iterate-loop${NC}      # Run iterations until all tasks complete"
echo -e "   ${YELLOW}make iterate-complete${NC}  # Check if all tasks are completed"
echo -e "   ${YELLOW}make archive-completed${NC} # Archive completed tasks"
echo ""
echo -e "${CYAN}📚 Documentation:${NC}"
echo -e "   - Read ${YELLOW}CURSOR_ITERATION_README.md${NC} for detailed usage"
echo -e "   - Check ${YELLOW}prompts/iterate.md${NC} after initialization"
echo -e "   - Review ${YELLOW}tasks.md${NC} for your technology-specific task backlog"
echo ""
echo -e "${GREEN}🎉 Happy iterating!${NC}"