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
	fmt.Println("  cursor-iter task-status   [--file tasks.md]")
	fmt.Println("  cursor-iter archive-completed [--file tasks.md] [--outdir completed_tasks]")
	fmt.Println("  cursor-iter iterate-init   [--model auto]  # uses prompts/initialize-iteration-universal.md")
	fmt.Println("  cursor-iter iterate                      # runs iteration using prompts/iterate.md")
	fmt.Println("  cursor-iter iterate-loop                 # loops until completion")
	fmt.Println("  cursor-iter add-feature                  # uses prompts/add-feature.md")
	fmt.Println("  cursor-iter add-feature --file <path>    # read feature description from file")
	fmt.Println("  cursor-iter add-feature --prompt \"desc\"  # provide feature description as argument")
	fmt.Println("  cursor-iter validate-tasks [--fix]       # validate/fix tasks.md structure")
	fmt.Println("  cursor-iter reset                       # remove all control files")
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
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])
		if *dbg {
			fmt.Printf("[%s] task-status reading %s\n", ts(), *file)
		}
		content, err := os.ReadFile(*file)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error reading %s: %v\n", *file, err)
			os.Exit(1)
		}
		report := tasks.StatusReport(string(content))
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
		outdir := fs.String("outdir", "completed_tasks", "archive directory")
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])
		if *dbg {
			fmt.Printf("[%s] archiving completed from %s to %s\n", ts(), *file, *outdir)
		}
		content, err := os.ReadFile(*file)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error reading %s: %v\n", *file, err)
			os.Exit(1)
		}
		archived, remaining, archiveFile, err := tasks.ArchiveCompleted(string(content), *outdir)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error archiving: %v\n", err)
			os.Exit(1)
		}
		if err := os.WriteFile(*file, []byte(remaining), 0644); err != nil {
			fmt.Fprintf(os.Stderr, "error writing tasks: %v\n", err)
			os.Exit(1)
		}
		if err := os.WriteFile(archiveFile, []byte(archived), 0644); err != nil {
			fmt.Fprintf(os.Stderr, "error writing archive: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("Archived to %s\n", archiveFile)
	case "iterate-init":
		fs := flag.NewFlagSet("iterate-init", flag.ExitOnError)
		model := fs.String("model", envOr("MODEL", "auto"), "cursor-agent model")
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
		if *dbg {
			fmt.Printf("[%s] iterate-init using model=%s, prompt=%s\n", ts(), *model, promptFile)
		}
		if err := runner.CursorAgentWithDebug(*dbg, "--print", "--force", "--model", *model, string(data)); err != nil {
			os.Exit(1)
		}
	case "iterate":
		// Run the main iteration based on prompts/iterate.md
		// We reuse the existing shell command content to direct cursor-agent
		file := resolveTasksFile()
		
		// Acquire file lock before running iteration
		lock, err := LockFile(file)
		if err != nil {
			fmt.Fprintf(os.Stderr, "[%s] ⚠️ Could not acquire file lock: %v\n", ts(), err)
			fmt.Fprintf(os.Stderr, "[%s] 💡 Another process may be modifying tasks.md. Please try again later.\n", ts())
			os.Exit(1)
		}
		
		fmt.Printf("[%s] ✅ Acquired file lock successfully - safe to proceed\n", ts())
		
		// Set up cleanup to release lock on exit
		defer func() {
			lock.Unlock()
			fmt.Printf("[%s] 🔓 Released file lock\n", ts())
		}()
		
		msg := "Please execute the engineering iteration loop as defined in prompts/iterate.md. Read the control files (architecture.md, tasks.md, progress.md, decisions.md, test_plan.md, qa_checklist.md, CHANGELOG.md) and select the first unchecked task from tasks.md. Then implement, test, validate, document, and commit the changes following the quality gates specified in the iteration prompt."
		if debug {
			fmt.Printf("[%s] iterate executing one cycle\n", ts())
		}
		if err := runner.CursorAgentWithDebug(debug, "--print", "--force", msg); err != nil {
			os.Exit(1)
		}
	case "iterate-loop":
		// Minimal loop invoking iterate until tasks are complete
		file := resolveTasksFile()
		for i := 1; i <= 50; i++ { // safety cap
			// Acquire file lock before reading tasks
			lock, err := LockFile(file)
			if err != nil {
				fmt.Fprintf(os.Stderr, "[%s] ⚠️ Could not acquire file lock: %v\n", ts(), err)
				fmt.Fprintf(os.Stderr, "[%s] 💡 Another process may be modifying tasks.md. Retrying...\n", ts())
				time.Sleep(2 * time.Second)
				continue
			}
			
			fmt.Printf("[%s] ✅ Acquired file lock successfully - safe to proceed\n", ts())

			b, err := os.ReadFile(file)
			if err != nil {
				lock.Unlock()
				fmt.Fprintf(os.Stderr, "error reading tasks file: %v\n", err)
				os.Exit(1)
			}
			content := string(b)

			if tasks.Complete(content) {
				lock.Unlock()
				fmt.Printf("[%s] ✅ All tasks completed successfully!\n", ts())
				return
			}

			// Show current progress
			progress := tasks.GetTaskProgress(content)
			fmt.Printf("[%s] Iteration #%d - %s\n", ts(), i, progress)

			// Mark the next task as in-progress if there's a pending task
			nextTask := tasks.GetNextPendingTask(content)
			if nextTask != nil {
				updatedContent, err := tasks.MarkTaskInProgress(content)
				if err == nil {
					// Write the updated content back to the file while holding the lock
					if err := os.WriteFile(file, []byte(updatedContent), 0644); err != nil {
						lock.Unlock()
						fmt.Fprintf(os.Stderr, "[%s] ⚠️ Warning: could not update task status: %v\n", ts(), err)
					} else {
						fmt.Printf("[%s] 📝 Marked task '%s' as in-progress\n", ts(), nextTask.Title)
					}
				}
			}

			fmt.Printf("[%s] 🔄 Starting iteration...\n", ts())
			if err := runner.CursorAgentWithDebug(debug, "--print", "--force", "Please execute the engineering iteration loop as defined in prompts/iterate.md."); err != nil {
				lock.Unlock()
				fmt.Fprintf(os.Stderr, "[%s] ❌ iteration failed: %v\n", ts(), err)
				os.Exit(1)
			}

			// Release lock after cursor-agent completes successfully
			lock.Unlock()
			fmt.Printf("[%s] 🔓 Released file lock\n", ts())

			// Check progress after iteration (without lock for quick read)
			b2, err := os.ReadFile(file)
			if err == nil {
				newContent := string(b2)
				newProgress := tasks.GetTaskProgress(newContent)
				fmt.Printf("[%s] 📊 Updated progress: %s\n", ts(), newProgress)
			}
		}
		fmt.Printf("[%s] ⚠️ Reached max iterations (%d) without completion\n", ts(), 50)
	case "add-feature":
		fs := flag.NewFlagSet("add-feature", flag.ExitOnError)
		file := fs.String("file", "", "read feature description from file")
		prompt := fs.String("prompt", "", "provide feature description as command line argument")
		dbg := fs.Bool("debug", debug, "enable verbose logging")
		_ = fs.Parse(os.Args[2:])

		promptFile := "./prompts/add-feature.md"

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

		fmt.Printf("[%s] Analyzing feature and creating architecture/tasks...\n", ts())
		if *dbg {
			fmt.Printf("[%s] add-feature using prompt=%s with feature: %s\n", ts(), promptFile, featureDesc)
		}

		// Check if iterate-loop might be running and warn user
		tasksFile := resolveTasksFile()
		if _, err := os.Stat(tasksFile); err == nil {
			lock, err := LockFile(tasksFile)
			if err != nil {
				fmt.Printf("[%s] ⚠️ Warning: Could not acquire exclusive lock on %s\n", ts(), tasksFile)
				fmt.Printf("[%s] 💡 This might mean iterate-loop is running. Proceeding anyway...\n", ts())
			} else {
				// We got the lock, release it immediately
				lock.Unlock()
				fmt.Printf("[%s] ✅ Acquired file lock successfully - safe to proceed\n", ts())
			}
		}

		if err := runner.CursorAgentWithDebug(*dbg, "--print", "--force", promptContent); err != nil {
			os.Exit(1)
		}

		fmt.Printf("[%s] ✅ Feature analysis complete! Tasks should be added to %s\n", ts(), tasksFile)
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
