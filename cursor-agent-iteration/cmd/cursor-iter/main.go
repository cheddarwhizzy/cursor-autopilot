package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/cheddarwhizzy/cursor-autopilot/cursor-agent-iteration/internal/runner"
	"github.com/cheddarwhizzy/cursor-autopilot/cursor-agent-iteration/internal/tasks"
)

// Global mutex for file operations to prevent race conditions
var fileMutex sync.Mutex

// FileLock represents a file lock
type FileLock struct {
	file *os.File
}

// LockFile creates an exclusive lock on a file
func LockFile(filePath string) (*FileLock, error) {
	fileMutex.Lock()

	file, err := os.OpenFile(filePath, os.O_CREATE|os.O_RDWR, 0644)
	if err != nil {
		fileMutex.Unlock()
		return nil, fmt.Errorf("failed to open file %s: %v", filePath, err)
	}

	// Try to acquire exclusive lock
	err = syscall.Flock(int(file.Fd()), syscall.LOCK_EX|syscall.LOCK_NB)
	if err != nil {
		file.Close()
		fileMutex.Unlock()
		return nil, fmt.Errorf("failed to lock file %s: %v", filePath, err)
	}

	return &FileLock{file: file}, nil
}

// Unlock releases the file lock
func (fl *FileLock) Unlock() error {
	if fl.file != nil {
		syscall.Flock(int(fl.file.Fd()), syscall.LOCK_UN)
		err := fl.file.Close()
		fileMutex.Unlock()
		return err
	}
	fileMutex.Unlock()
	return nil
}

func usage() {
	fmt.Println("cursor-iter - task utilities")
	fmt.Println("Usage:")
	fmt.Println("  cursor-iter task-status   [--file tasks.md] [--progress progress.md]")
	fmt.Println("  cursor-iter archive-completed [--file tasks.md] [--progress progress.md] [--outdir completed_tasks]")
	fmt.Println("  cursor-iter iterate-init   [--model auto] [--codex]  # uses prompts/initialize-iteration-universal.md")
	fmt.Println("  cursor-iter iterate        [--max-in-progress 10]    # runs iteration using prompts/iterate.md")
	fmt.Println("  cursor-iter iterate-loop   [--codex] [--max-in-progress 10]  # loops until completion")
	fmt.Println("  cursor-iter add-feature                  # uses prompts/add-feature.md (DESIGN ONLY)")
	fmt.Println("  cursor-iter add-feature --file <path>    # read feature description from file")
	fmt.Println("  cursor-iter add-feature --prompt \"desc\"  # provide feature description as argument")
	fmt.Println("  cursor-iter add-feature [--codex]        # use codex instead of cursor-agent")
	fmt.Println("  cursor-iter run-agent --prompt \"request\" # send ad-hoc request to cursor-agent/codex")
	fmt.Println("  cursor-iter run-agent [--codex]          # use codex instead of cursor-agent")
	fmt.Println("  cursor-iter validate-tasks [--fix]       # validate/fix tasks.md structure")
	fmt.Println("  cursor-iter reset                       # remove all control files")
	fmt.Println("")
	fmt.Println("Options:")
	fmt.Println("  --codex              Use codex CLI with gpt-5-codex model instead of cursor-agent")
	fmt.Println("  --model              Specify model for cursor-agent (auto, gpt-4o, etc.) or codex (gpt-5-codex)")
	fmt.Println("  --max-in-progress N  Maximum number of in-progress tasks allowed (default: 10)")
	fmt.Println("")
	fmt.Println("Task Workflow:")
	fmt.Println("  tasks.md     - Master task list (add-feature adds tasks here)")
	fmt.Println("  progress.md  - Completion log (iterate-loop updates when tasks complete)")
	fmt.Println("  NOTE: This separation prevents write conflicts when adding features during iterate-loop")
	fmt.Println("")
	fmt.Println("Task Continuation:")
	fmt.Println("  iterate-loop now continues working on in-progress tasks until completion")
	fmt.Println("  If a task doesn't complete in one iteration, it will retry on the next iteration")
	fmt.Println("  Use --max-in-progress to limit concurrent task processing")
}

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(1)
	}
	cmd := os.Args[1]
	debug := envOr("DEBUG", "") != "" // DEBUG=1 enables verbose mode
	switch cmd {
	case "task-status":
		fs := flag.NewFlagSet("task-status", flag.ExitOnError)
		file := fs.String("file", resolveTasksFile(), "tasks file")
		progressFile := fs.String("progress", resolveProgressFile(), "progress file")
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])
		if *dbg {
			fmt.Printf("[%s] task-status reading %s and %s\n", ts(), *file, *progressFile)
		}

		// Read tasks.md
		taskContent, err := os.ReadFile(*file)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error reading %s: %v\n", *file, err)
			os.Exit(1)
		}

		// Read progress.md (create if doesn't exist)
		progressContent, err := os.ReadFile(*progressFile)
		if err != nil {
			// If progress.md doesn't exist, create an empty one
			progressContent = []byte("# Progress Log\n\n## Completed Tasks\n\n")
		}

		report := tasks.StatusReportWithProgress(string(taskContent), string(progressContent))
		fmt.Println(report)
	case "validate-tasks":
		fs := flag.NewFlagSet("validate-tasks", flag.ExitOnError)
		file := fs.String("file", resolveTasksFile(), "tasks file")
		fix := fs.Bool("fix", false, "attempt to fix structure issues")
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])
		if *dbg {
			fmt.Printf("[%s] validate-tasks reading %s\n", ts(), *file)
		}
		content, err := os.ReadFile(*file)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error reading %s: %v\n", *file, err)
			os.Exit(1)
		}

		if *fix {
			fixedContent, result := tasks.ValidateAndFixTasksStructure(string(content))
			if !result.Valid {
				fmt.Fprintf(os.Stderr, "Structure validation failed:\n")
				for _, err := range result.Errors {
					fmt.Fprintf(os.Stderr, "  ERROR: %s\n", err)
				}
				os.Exit(1)
			}
			if len(result.Warnings) > 0 {
				fmt.Printf("Warnings:\n")
				for _, warning := range result.Warnings {
					fmt.Printf("  WARNING: %s\n", warning)
				}
			}
			if err := os.WriteFile(*file, []byte(fixedContent), 0644); err != nil {
				fmt.Fprintf(os.Stderr, "error writing fixed content: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("✅ Fixed tasks.md structure\n")
		} else {
			result := tasks.ValidateTasksStructure(string(content))
			if result.Valid {
				fmt.Printf("✅ tasks.md structure is valid\n")
			} else {
				fmt.Fprintf(os.Stderr, "❌ Structure validation failed:\n")
				for _, err := range result.Errors {
					fmt.Fprintf(os.Stderr, "  ERROR: %s\n", err)
				}
				os.Exit(1)
			}
			if len(result.Warnings) > 0 {
				fmt.Printf("Warnings:\n")
				for _, warning := range result.Warnings {
					fmt.Printf("  WARNING: %s\n", warning)
				}
			}
		}
	case "archive-completed":
		fs := flag.NewFlagSet("archive-completed", flag.ExitOnError)
		file := fs.String("file", resolveTasksFile(), "tasks file")
		progressFile := fs.String("progress", resolveProgressFile(), "progress file")
		outdir := fs.String("outdir", "completed_tasks", "archive directory")
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])
		if *dbg {
			fmt.Printf("[%s] archiving completed from %s and %s to %s\n", ts(), *file, *progressFile, *outdir)
		}

		// Read tasks.md
		taskContent, err := os.ReadFile(*file)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error reading %s: %v\n", *file, err)
			os.Exit(1)
		}

		// Read progress.md
		progressContent, readErr := os.ReadFile(*progressFile)
		if readErr != nil {
			fmt.Fprintf(os.Stderr, "error reading %s: %v\n", *progressFile, readErr)
			os.Exit(1)
		}

		// Archive completed tasks
		// 1. Move completed tasks from progress.md to archive file
		// 2. Remove completed tasks from tasks.md
		archived, remainingProgress, updatedTasks, archiveFile, err := tasks.ArchiveCompletedTasks(
			string(taskContent),
			string(progressContent),
			*outdir,
		)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error archiving: %v\n", err)
			os.Exit(1)
		}

		// Update tasks.md (remove completed tasks)
		if err := os.WriteFile(*file, []byte(updatedTasks), 0644); err != nil {
			fmt.Fprintf(os.Stderr, "error writing tasks: %v\n", err)
			os.Exit(1)
		}

		// Update progress.md (remove completed tasks, keep in-progress)
		if err := os.WriteFile(*progressFile, []byte(remainingProgress), 0644); err != nil {
			fmt.Fprintf(os.Stderr, "error writing progress: %v\n", err)
			os.Exit(1)
		}

		// Write archive file
		if err := os.WriteFile(archiveFile, []byte(archived), 0644); err != nil {
			fmt.Fprintf(os.Stderr, "error writing archive: %v\n", err)
			os.Exit(1)
		}

		fmt.Printf("✅ Archived completed tasks to %s\n", archiveFile)
		fmt.Printf("✅ Removed completed tasks from tasks.md\n")
		fmt.Printf("✅ Removed completed tasks from progress.md (kept in-progress tasks)\n")
	case "iterate-init":
		fs := flag.NewFlagSet("iterate-init", flag.ExitOnError)
		model := fs.String("model", envOr("MODEL", "auto"), "cursor-agent model or codex model (gpt-5-codex)")
		useCodex := fs.Bool("codex", false, "use codex CLI with gpt-5-codex model")
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])
		promptFile := "./prompts/initialize-iteration-universal.md"

		// Try to fetch from GitHub if not present locally
		if err := fetchPromptFromGitHub(promptFile); err != nil {
			fmt.Fprintf(os.Stderr, "failed to fetch prompt: %v\n", err)
			os.Exit(1)
		}

		data, err := os.ReadFile(promptFile)
		if err != nil {
			fmt.Fprintf(os.Stderr, "missing prompt %s: %v\n", promptFile, err)
			os.Exit(1)
		}

		// Set default model for codex if not specified
		agentModel := *model
		if *useCodex && *model == "auto" {
			agentModel = "gpt-5-codex"
		}

		if *dbg {
			if *useCodex {
				fmt.Printf("[%s] iterate-init using codex model=%s, prompt=%s\n", ts(), agentModel, promptFile)
			} else {
				fmt.Printf("[%s] iterate-init using cursor-agent model=%s, prompt=%s\n", ts(), agentModel, promptFile)
			}
		}

		if *useCodex {
			if err := runner.CodexWithDebug(*dbg, agentModel, string(data)); err != nil {
				os.Exit(1)
			}
		} else {
			if err := runner.CursorAgentWithDebug(*dbg, "--print", "--force", "--model", agentModel, string(data)); err != nil {
				os.Exit(1)
			}
		}
	case "iterate":
		fs := flag.NewFlagSet("iterate", flag.ExitOnError)
		useCodex := fs.Bool("codex", false, "use codex CLI with gpt-5-codex model")
		model := fs.String("model", envOr("MODEL", "auto"), "cursor-agent model or codex model (gpt-5-codex)")
		maxInProgress := fs.Int("max-in-progress", 10, "maximum number of in-progress tasks allowed")
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])

		// Run the main iteration based on prompts/iterate.md
		file := resolveTasksFile()
		progressFile := resolveProgressFile()

		// Acquire file lock before running iteration
		lock, err := LockFile(file)
		if err != nil {
			fmt.Fprintf(os.Stderr, "[%s] ⚠️ Could not acquire file lock: %v\n", ts(), err)
			fmt.Fprintf(os.Stderr, "[%s] 💡 Another process may be modifying tasks.md. Please try again later.\n", ts())
			os.Exit(1)
		}

		if *dbg {
			fmt.Printf("[%s] ✅ Acquired file lock successfully - safe to proceed\n", ts())
		}

		// Read tasks.md and progress.md
		if *dbg {
			fmt.Printf("[%s] 📖 Reading tasks from: %s\n", ts(), file)
		}
		b, err := os.ReadFile(file)
		if err != nil {
			lock.Unlock()
			fmt.Fprintf(os.Stderr, "error reading tasks file: %v\n", err)
			os.Exit(1)
		}
		taskContent := string(b)
		if *dbg {
			fmt.Printf("[%s] ✅ Successfully read tasks.md (%d bytes)\n", ts(), len(b))
		}

		if *dbg {
			fmt.Printf("[%s] 📖 Reading progress from: %s\n", ts(), progressFile)
		}
		progressContent, err := os.ReadFile(progressFile)
		if err != nil {
			// If progress.md doesn't exist, create an empty one
			progressContent = []byte("# Progress Log\n\n## Completed Tasks\n\n")
			os.WriteFile(progressFile, progressContent, 0644)
			if *dbg {
				fmt.Printf("[%s] 📝 Created new progress.md file\n", ts())
			}
		} else {
			if *dbg {
				fmt.Printf("[%s] ✅ Successfully read progress.md (%d bytes)\n", ts(), len(progressContent))
			}
		}
		progressStr := string(progressContent)

		// Get current in-progress tasks
		if *dbg {
			fmt.Printf("[%s] 🔍 Checking for in-progress tasks...\n", ts())
		}
		inProgressTasks := tasks.GetAllInProgressTasks(taskContent, progressStr)
		inProgressCount := len(inProgressTasks)
		if *dbg {
			fmt.Printf("[%s] 📊 Found %d in-progress tasks (max allowed: %d)\n", ts(), inProgressCount, *maxInProgress)
		}

		var currentTask *tasks.Task
		var taskToWork string

		// First, check if there's an existing in-progress task
		if len(inProgressTasks) > 0 {
			// Continue working on the first in-progress task
			currentTask = inProgressTasks[0]
			taskToWork = currentTask.Title
			if *dbg {
				fmt.Printf("[%s] 🎯 Selected in-progress task to continue: '%s'\n", ts(), taskToWork)
			}
			fmt.Printf("[%s] 🔄 Continuing in-progress task: '%s' (%d/%d criteria)\n",
				ts(), currentTask.Title, currentTask.ACChecked, currentTask.ACTotal)
		} else if inProgressCount < *maxInProgress {
			// Only start a new task if we're under the max in-progress limit
			if *dbg {
				fmt.Printf("[%s] 🔍 Looking for next pending task...\n", ts())
			}
			nextTask := tasks.GetNextPendingTaskWithProgress(taskContent, progressStr)
			if nextTask != nil {
				if *dbg {
					fmt.Printf("[%s] 🎯 Found next pending task: '%s'\n", ts(), nextTask.Title)
					fmt.Printf("[%s] 📝 Marking task as in-progress in progress.md...\n", ts())
				}
				// Mark task as in-progress in progress.md (not tasks.md)
				updatedProgress := tasks.MarkTaskInProgress(progressStr, nextTask.Title)

				// Write the updated progress.md
				if err := os.WriteFile(progressFile, []byte(updatedProgress), 0644); err != nil {
					lock.Unlock()
					fmt.Fprintf(os.Stderr, "[%s] ⚠️ Warning: could not update progress: %v\n", ts(), err)
					os.Exit(1)
				} else {
					if *dbg {
						fmt.Printf("[%s] ✅ Successfully marked task as in-progress in progress.md\n", ts())
					}
					progressStr = updatedProgress // Update local copy
					currentTask = nextTask
					taskToWork = nextTask.Title
					fmt.Printf("[%s] 📝 Started new task: '%s'\n", ts(), nextTask.Title)
				}
			} else if *dbg {
				fmt.Printf("[%s] ℹ️ No pending tasks found\n", ts())
			}
		} else {
			lock.Unlock()
			fmt.Fprintf(os.Stderr, "[%s] ⚠️ Max in-progress tasks (%d) reached. Cannot start new task.\n", ts(), *maxInProgress)
			fmt.Fprintf(os.Stderr, "[%s] 💡 Complete existing in-progress tasks before starting new ones.\n", ts())
			os.Exit(1)
		}

		if currentTask == nil {
			lock.Unlock()
			fmt.Fprintf(os.Stderr, "[%s] ⚠️ No tasks available to work on\n", ts())
			os.Exit(1)
		}

		// Extract the full task details from tasks.md
		if *dbg {
			fmt.Printf("[%s] 📋 Extracting full task details from tasks.md...\n", ts())
		}
		taskDetails := tasks.ExtractTaskDetails(taskContent, taskToWork)
		if *dbg {
			fmt.Printf("[%s] ✅ Task details extracted (%d bytes)\n", ts(), len(taskDetails))
		}

		// Build the prompt with the specific task and control file references
		if *dbg {
			fmt.Printf("[%s] 📝 Building prompt for cursor-agent...\n", ts())
		}
		msg := fmt.Sprintf(`You are working on a specific task from the engineering iteration system.

## Your Task

%s

## Instructions

1. Review the control files for context:
   - architecture.md: System architecture and design
   - decisions.md: Architectural Decision Records (ADRs)
   - progress.md: Completed tasks and progress history
   - test_plan.md: Testing strategy and coverage
   - qa_checklist.md: Quality assurance requirements
   - CHANGELOG.md: Change history
   - context.md: Project context (if available)

2. Implement the task following these steps:
   - Plan your implementation approach
   - Write the code with comprehensive logging and comments
   - Create/update tests to verify functionality
   - Run quality gates (linting, formatting, type checking, tests)
   - Update documentation as needed
   - Commit changes with conventional commit messages

3. Track progress:
   - Check off each acceptance criterion in tasks.md as you complete it
   - When ALL criteria are checked, move the task from "## In Progress" to "## Completed Tasks" in progress.md
   - Use format: "- ✅ [YYYY-MM-DD HH:MM] Task Title - completion notes"

4. Quality Requirements:
   - All tests must pass
   - Code must pass linting and formatting checks
   - Follow existing code patterns and conventions
   - Add detailed code comments explaining complex logic
   - Include logging for debugging and monitoring

## Important Notes

- Focus ONLY on this specific task
- tasks.md is a simple task list (no status emojis) - only check off acceptance criteria
- progress.md tracks task status (in-progress and completed)
- When all acceptance criteria are checked, move this task from "## In Progress" to "## Completed Tasks" in progress.md
- Ensure all quality gates pass before marking complete

Work on this task until all acceptance criteria are checked off and the task is moved to completed in progress.md.`, taskDetails)

		// Set default model for codex if not specified
		agentModel := *model
		if *useCodex && *model == "auto" {
			agentModel = "gpt-5-codex"
		}

		// Release lock before running cursor-agent (it will run for a while)
		lock.Unlock()
		if *dbg {
			fmt.Printf("[%s] 🔓 Released file lock before running cursor-agent\n", ts())
		}

		// Log which task is about to be sent to cursor-agent
		fmt.Printf("[%s] 🚀 Sending task to cursor-agent: '%s'\n", ts(), taskToWork)
		if *dbg {
			if *useCodex {
				fmt.Printf("[%s] 🤖 Using codex (model: %s)\n", ts(), agentModel)
			} else {
				fmt.Printf("[%s] 🤖 Using cursor-agent (model: %s)\n", ts(), agentModel)
			}
			fmt.Printf("[%s] 📊 Task progress: %d/%d acceptance criteria completed\n", ts(), currentTask.ACChecked, currentTask.ACTotal)
		}

		// Run cursor-agent
		var agentErr error
		if *useCodex {
			agentErr = runner.CodexWithDebug(*dbg, agentModel, msg)
		} else {
			agentErr = runner.CursorAgentWithDebug(*dbg, "--print", "--force", msg)
		}

		if agentErr != nil {
			fmt.Fprintf(os.Stderr, "[%s] ⚠️ Iteration failed: %v\n", ts(), agentErr)
			os.Exit(1)
		}

		// Check if the task is now complete
		if *dbg {
			fmt.Printf("[%s] 🔍 Rechecking task status after cursor-agent completion...\n", ts())
			fmt.Printf("[%s] 📖 Re-reading tasks.md to check for updates...\n", ts())
		}
		b2, err := os.ReadFile(file)
		if err == nil {
			if *dbg {
				fmt.Printf("[%s] ✅ Re-read tasks.md (%d bytes)\n", ts(), len(b2))
				fmt.Printf("[%s] 📖 Re-reading progress.md to check for completion status...\n", ts())
			}
			progressContent2, _ := os.ReadFile(progressFile)
			if *dbg && progressContent2 != nil {
				fmt.Printf("[%s] ✅ Re-read progress.md (%d bytes)\n", ts(), len(progressContent2))
			}
			newTaskContent := string(b2)
			newProgressStr := string(progressContent2)

			if *dbg {
				fmt.Printf("[%s] 🔍 Checking if task '%s' is now marked as completed...\n", ts(), taskToWork)
			}
			taskCompleted := tasks.IsTaskCompletedAfterRun(newTaskContent, newProgressStr, taskToWork)

			if taskCompleted {
				fmt.Printf("[%s] ✅ Task completed: %s\n", ts(), taskToWork)
			} else {
				fmt.Printf("[%s] ⚠️ Task not yet complete: %s - run 'iterate' again to continue\n", ts(), taskToWork)
				if *dbg {
					fmt.Printf("[%s] 💡 Task will be retried on next iteration\n", ts())
				}
			}

			// Show updated progress
			newProgress := tasks.GetTaskProgressWithProgress(newTaskContent, newProgressStr)
			fmt.Printf("[%s] 📊 Updated progress: %s\n", ts(), newProgress)
		} else if *dbg {
			fmt.Printf("[%s] ⚠️ Could not re-read files after cursor-agent: %v\n", ts(), err)
		}
	case "iterate-loop":
		fs := flag.NewFlagSet("iterate-loop", flag.ExitOnError)
		useCodex := fs.Bool("codex", false, "use codex CLI with gpt-5-codex model")
		model := fs.String("model", envOr("MODEL", "auto"), "cursor-agent model or codex model (gpt-5-codex)")
		maxInProgress := fs.Int("max-in-progress", 10, "maximum number of in-progress tasks allowed")
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])

		// Minimal loop invoking iterate until tasks are complete
		file := resolveTasksFile()
		progressFile := resolveProgressFile()

		// Set default model for codex if not specified
		agentModel := *model
		if *useCodex && *model == "auto" {
			agentModel = "gpt-5-codex"
		}

		fmt.Printf("[%s] 🚀 Starting iterate-loop (max in-progress: %d)\n", ts(), *maxInProgress)

		for i := 1; i <= 50; i++ { // safety cap
			// Acquire file lock before reading tasks
			lock, err := LockFile(file)
			if err != nil {
				fmt.Fprintf(os.Stderr, "[%s] ⚠️ Could not acquire file lock: %v\n", ts(), err)
				fmt.Fprintf(os.Stderr, "[%s] 💡 Another process may be modifying tasks.md. Retrying...\n", ts())
				time.Sleep(2 * time.Second)
				continue
			}

			if *dbg {
				fmt.Printf("[%s] ✅ Acquired file lock successfully - safe to proceed\n", ts())
			}

			// Read tasks.md
			if *dbg {
				fmt.Printf("[%s] 📖 Reading tasks from: %s\n", ts(), file)
			}
			b, err := os.ReadFile(file)
			if err != nil {
				lock.Unlock()
				fmt.Fprintf(os.Stderr, "error reading tasks file: %v\n", err)
				os.Exit(1)
			}
			taskContent := string(b)
			if *dbg {
				fmt.Printf("[%s] ✅ Successfully read tasks.md (%d bytes)\n", ts(), len(b))
			}

			// Read progress.md (create if doesn't exist)
			if *dbg {
				fmt.Printf("[%s] 📖 Reading progress from: %s\n", ts(), progressFile)
			}
			progressContent, err := os.ReadFile(progressFile)
			if err != nil {
				// If progress.md doesn't exist, create an empty one
				progressContent = []byte("# Progress Log\n\n## Completed Tasks\n\n")
				os.WriteFile(progressFile, progressContent, 0644)
				if *dbg {
					fmt.Printf("[%s] 📝 Created new progress.md file\n", ts())
				}
			} else {
				if *dbg {
					fmt.Printf("[%s] ✅ Successfully read progress.md (%d bytes)\n", ts(), len(progressContent))
				}
			}
			progressStr := string(progressContent)

			// Check if all tasks are complete using progress.md
			if tasks.CompleteAllChecked(taskContent, progressStr) {
				lock.Unlock()
				fmt.Printf("[%s] ✅ All tasks completed successfully!\n", ts())
				return
			}

			// Show current progress using both files
			progress := tasks.GetTaskProgressWithProgress(taskContent, progressStr)
			fmt.Printf("[%s] Iteration #%d - %s\n", ts(), i, progress)

			// Get current in-progress tasks
			if *dbg {
				fmt.Printf("[%s] 🔍 Checking for in-progress tasks...\n", ts())
			}
			inProgressTasks := tasks.GetAllInProgressTasks(taskContent, progressStr)
			inProgressCount := len(inProgressTasks)

			if *dbg {
				fmt.Printf("[%s] 📊 Found %d in-progress tasks (max allowed: %d)\n", ts(), inProgressCount, *maxInProgress)
			}

			var currentTask *tasks.Task
			var taskToWork string

			// First, check if there's an existing in-progress task
			if len(inProgressTasks) > 0 {
				// Continue working on the first in-progress task
				currentTask = inProgressTasks[0]
				taskToWork = currentTask.Title
				if *dbg {
					fmt.Printf("[%s] 🎯 Selected in-progress task to continue: '%s'\n", ts(), taskToWork)
				}
				fmt.Printf("[%s] 🔄 Continuing in-progress task: '%s' (%d/%d criteria)\n",
					ts(), currentTask.Title, currentTask.ACChecked, currentTask.ACTotal)
			} else if inProgressCount < *maxInProgress {
				// Only start a new task if we're under the max in-progress limit
				if *dbg {
					fmt.Printf("[%s] 🔍 Looking for next pending task...\n", ts())
				}
				nextTask := tasks.GetNextPendingTaskWithProgress(taskContent, progressStr)
				if nextTask != nil {
					if *dbg {
						fmt.Printf("[%s] 🎯 Found next pending task: '%s'\n", ts(), nextTask.Title)
						fmt.Printf("[%s] 📝 Marking task as in-progress in progress.md...\n", ts())
					}
					// Mark task as in-progress in progress.md (not tasks.md)
					updatedProgress := tasks.MarkTaskInProgress(progressStr, nextTask.Title)

					// Write the updated progress.md
					if err := os.WriteFile(progressFile, []byte(updatedProgress), 0644); err != nil {
						lock.Unlock()
						fmt.Fprintf(os.Stderr, "[%s] ⚠️ Warning: could not update progress: %v\n", ts(), err)
					} else {
						if *dbg {
							fmt.Printf("[%s] ✅ Successfully marked task as in-progress in progress.md\n", ts())
						}
						progressStr = updatedProgress // Update local copy
						currentTask = nextTask
						taskToWork = nextTask.Title
						fmt.Printf("[%s] 📝 Started new task: '%s'\n", ts(), nextTask.Title)
					}
				} else if *dbg {
					fmt.Printf("[%s] ℹ️ No pending tasks found\n", ts())
				}
			} else {
				lock.Unlock()
				fmt.Fprintf(os.Stderr, "[%s] ⚠️ Max in-progress tasks (%d) reached. Cannot start new task.\n", ts(), *maxInProgress)
				fmt.Fprintf(os.Stderr, "[%s] 💡 Waiting for in-progress tasks to complete...\n", ts())
				time.Sleep(5 * time.Second)
				continue
			}

			if currentTask == nil {
				lock.Unlock()
				fmt.Fprintf(os.Stderr, "[%s] ⚠️ No tasks available to work on\n", ts())
				break
			}

			fmt.Printf("[%s] 🔄 Starting iteration for task: %s\n", ts(), taskToWork)

			// Extract the full task details from tasks.md
			if *dbg {
				fmt.Printf("[%s] 📋 Extracting full task details from tasks.md...\n", ts())
			}
			taskDetails := tasks.ExtractTaskDetails(taskContent, taskToWork)
			if *dbg {
				fmt.Printf("[%s] ✅ Task details extracted (%d bytes)\n", ts(), len(taskDetails))
			}

			// Build the prompt with the specific task and control file references
			if *dbg {
				fmt.Printf("[%s] 📝 Building prompt for cursor-agent...\n", ts())
			}
			msg := fmt.Sprintf(`You are working on a specific task from the engineering iteration system.

## Your Task

%s

## Instructions

1. Review the control files for context:
   - architecture.md: System architecture and design
   - decisions.md: Architectural Decision Records (ADRs)
   - progress.md: Completed tasks and progress history
   - test_plan.md: Testing strategy and coverage
   - qa_checklist.md: Quality assurance requirements
   - CHANGELOG.md: Change history
   - context.md: Project context (if available)

2. Implement the task following these steps:
   - Plan your implementation approach
   - Write the code with comprehensive logging and comments
   - Create/update tests to verify functionality
   - Run quality gates (linting, formatting, type checking, tests)
   - Update documentation as needed
   - Commit changes with conventional commit messages

3. Track progress:
   - Check off each acceptance criterion in tasks.md as you complete it
   - When ALL criteria are checked, move the task from "## In Progress" to "## Completed Tasks" in progress.md
   - Use format: "- ✅ [YYYY-MM-DD HH:MM] Task Title - completion notes"

4. Quality Requirements:
   - All tests must pass
   - Code must pass linting and formatting checks
   - Follow existing code patterns and conventions
   - Add detailed code comments explaining complex logic
   - Include logging for debugging and monitoring

## Important Notes

- Focus ONLY on this specific task
- tasks.md is a simple task list (no status emojis) - only check off acceptance criteria
- progress.md tracks task status (in-progress and completed)
- When all acceptance criteria are checked, move this task from "## In Progress" to "## Completed Tasks" in progress.md
- Ensure all quality gates pass before marking complete

Work on this task until all acceptance criteria are checked off and the task is moved to completed in progress.md.`, taskDetails)

			// Release lock before running cursor-agent (it will run for a while)
			lock.Unlock()
			if *dbg {
				fmt.Printf("[%s] 🔓 Released file lock before running cursor-agent\n", ts())
			}

			// Log which task is about to be sent to cursor-agent
			fmt.Printf("[%s] 🚀 Sending task to cursor-agent: '%s'\n", ts(), taskToWork)
			if *dbg {
				if *useCodex {
					fmt.Printf("[%s] 🤖 Using codex (model: %s)\n", ts(), agentModel)
				} else {
					fmt.Printf("[%s] 🤖 Using cursor-agent (model: %s)\n", ts(), agentModel)
				}
				fmt.Printf("[%s] 📊 Task progress: %d/%d acceptance criteria completed\n", ts(), currentTask.ACChecked, currentTask.ACTotal)
			}

			// Run cursor-agent
			var agentErr error
			if *useCodex {
				agentErr = runner.CodexWithDebug(*dbg, agentModel, msg)
			} else {
				agentErr = runner.CursorAgentWithDebug(*dbg, "--print", "--force", msg)
			}

			if agentErr != nil {
				fmt.Fprintf(os.Stderr, "[%s] ⚠️ Iteration failed: %v\n", ts(), agentErr)
				fmt.Fprintf(os.Stderr, "[%s] 💡 Will retry on next iteration...\n", ts())
				time.Sleep(2 * time.Second)
				continue
			}

			// Check if the task is now complete
			if *dbg {
				fmt.Printf("[%s] 🔍 Rechecking task status after cursor-agent completion...\n", ts())
				fmt.Printf("[%s] 📖 Re-reading tasks.md to check for updates...\n", ts())
			}
			b2, err := os.ReadFile(file)
			if err != nil {
				fmt.Fprintf(os.Stderr, "[%s] ⚠️ Could not read tasks file: %v\n", ts(), err)
				continue
			}
			if *dbg {
				fmt.Printf("[%s] ✅ Re-read tasks.md (%d bytes)\n", ts(), len(b2))
				fmt.Printf("[%s] 📖 Re-reading progress.md to check for completion status...\n", ts())
			}
			progressContent2, _ := os.ReadFile(progressFile)
			if *dbg && progressContent2 != nil {
				fmt.Printf("[%s] ✅ Re-read progress.md (%d bytes)\n", ts(), len(progressContent2))
			}
			newTaskContent := string(b2)
			newProgressStr := string(progressContent2)

			if *dbg {
				fmt.Printf("[%s] 🔍 Checking if task '%s' is now marked as completed...\n", ts(), taskToWork)
			}
			taskCompleted := tasks.IsTaskCompletedAfterRun(newTaskContent, newProgressStr, taskToWork)

			if taskCompleted {
				fmt.Printf("[%s] ✅ Task completed: %s\n", ts(), taskToWork)
			} else {
				fmt.Printf("[%s] ⚠️ Task not yet complete: %s - will retry on next iteration\n", ts(), taskToWork)
				if *dbg {
					fmt.Printf("[%s] 💡 Task remains in-progress and will be retried\n", ts())
				}
			}

			// Show updated progress
			newProgress := tasks.GetTaskProgressWithProgress(newTaskContent, newProgressStr)
			fmt.Printf("[%s] 📊 Updated progress: %s\n", ts(), newProgress)

			// Small delay between iterations
			time.Sleep(2 * time.Second)
		}
		fmt.Printf("[%s] ⚠️ Reached max iterations (%d) without completion\n", ts(), 50)
	case "add-feature":
		fs := flag.NewFlagSet("add-feature", flag.ExitOnError)
		file := fs.String("file", "", "read feature description from file")
		prompt := fs.String("prompt", "", "provide feature description as command line argument")
		useCodex := fs.Bool("codex", false, "use codex CLI with gpt-5-codex model")
		model := fs.String("model", envOr("MODEL", "auto"), "cursor-agent model or codex model (gpt-5-codex)")
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])

		promptFile := "./prompts/add-feature.md"

		// Try to fetch from GitHub if not present locally
		if fetchErr := fetchPromptFromGitHub(promptFile); fetchErr != nil {
			fmt.Fprintf(os.Stderr, "failed to fetch prompt: %v\n", fetchErr)
			os.Exit(1)
		}

		data, readErr := os.ReadFile(promptFile)
		if readErr != nil {
			fmt.Fprintf(os.Stderr, "missing prompt %s: %v\n", promptFile, readErr)
			os.Exit(1)
		}

		var featureDesc string

		// Check if feature description is provided via --prompt flag
		if *prompt != "" {
			featureDesc = *prompt
			fmt.Printf("✅ Using feature description from --prompt flag (%d characters)\n", len(featureDesc))
		} else if *file != "" {
			// Read from file
			fileData, err := os.ReadFile(*file)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error reading file %s: %v\n", *file, err)
				os.Exit(1)
			}
			featureDesc = string(fileData)
			fmt.Printf("✅ Loaded feature description from %s (%d characters)\n", *file, len(featureDesc))
		} else {
			// Interactive input
			fmt.Print("Enter feature description (press Enter twice when done):\n")
			fmt.Print("Tip: For long descriptions, you can paste multi-line text. Press Enter twice to finish.\n")
			fmt.Print("Alternative: Use --file <path> to read from a file or --prompt \"description\"\n")

			scanner := bufio.NewScanner(os.Stdin)
			var lines []string
			emptyLineCount := 0
			lineCount := 0

			for scanner.Scan() {
				line := scanner.Text()
				lineCount++

				// Show progress every 10 lines for long inputs
				if lineCount%10 == 0 {
					fmt.Printf("... %d lines entered (press Enter twice to finish)\n", lineCount)
				}

				if line == "" {
					emptyLineCount++
					if emptyLineCount >= 2 {
						break
					}
					lines = append(lines, line)
				} else {
					emptyLineCount = 0
					lines = append(lines, line)
				}
			}

			if err := scanner.Err(); err != nil {
				fmt.Fprintf(os.Stderr, "Error reading input: %v\n", err)
				os.Exit(1)
			}

			featureDesc = strings.Join(lines, "\n")

			// Validate input
			if len(strings.TrimSpace(featureDesc)) == 0 {
				fmt.Fprintf(os.Stderr, "Error: Feature description cannot be empty\n")
				os.Exit(1)
			}

			fmt.Printf("✅ Received %d lines of feature description\n", lineCount)
		}

		// Replace placeholder with user input
		promptContent := strings.ReplaceAll(string(data), "{{FEATURE_DESCRIPTION}}", featureDesc)

		// Set default model for codex if not specified
		agentModel := *model
		if *useCodex && *model == "auto" {
			agentModel = "gpt-5-codex"
		}

		fmt.Printf("[%s] Analyzing feature and creating architecture/tasks...\n", ts())
		if *dbg {
			if *useCodex {
				fmt.Printf("[%s] add-feature using codex model=%s, prompt=%s with feature: %s\n", ts(), agentModel, promptFile, featureDesc)
			} else {
				fmt.Printf("[%s] add-feature using cursor-agent model=%s, prompt=%s with feature: %s\n", ts(), agentModel, promptFile, featureDesc)
			}
		}

		// Check if iterate-loop might be running and warn user
		tasksFile := resolveTasksFile()

		if *dbg {
			fmt.Printf("[%s] 📖 Checking for existing tasks.md at: %s\n", ts(), tasksFile)
		}
		if _, err := os.Stat(tasksFile); err == nil {
			if *dbg {
				fmt.Printf("[%s] ✅ Found existing tasks.md\n", ts())
			}
			lock, err := LockFile(tasksFile)
			if err != nil {
				fmt.Printf("[%s] ⚠️ Warning: Could not acquire exclusive lock on %s\n", ts(), tasksFile)
				fmt.Printf("[%s] 💡 This might mean iterate-loop is running. Proceeding anyway...\n", ts())
			} else {
				// We got the lock, release it immediately
				lock.Unlock()
				if *dbg {
					fmt.Printf("[%s] ✅ Acquired file lock successfully - safe to proceed\n", ts())
				}
			}
		} else if *dbg {
			fmt.Printf("[%s] ℹ️ No existing tasks.md found (will be created)\n", ts())
		}

		// Log that we're about to send to cursor-agent
		fmt.Printf("[%s] 🚀 Sending feature design request to cursor-agent...\n", ts())
		if *dbg {
			if *useCodex {
				fmt.Printf("[%s] 🤖 Using codex (model: %s)\n", ts(), agentModel)
			} else {
				fmt.Printf("[%s] 🤖 Using cursor-agent (model: %s)\n", ts(), agentModel)
			}
		}

		// Run cursor-agent to directly edit files
		var runErr error

		if *useCodex {
			runErr = runner.CodexWithDebug(*dbg, agentModel, promptContent)
		} else {
			runErr = runner.CursorAgentWithDebug(*dbg, "--print", "--force", promptContent)
		}

		if runErr != nil {
			fmt.Fprintf(os.Stderr, "[%s] ❌ Feature analysis failed: %v\n", ts(), runErr)
			os.Exit(1)
		}

		// Success - cursor-agent has directly edited the control files
		fmt.Printf("[%s] ✅ Feature design complete!\n", ts())
		fmt.Printf("[%s] 📝 Control files have been updated by cursor-agent\n", ts())

		// Verify that files were actually updated
		controlFiles := []string{"architecture.md", "tasks.md", "test_plan.md", "decisions.md"}
		updatedFiles := []string{}

		for _, file := range controlFiles {
			if _, err := os.Stat(file); err == nil {
				updatedFiles = append(updatedFiles, file)
			}
		}

		if len(updatedFiles) > 0 {
			fmt.Printf("[%s] ✅ Updated files:\n", ts())
			for _, file := range updatedFiles {
				fmt.Printf("  - %s\n", file)
			}

			// Check if tasks.md exists and has content
			if _, err := os.Stat("tasks.md"); err == nil {
				content, readErr := os.ReadFile("tasks.md")
				if readErr == nil && len(content) > 0 {
					fmt.Printf("[%s] 📝 Tasks have been added to tasks.md\n", ts())
					fmt.Printf("[%s] 💡 Run 'cursor-iter task-status' to see all tasks\n", ts())
					fmt.Printf("[%s] 💡 Run 'cursor-iter iterate-loop' to start processing tasks\n", ts())
				}
			}
		} else {
			fmt.Printf("[%s] ⚠️ Warning: No control files found. The agent may not have created them yet.\n", ts())
			fmt.Printf("[%s] 💡 Check if cursor-agent made the expected changes.\n", ts())
		}
	case "run-agent":
		// Send ad-hoc request to cursor-agent/codex with control file references
		fs := flag.NewFlagSet("run-agent", flag.ExitOnError)
		prompt := fs.String("prompt", "", "ad-hoc request to send to cursor-agent/codex")
		useCodex := fs.Bool("codex", false, "use codex CLI with gpt-5-codex model")
		model := fs.String("model", envOr("MODEL", "auto"), "cursor-agent model or codex model (gpt-5-codex)")
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])

		// Validate prompt is provided
		if *prompt == "" {
			fmt.Fprintf(os.Stderr, "Error: --prompt is required\n")
			fmt.Fprintf(os.Stderr, "Usage: cursor-iter run-agent --prompt \"your request here\"\n")
			fmt.Fprintf(os.Stderr, "Example: cursor-iter run-agent --prompt \"add to our control files that pnpm build should succeed\"\n")
			os.Exit(1)
		}

		// Set default model for codex if not specified
		agentModel := *model
		if *useCodex && *model == "auto" {
			agentModel = "gpt-5-codex"
		}

		// Build a comprehensive prompt with control file references
		controlFilesList := []string{
			"architecture.md - System architecture and design",
			"decisions.md - Architectural Decision Records (ADRs)",
			"tasks.md - Task backlog and current work",
			"progress.md - Completed tasks and progress history",
			"test_plan.md - Testing strategy and coverage",
			"qa_checklist.md - Quality assurance requirements",
			"CHANGELOG.md - Change history",
			"context.md - Project context (if available)",
		}

		// Check which control files exist
		existingControlFiles := []string{}
		for _, fileDesc := range controlFilesList {
			fileName := strings.Split(fileDesc, " - ")[0]
			if _, err := os.Stat(fileName); err == nil {
				existingControlFiles = append(existingControlFiles, fileDesc)
			}
		}

		// Build the enhanced prompt
		enhancedPrompt := fmt.Sprintf(`You are working on a repository managed by the cursor-iter engineering iteration system.

## User Request

%s

## Available Control Files

The following control files are available for reference and may need to be updated:

%s

## Instructions

1. **Review the control files** listed above to understand the current state of the repository
2. **Implement the user's request** following these guidelines:
   - Update any relevant control files (architecture.md, decisions.md, tasks.md, etc.)
   - Follow existing code patterns and conventions
   - Include comprehensive logging and code comments
   - Add or update tests as needed
   - Ensure all quality gates pass (linting, formatting, type checking, tests)
   - Document your changes appropriately
   - Use conventional commit messages when committing

3. **Quality Requirements**:
   - All tests must pass
   - Code must pass linting and formatting checks
   - Follow the architecture and decisions documented in control files
   - Add detailed code comments explaining complex logic
   - Include logging for debugging and monitoring

4. **Control File Updates**:
   - If you update control files, ensure consistency across all related files
   - Document architectural decisions in decisions.md
   - Update architecture.md if system design changes
   - Add tasks to tasks.md if follow-up work is needed
   - Update test_plan.md if test coverage needs change

5. **Commit your changes** with a clear, conventional commit message

Complete the user's request and ensure all control files are updated appropriately.`, *prompt, strings.Join(existingControlFiles, "\n"))

		if *dbg {
			fmt.Printf("[%s] 🚀 Running ad-hoc request with cursor-agent...\n", ts())
			if *useCodex {
				fmt.Printf("[%s] 🤖 Using codex (model: %s)\n", ts(), agentModel)
			} else {
				fmt.Printf("[%s] 🤖 Using cursor-agent (model: %s)\n", ts(), agentModel)
			}
			fmt.Printf("[%s] 📝 User request: %s\n", ts(), *prompt)
			fmt.Printf("[%s] 📋 Control files available: %d\n", ts(), len(existingControlFiles))
		}

		// Log that we're about to send to cursor-agent
		fmt.Printf("[%s] 🚀 Sending ad-hoc request to agent...\n", ts())
		if *dbg {
			fmt.Printf("[%s] 📊 Enhanced prompt size: %d bytes\n", ts(), len(enhancedPrompt))
		}

		// Run cursor-agent or codex
		var runErr error
		if *useCodex {
			runErr = runner.CodexWithDebug(*dbg, agentModel, enhancedPrompt)
		} else {
			runErr = runner.CursorAgentWithDebug(*dbg, "--print", "--force", enhancedPrompt)
		}

		if runErr != nil {
			fmt.Fprintf(os.Stderr, "[%s] ❌ Ad-hoc request failed: %v\n", ts(), runErr)
			os.Exit(1)
		}

		fmt.Printf("[%s] ✅ Ad-hoc request completed successfully!\n", ts())
		if *dbg {
			fmt.Printf("[%s] 💡 Review changes and run 'cursor-iter task-status' to check task progress\n", ts())
		}
	case "reset":
		// Remove all control files
		controlFiles := []string{
			"architecture.md",
			"progress.md",
			"decisions.md",
			"test_plan.md",
			"qa_checklist.md",
			"CHANGELOG.md",
			"context.md",
			"tasks.md",
			"prompts/iterate.md",
			"completed_tasks",
		}

		removed := 0
		for _, file := range controlFiles {
			if err := os.RemoveAll(file); err == nil {
				fmt.Printf("Removed: %s\n", file)
				removed++
			}
		}
		fmt.Printf("Reset complete. Removed %d control files/directories.\n", removed)
	default:
		if cmd == "-h" || cmd == "--help" || strings.TrimSpace(cmd) == "" {
			usage()
			return
		}
		fmt.Fprintf(os.Stderr, "unknown command: %s\n", cmd)
		usage()
		os.Exit(1)
	}
}

func resolveTasksFile() string {
	if v := os.Getenv("TASKS_FILE"); v != "" {
		return v
	}
	if _, err := os.Stat("tasks.md"); err == nil {
		return "tasks.md"
	}
	if _, err := os.Stat("../tasks.md"); err == nil {
		return "../tasks.md"
	}
	return "tasks.md"
}

func resolveProgressFile() string {
	if v := os.Getenv("PROGRESS_FILE"); v != "" {
		return v
	}
	if _, err := os.Stat("progress.md"); err == nil {
		return "progress.md"
	}
	if _, err := os.Stat("../progress.md"); err == nil {
		return "../progress.md"
	}
	return "progress.md"
}

func envOr(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

func ts() string { return time.Now().Format("15:04:05") }

// fetchPromptFromGitHub fetches a prompt file from GitHub if it doesn't exist locally
func fetchPromptFromGitHub(promptFile string) error {
	// Check if file already exists locally
	if _, err := os.Stat(promptFile); err == nil {
		return nil // File exists, no need to fetch
	}

	// Extract the filename from the path
	filename := filepath.Base(promptFile)

	// GitHub repository details
	owner := "cheddarwhizzy"
	repo := "cursor-autopilot"
	branch := "main"

	// Construct GitHub raw URL
	url := fmt.Sprintf("https://raw.githubusercontent.com/%s/%s/%s/cursor-agent-iteration/prompts/%s",
		owner, repo, branch, filename)

	fmt.Printf("[%s] Fetching %s from GitHub...\n", ts(), filename)

	// Make HTTP request
	resp, err := http.Get(url)
	if err != nil {
		return fmt.Errorf("failed to fetch %s from GitHub: %v", filename, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to fetch %s: HTTP %d", filename, resp.StatusCode)
	}

	// Create directory if it doesn't exist
	dir := filepath.Dir(promptFile)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory %s: %v", dir, err)
	}

	// Read response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response body: %v", err)
	}

	// Write file
	if err := os.WriteFile(promptFile, body, 0644); err != nil {
		return fmt.Errorf("failed to write %s: %v", promptFile, err)
	}

	fmt.Printf("[%s] ✅ Successfully fetched %s\n", ts(), filename)
	return nil
}
