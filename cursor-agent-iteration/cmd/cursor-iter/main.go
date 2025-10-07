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
	"time"

	"github.com/cheddarwhizzy/cursor-autopilot/cursor-agent-iteration/internal/runner"
	"github.com/cheddarwhizzy/cursor-autopilot/cursor-agent-iteration/internal/tasks"
)

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
			b, err := os.ReadFile(file)
			if err != nil {
				fmt.Fprintf(os.Stderr, "error reading tasks file: %v\n", err)
				os.Exit(1)
			}
			content := string(b)

			if tasks.Complete(content) {
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
					// Write the updated content back to the file
					if err := os.WriteFile(file, []byte(updatedContent), 0644); err != nil {
						fmt.Fprintf(os.Stderr, "[%s] ⚠️ Warning: could not update task status: %v\n", ts(), err)
					} else {
						fmt.Printf("[%s] 📝 Marked task '%s' as in-progress\n", ts(), nextTask.Title)
					}
				}
			}

			fmt.Printf("[%s] 🔄 Starting iteration...\n", ts())
			if err := runner.CursorAgentWithDebug(debug, "--print", "--force", "Please execute the engineering iteration loop as defined in prompts/iterate.md."); err != nil {
				fmt.Fprintf(os.Stderr, "[%s] ❌ iteration failed: %v\n", ts(), err)
				os.Exit(1)
			}

			// Check progress after iteration
			b2, err := os.ReadFile(file)
			if err == nil {
				newContent := string(b2)
				newProgress := tasks.GetTaskProgress(newContent)
				fmt.Printf("[%s] 📊 Updated progress: %s\n", ts(), newProgress)
			}
		}
		fmt.Printf("[%s] ⚠️ Reached max iterations (%d) without completion\n", ts(), 50)
	case "add-feature":
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

		// Check if feature description is provided via file
		if len(os.Args) > 2 && os.Args[2] == "--file" && len(os.Args) > 3 {
			// Read from file
			filePath := os.Args[3]
			fileData, err := os.ReadFile(filePath)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error reading file %s: %v\n", filePath, err)
				os.Exit(1)
			}
			featureDesc = string(fileData)
			fmt.Printf("✅ Loaded feature description from %s (%d characters)\n", filePath, len(featureDesc))
		} else {
			// Interactive input
			fmt.Print("Enter feature description (press Enter twice when done):\n")
			fmt.Print("Tip: For long descriptions, you can paste multi-line text. Press Enter twice to finish.\n")
			fmt.Print("Alternative: Use --file <path> to read from a file\n")

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
		if debug {
			fmt.Printf("[%s] add-feature using prompt=%s with feature: %s\n", ts(), promptFile, featureDesc)
		}
		if err := runner.CursorAgentWithDebug(debug, "--print", "--force", promptContent); err != nil {
			os.Exit(1)
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
