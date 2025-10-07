# Makefile for Cursor Agent Iteration System

.PHONY: help iterate-init iterate iterate-custom tasks-update iterate-complete iterate-loop add-feature archive-completed

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

## iterate-complete: Check if all tasks are completed
iterate-complete:
	@echo "Checking completion status..."
	@./scripts/check-complete.sh

## iterate-loop: Run iterations until all tasks are completed
iterate-loop:
	@echo "Starting continuous iteration loop..."
	@echo "Press Ctrl+C to stop at any time"
	@./scripts/iterate-loop.sh

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
