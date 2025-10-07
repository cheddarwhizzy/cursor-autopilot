package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
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
        if *dbg { fmt.Printf("[%s] task-status reading %s\n", ts(), *file) }
        content, err := os.ReadFile(*file)
        if err != nil {
            fmt.Fprintf(os.Stderr, "error reading %s: %v\n", *file, err)
            os.Exit(1)
        }
        report := tasks.StatusReport(string(content))
        fmt.Println(report)
    case "archive-completed":
        fs := flag.NewFlagSet("archive-completed", flag.ExitOnError)
        file := fs.String("file", resolveTasksFile(), "tasks file")
        outdir := fs.String("outdir", "completed_tasks", "archive directory")
        dbg := fs.Bool("debug", debug, "enable verbose logging")
        _ = fs.Parse(os.Args[2:])
        if *dbg { fmt.Printf("[%s] archiving completed from %s to %s\n", ts(), *file, *outdir) }
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
        data, err := os.ReadFile(promptFile)
        if err != nil {
            fmt.Fprintf(os.Stderr, "missing prompt %s: %v\n", promptFile, err)
            os.Exit(1)
        }
        if *dbg { fmt.Printf("[%s] iterate-init using model=%s, prompt=%s\n", ts(), *model, promptFile) }
        if err := runner.CursorAgentWithDebug(*dbg, "--print", "--force", "--model", *model, string(data)); err != nil {
            os.Exit(1)
        }
    case "iterate":
        // Run the main iteration based on prompts/iterate.md
        // We reuse the existing shell command content to direct cursor-agent
        msg := "Please execute the engineering iteration loop as defined in prompts/iterate.md. Read the control files (architecture.md, tasks.md, progress.md, decisions.md, test_plan.md, qa_checklist.md, CHANGELOG.md) and select the first unchecked task from tasks.md. Then implement, test, validate, document, and commit the changes following the quality gates specified in the iteration prompt."
        if debug { fmt.Printf("[%s] iterate executing one cycle\n", ts()) }
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
        data, err := os.ReadFile(promptFile)
        if err != nil {
            fmt.Fprintf(os.Stderr, "missing prompt %s: %v\n", promptFile, err)
            os.Exit(1)
        }
        
        // Prompt user for feature description
        fmt.Print("Enter feature description (press Enter twice when done):\n")
        var featureDesc string
        scanner := bufio.NewScanner(os.Stdin)
        var lines []string
        emptyLineCount := 0
        
        for scanner.Scan() {
            line := scanner.Text()
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
        featureDesc = strings.Join(lines, "\n")
        
        // Replace placeholder with user input
        promptContent := strings.ReplaceAll(string(data), "{{FEATURE_DESCRIPTION}}", featureDesc)
        
        fmt.Printf("[%s] Analyzing feature and creating architecture/tasks...\n", ts())
        if debug { fmt.Printf("[%s] add-feature using prompt=%s with feature: %s\n", ts(), promptFile, featureDesc) }
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


