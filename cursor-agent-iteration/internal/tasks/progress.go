package tasks

import (
	"fmt"
	"path/filepath"
	"strings"
	"time"
)

// ProgressEntry represents a task status entry in progress.md
type ProgressEntry struct {
	TaskTitle   string
	Status      string // "in-progress" or "completed"
	StartedAt   time.Time
	CompletedAt time.Time
	Notes       string
}

// ParseProgress reads progress.md and returns task status entries
func ParseProgress(progressMd string) map[string]ProgressEntry {
	entries := make(map[string]ProgressEntry)
	lines := strings.Split(progressMd, "\n")

	inCompletedSection := false
	inProgressSection := false

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)

		// Check for section headers
		if trimmed == "## In Progress" {
			inProgressSection = true
			inCompletedSection = false
			continue
		} else if trimmed == "## Completed Tasks" {
			inCompletedSection = true
			inProgressSection = false
			continue
		} else if strings.HasPrefix(trimmed, "## ") {
			inProgressSection = false
			inCompletedSection = false
			continue
		}

		// Parse in-progress tasks: "- 🔄 [2025-01-08 19:00] Task Title - notes"
		if inProgressSection && (strings.HasPrefix(trimmed, "- 🔄") || strings.HasPrefix(trimmed, "* 🔄")) {
			parts := strings.SplitN(line, "]", 2)
			if len(parts) == 2 {
				remainder := strings.TrimSpace(parts[1])
				titleParts := strings.SplitN(remainder, " - ", 2)
				taskTitle := strings.TrimSpace(titleParts[0])
				notes := ""
				if len(titleParts) > 1 {
					notes = strings.TrimSpace(titleParts[1])
				}

				timestamp := strings.TrimPrefix(strings.TrimSpace(parts[0]), "- 🔄 [")
				timestamp = strings.TrimPrefix(timestamp, "* 🔄 [")
				startedAt, _ := time.Parse("2006-01-02 15:04", timestamp)

				entries[taskTitle] = ProgressEntry{
					TaskTitle: taskTitle,
					Status:    "in-progress",
					StartedAt: startedAt,
					Notes:     notes,
				}
			}
		}

		// Parse completed tasks: "- ✅ [2025-01-08 19:00] Task Title - notes"
		if inCompletedSection && (strings.HasPrefix(trimmed, "- ✅") || strings.HasPrefix(trimmed, "* ✅")) {
			parts := strings.SplitN(line, "]", 2)
			if len(parts) == 2 {
				remainder := strings.TrimSpace(parts[1])
				titleParts := strings.SplitN(remainder, " - ", 2)
				taskTitle := strings.TrimSpace(titleParts[0])
				notes := ""
				if len(titleParts) > 1 {
					notes = strings.TrimSpace(titleParts[1])
				}

				timestamp := strings.TrimPrefix(strings.TrimSpace(parts[0]), "- ✅ [")
				timestamp = strings.TrimPrefix(timestamp, "* ✅ [")
				completedAt, _ := time.Parse("2006-01-02 15:04", timestamp)

				entries[taskTitle] = ProgressEntry{
					TaskTitle:   taskTitle,
					Status:      "completed",
					CompletedAt: completedAt,
					Notes:       notes,
				}
			}
		}
	}

	return entries
}

// LogTaskCompletion adds a task completion entry to progress.md
func LogTaskCompletion(progressMd string, taskTitle string, notes string) string {
	timestamp := time.Now().Format("2006-01-02 15:04")
	entry := fmt.Sprintf("- ✅ [%s] %s", timestamp, taskTitle)
	if notes != "" {
		entry += fmt.Sprintf(" - %s", notes)
	}
	entry += "\n"

	// If progress.md is empty or doesn't have a header, add one
	if strings.TrimSpace(progressMd) == "" {
		progressMd = "# Progress Log\n\n## Completed Tasks\n\n"
	} else if !strings.Contains(progressMd, "## Completed Tasks") {
		progressMd += "\n## Completed Tasks\n\n"
	}

	// Find the "## Completed Tasks" section and add the entry there
	lines := strings.Split(progressMd, "\n")
	var result []string
	inCompletedSection := false
	entryAdded := false

	for _, line := range lines {
		if strings.TrimSpace(line) == "## Completed Tasks" {
			inCompletedSection = true
			result = append(result, line)
			continue
		}

		// If we're in the Completed Tasks section and haven't added the entry yet
		if inCompletedSection && !entryAdded && strings.TrimSpace(line) == "" {
			result = append(result, line)
			result = append(result, entry)
			entryAdded = true
			continue
		}

		// Stop if we hit another section
		if inCompletedSection && strings.HasPrefix(strings.TrimSpace(line), "## ") {
			if !entryAdded {
				result = append(result, entry)
				entryAdded = true
			}
			inCompletedSection = false
		}

		result = append(result, line)
	}

	// If we reached the end and haven't added the entry, add it now
	if !entryAdded {
		result = append(result, entry)
	}

	return strings.Join(result, "\n")
}

// MarkTaskInProgress adds a task to the "In Progress" section of progress.md
func MarkTaskInProgress(progressMd string, taskTitle string) string {
	timestamp := time.Now().Format("2006-01-02 15:04")
	entry := fmt.Sprintf("- 🔄 [%s] %s\n", timestamp, taskTitle)

	// If progress.md is empty or doesn't have headers, create structure
	if strings.TrimSpace(progressMd) == "" {
		progressMd = "# Progress Log\n\n## In Progress\n\n## Completed Tasks\n\n"
	} else if !strings.Contains(progressMd, "## In Progress") {
		// Add In Progress section before Completed Tasks
		if strings.Contains(progressMd, "## Completed Tasks") {
			progressMd = strings.Replace(progressMd, "## Completed Tasks", "## In Progress\n\n## Completed Tasks", 1)
		} else {
			progressMd += "\n## In Progress\n\n"
		}
	}

	// Find the "## In Progress" section and add the entry there
	lines := strings.Split(progressMd, "\n")
	var result []string
	inProgressSection := false
	entryAdded := false

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)

		if trimmed == "## In Progress" {
			inProgressSection = true
			result = append(result, line)
			continue
		}

		// If we're in the In Progress section and haven't added the entry yet
		if inProgressSection && !entryAdded && trimmed == "" {
			result = append(result, line)
			result = append(result, entry)
			entryAdded = true
			continue
		}

		// Stop if we hit another section
		if inProgressSection && strings.HasPrefix(trimmed, "## ") {
			if !entryAdded {
				result = append(result, entry)
				entryAdded = true
			}
			inProgressSection = false
		}

		result = append(result, line)
	}

	// If we reached the end and haven't added the entry, add it now
	if !entryAdded {
		result = append(result, entry)
	}

	return strings.Join(result, "\n")
}

// MoveTaskToCompleted moves a task from "In Progress" to "Completed" in progress.md
func MoveTaskToCompleted(progressMd string, taskTitle string, notes string) string {
	timestamp := time.Now().Format("2006-01-02 15:04")
	completedEntry := fmt.Sprintf("- ✅ [%s] %s", timestamp, taskTitle)
	if notes != "" {
		completedEntry += fmt.Sprintf(" - %s", notes)
	}
	completedEntry += "\n"

	lines := strings.Split(progressMd, "\n")
	var result []string
	inProgressSection := false
	completedSection := false
	taskAdded := false

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)

		// Track sections
		if trimmed == "## In Progress" {
			inProgressSection = true
			completedSection = false
			result = append(result, line)
			continue
		} else if trimmed == "## Completed Tasks" {
			completedSection = true
			inProgressSection = false
			result = append(result, line)
			continue
		} else if strings.HasPrefix(trimmed, "## ") {
			inProgressSection = false
			completedSection = false
		}

		// Remove from In Progress section
		if inProgressSection && strings.Contains(line, taskTitle) && strings.Contains(line, "🔄") {
			continue // Skip this line
		}

		// Add to Completed section
		if completedSection && !taskAdded && trimmed == "" {
			result = append(result, line)
			result = append(result, completedEntry)
			taskAdded = true
			continue
		}

		result = append(result, line)
	}

	// If task wasn't added yet (no empty line found), add it now
	if !taskAdded && completedSection {
		result = append(result, completedEntry)
	}

	return strings.Join(result, "\n")
}

// IsTaskCompleted checks if a task is marked as completed in progress.md
func IsTaskCompleted(progressMd string, taskTitle string) bool {
	entries := ParseProgress(progressMd)
	entry, exists := entries[taskTitle]
	return exists && entry.Status == "completed"
}

// IsTaskInProgress checks if a task is marked as in-progress in progress.md
func IsTaskInProgress(progressMd string, taskTitle string) bool {
	entries := ParseProgress(progressMd)
	entry, exists := entries[taskTitle]
	return exists && entry.Status == "in-progress"
}

// GetCompletedTasks returns a list of completed task titles from progress.md
func GetCompletedTasks(progressMd string) []string {
	entries := ParseProgress(progressMd)
	var titles []string
	for title, entry := range entries {
		if entry.Status == "completed" {
			titles = append(titles, title)
		}
	}
	return titles
}

// GetInProgressTasks returns a list of in-progress task titles from progress.md
func GetInProgressTasks(progressMd string) []string {
	entries := ParseProgress(progressMd)
	var titles []string
	for title, entry := range entries {
		if entry.Status == "in-progress" {
			titles = append(titles, title)
		}
	}
	return titles
}

// GetNextPendingTaskWithProgress returns the first task that's not in progress.md
func GetNextPendingTaskWithProgress(tasksMd string, progressMd string) *Task {
	tasks := parseTasks(tasksMd)
	progressEntries := ParseProgress(progressMd)

	for _, t := range tasks {
		// Skip tasks that are in progress.md (either in-progress or completed)
		if _, exists := progressEntries[t.Title]; exists {
			continue
		}

		// Return the first task not in progress.md (pending)
		return &t
	}

	return nil
}

// GetCurrentTaskWithProgress returns the first in-progress task from progress.md
func GetCurrentTaskWithProgress(tasksMd string, progressMd string) *Task {
	tasks := parseTasks(tasksMd)
	progressEntries := ParseProgress(progressMd)

	for _, t := range tasks {
		// Check if task is in-progress in progress.md
		if entry, exists := progressEntries[t.Title]; exists && entry.Status == "in-progress" {
			return &t
		}
	}

	return nil
}

// CompleteAllChecked checks if all tasks are marked as completed in progress.md
func CompleteAllChecked(tasksMd string, progressMd string) bool {
	tasks := parseTasks(tasksMd)
	if len(tasks) == 0 {
		return false
	}

	progressEntries := ParseProgress(progressMd)

	for _, t := range tasks {
		// Check if task is marked as completed in progress.md
		entry, exists := progressEntries[t.Title]
		if !exists || entry.Status != "completed" {
			return false
		}
	}

	return true
}

// StatusReportWithProgress generates a status report using both tasks.md and progress.md
func StatusReportWithProgress(tasksMd string, progressMd string) string {
	tasks := parseTasks(tasksMd)
	progressEntries := ParseProgress(progressMd)

	total := len(tasks)
	done := 0
	prog := 0
	pend := 0

	var doneL, progL, pendL []string

	for _, t := range tasks {
		// Check task status in progress.md
		entry, exists := progressEntries[t.Title]

		if exists && entry.Status == "completed" {
			done++
			doneL = append(doneL, fmt.Sprintf("  - %s", t.Title))
		} else if exists && entry.Status == "in-progress" {
			prog++
			progL = append(progL, fmt.Sprintf("  - %s (%d/%d criteria completed)", t.Title, t.ACChecked, t.ACTotal))
		} else {
			pend++
			pendL = append(pendL, fmt.Sprintf("  - %s", t.Title))
		}
	}

	var b strings.Builder
	b.WriteString("📊 Task Status Overview\n")
	b.WriteString("======================\n")
	b.WriteString("Status tracked in: progress.md (✅ completed, 🔄 in-progress)\n")
	b.WriteString("Task list from: tasks.md (⏳ pending)\n\n")

	// Show current task status at the top
	current := GetCurrentTaskWithProgress(tasksMd, progressMd)
	if current != nil {
		b.WriteString(fmt.Sprintf("🎯 CURRENT TASK: %s (%d/%d criteria completed)\n\n", current.Title, current.ACChecked, current.ACTotal))
	} else if len(tasks) > 0 {
		next := GetNextPendingTaskWithProgress(tasksMd, progressMd)
		if next != nil {
			b.WriteString(fmt.Sprintf("🎯 NEXT TASK: %s\n\n", next.Title))
		} else {
			b.WriteString("🎯 ALL TASKS COMPLETED! 🎉\n\n")
		}
	}

	b.WriteString(fmt.Sprintf("Total Tasks: %d (from tasks.md)\n", total))
	b.WriteString(fmt.Sprintf("✅ Completed: %d (from progress.md)\n", done))
	b.WriteString(fmt.Sprintf("🔄 In Progress: %d (from progress.md)\n", prog))
	b.WriteString(fmt.Sprintf("⏳ Pending: %d (not in progress.md)\n\n", pend))

	if done > 0 {
		b.WriteString("✅ Completed Tasks (from progress.md):\n")
		b.WriteString(strings.Join(doneL, "\n"))
		b.WriteString("\n\n")
	}

	if prog > 0 {
		b.WriteString("🔄 In Progress Tasks (from progress.md):\n")
		b.WriteString(strings.Join(progL, "\n"))
		b.WriteString("\n\n")
	}

	if pend > 0 {
		b.WriteString("⏳ Pending Tasks (next 5):\n")
		if len(pendL) > 5 {
			b.WriteString(strings.Join(pendL[:5], "\n"))
			b.WriteString(fmt.Sprintf("\n  ... and %d more\n\n", len(pendL)-5))
		} else {
			b.WriteString(strings.Join(pendL, "\n"))
			b.WriteString("\n\n")
		}
	}

	return strings.TrimSuffix(b.String(), "\n")
}

// GetTaskProgressWithProgress returns a progress string using both files
func GetTaskProgressWithProgress(tasksMd string, progressMd string) string {
	tasks := parseTasks(tasksMd)
	if len(tasks) == 0 {
		return "No tasks found"
	}

	current := GetCurrentTaskWithProgress(tasksMd, progressMd)
	if current != nil {
		return fmt.Sprintf("🔄 Working on: %s (%d/%d criteria)", current.Title, current.ACChecked, current.ACTotal)
	}

	next := GetNextPendingTaskWithProgress(tasksMd, progressMd)
	if next != nil {
		return fmt.Sprintf("⏳ Next task: %s", next.Title)
	}

	return "✅ All tasks completed"
}

// IsTaskCompletedAfterRun checks if a specific task is now marked as complete in progress.md
func IsTaskCompletedAfterRun(tasksMd string, progressMd string, taskTitle string) bool {
	return IsTaskCompleted(progressMd, taskTitle)
}

// CountInProgressTasks returns the count of tasks marked as in-progress in progress.md
func CountInProgressTasks(tasksMd string, progressMd string) int {
	return len(GetInProgressTasks(progressMd))
}

// GetAllInProgressTasks returns all tasks marked as in-progress from progress.md
func GetAllInProgressTasks(tasksMd string, progressMd string) []*Task {
	tasks := parseTasks(tasksMd)
	progressEntries := ParseProgress(progressMd)
	var inProgress []*Task

	for i, t := range tasks {
		// Check if task is in-progress in progress.md
		if entry, exists := progressEntries[t.Title]; exists && entry.Status == "in-progress" {
			taskCopy := tasks[i]
			inProgress = append(inProgress, &taskCopy)
		}
	}

	return inProgress
}

// ArchiveCompletedTasks archives completed tasks by:
// 1. Moving completed tasks from progress.md to an archive file
// 2. Removing completed tasks from tasks.md
// Returns: archived content, remaining progress.md, updated tasks.md, archive file path, error
func ArchiveCompletedTasks(tasksMd string, progressMd string, outdir string) (archived string, remainingProgress string, updatedTasks string, archiveFile string, err error) {
	// Create output directory
	if err := osMkdirAll(outdir); err != nil {
		return "", "", "", "", fmt.Errorf("failed to create archive directory: %v", err)
	}

	ts := time.Now().Format("2006-01-02_15-04-05")
	archiveFile = filepath.Join(outdir, fmt.Sprintf("completed_%s.md", ts))

	// Parse progress.md to get completed tasks
	progressEntries := ParseProgress(progressMd)
	completedTitles := make(map[string]bool)

	var archivedLines []string
	archivedLines = append(archivedLines, "# Archived Completed Tasks")
	archivedLines = append(archivedLines, "")
	archivedLines = append(archivedLines, fmt.Sprintf("Archived on: %s", time.Now().Format("2006-01-02 15:04")))
	archivedLines = append(archivedLines, "")

	// Collect completed tasks for archiving
	for title, entry := range progressEntries {
		if entry.Status == "completed" {
			completedTitles[title] = true
			completedAt := entry.CompletedAt.Format("2006-01-02 15:04")
			archivedLine := fmt.Sprintf("- ✅ [%s] %s", completedAt, title)
			if entry.Notes != "" {
				archivedLine += fmt.Sprintf(" - %s", entry.Notes)
			}
			archivedLines = append(archivedLines, archivedLine)
		}
	}

	archived = strings.Join(archivedLines, "\n")

	// Remove completed tasks from progress.md (keep only in-progress)
	var remainingLines []string
	lines := strings.Split(progressMd, "\n")
	inCompletedSection := false

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)

		// Track section
		if trimmed == "## Completed Tasks" {
			inCompletedSection = true
			remainingLines = append(remainingLines, line)
			continue
		} else if trimmed == "## In Progress" {
			inCompletedSection = false
			remainingLines = append(remainingLines, line)
			continue
		} else if strings.HasPrefix(trimmed, "## ") {
			inCompletedSection = false
			remainingLines = append(remainingLines, line)
			continue
		}

		// Skip completed task lines
		if inCompletedSection && (strings.HasPrefix(trimmed, "- ✅") || strings.HasPrefix(trimmed, "* ✅")) {
			continue // Don't add this line
		}

		remainingLines = append(remainingLines, line)
	}

	remainingProgress = strings.Join(remainingLines, "\n")

	// Remove completed tasks from tasks.md
	taskLines := strings.Split(tasksMd, "\n")
	var updatedTaskLines []string
	inCurrentTasks := false
	inTask := false
	currentTaskTitle := ""
	var taskBuffer []string

	for _, line := range taskLines {
		trimmed := strings.TrimSpace(line)

		// Check for Current Tasks section
		if trimmed == "## Current Tasks" {
			inCurrentTasks = true
			updatedTaskLines = append(updatedTaskLines, line)
			continue
		}

		// Check if we're leaving Current Tasks section
		if inCurrentTasks && strings.HasPrefix(trimmed, "## ") && trimmed != "## Current Tasks" {
			// Flush any pending task
			if inTask && !completedTitles[currentTaskTitle] {
				updatedTaskLines = append(updatedTaskLines, taskBuffer...)
			}
			inCurrentTasks = false
			inTask = false
			taskBuffer = nil
			updatedTaskLines = append(updatedTaskLines, line)
			continue
		}

		// Process tasks in Current Tasks section
		if inCurrentTasks {
			if strings.HasPrefix(line, "### Task:") {
				// Flush previous task if not completed
				if inTask && !completedTitles[currentTaskTitle] {
					updatedTaskLines = append(updatedTaskLines, taskBuffer...)
				}

				// Start new task
				title := strings.TrimSpace(strings.TrimPrefix(line, "### Task:"))
				currentTaskTitle = title
				taskBuffer = []string{line}
				inTask = true
				continue
			}

			// Collect lines for current task
			if inTask {
				taskBuffer = append(taskBuffer, line)
				continue
			}
		}

		// Outside Current Tasks section or not in a task
		updatedTaskLines = append(updatedTaskLines, line)
	}

	// Flush last task if not completed
	if inTask && !completedTitles[currentTaskTitle] {
		updatedTaskLines = append(updatedTaskLines, taskBuffer...)
	}

	updatedTasks = strings.Join(updatedTaskLines, "\n")

	return archived, remainingProgress, updatedTasks, archiveFile, nil
}

// ExtractTaskDetails extracts the full task content for a specific task title from tasks.md
// Returns the task section including title, context, acceptance criteria, files, tests, etc.
func ExtractTaskDetails(tasksMd string, taskTitle string) string {
	lines := strings.Split(tasksMd, "\n")
	var taskLines []string
	inTask := false
	inCurrentTasks := false
	foundTask := false

	for i, line := range lines {
		// Check if we've reached the "## Current Tasks" section
		if strings.TrimSpace(line) == "## Current Tasks" {
			inCurrentTasks = true
			continue
		}

		// Only process tasks if we're in the Current Tasks section
		if !inCurrentTasks {
			continue
		}

		// Stop if we hit another major section (##)
		if strings.HasPrefix(strings.TrimSpace(line), "## ") && strings.TrimSpace(line) != "## Current Tasks" {
			break
		}

		// Check if this is the start of our target task
		if strings.HasPrefix(line, "### Task:") {
			// Extract the task title (removing emoji if present)
			title := strings.TrimSpace(strings.TrimPrefix(line, "### Task:"))
			title = strings.TrimSpace(strings.Replace(title, "🔄", "", 1))
			title = strings.TrimSpace(strings.Replace(title, "✅", "", 1))
			title = strings.TrimSpace(strings.Replace(title, "⚠️", "", 1))

			if title == taskTitle {
				inTask = true
				foundTask = true
				taskLines = append(taskLines, line)
				continue
			} else if inTask {
				// We've reached another task, stop collecting
				break
			}
		}

		// Collect lines if we're in the target task
		if inTask {
			// Check if we've reached the next task header
			if i+1 < len(lines) && strings.HasPrefix(lines[i+1], "### Task:") {
				taskLines = append(taskLines, line)
				break
			}
			taskLines = append(taskLines, line)
		}
	}

	if !foundTask {
		return fmt.Sprintf("### Task: %s\n\nTask not found in tasks.md", taskTitle)
	}

	return strings.Join(taskLines, "\n")
}
