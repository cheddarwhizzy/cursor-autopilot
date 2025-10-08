package tasks

import (
	"fmt"
	"regexp"
	"strings"
)

// Complete returns true if there is at least one task and all tasks with
// acceptance criteria have all items checked.
func Complete(md string) bool {
	ts := parseTasks(md)
	if len(ts) == 0 {
		return false
	}
	for _, t := range ts {
		if t.ACTotal == 0 {
			// Treat tasks without AC as incomplete
			return false
		}
		if t.ACChecked != t.ACTotal {
			return false
		}
	}
	return true
}

// GetCurrentTask returns the first in-progress task (has emoji status or some AC checked)
func GetCurrentTask(md string) *Task {
	ts := parseTasks(md)
	for _, t := range ts {
		if t.Status == "in-progress" || (t.ACChecked > 0 && t.ACChecked < t.ACTotal) {
			return &t
		}
	}
	return nil
}

// GetNextPendingTask returns the first pending task (no status emoji and no AC checked)
func GetNextPendingTask(md string) *Task {
	ts := parseTasks(md)
	for _, t := range ts {
		if t.Status == "pending" && t.ACChecked == 0 {
			return &t
		}
	}
	return nil
}

// GetTaskProgress returns a progress string for the current state
func GetTaskProgress(md string) string {
	ts := parseTasks(md)
	if len(ts) == 0 {
		return "No tasks found"
	}

	current := GetCurrentTask(md)
	if current != nil {
		return fmt.Sprintf("🔄 Working on: %s (%d/%d criteria)", current.Title, current.ACChecked, current.ACTotal)
	}

	next := GetNextPendingTask(md)
	if next != nil {
		return fmt.Sprintf("⏳ Next task: %s", next.Title)
	}

	return "✅ All tasks completed"
}

// Note: MarkTaskInProgress has been moved to progress.go
// It now operates on progress.md instead of tasks.md
// tasks.md is now a simple list without status tracking

// ValidationResult represents the result of structure validation
type ValidationResult struct {
	Valid    bool
	Errors   []string
	Warnings []string
}

// ValidateTasksStructure validates that tasks.md has the correct structure
func ValidateTasksStructure(md string) ValidationResult {
	result := ValidationResult{Valid: true, Errors: []string{}, Warnings: []string{}}

	lines := strings.Split(md, "\n")
	hasCurrentTasksSection := false
	taskCount := 0
	inCurrentTasks := false

	// Regex patterns for validation
	currentTasksRegex := regexp.MustCompile(`^## Current Tasks\s*$`)
	taskHeaderRegex := regexp.MustCompile(`^### Task: (.+)\s*$`)
	contextRegex := regexp.MustCompile(`^\*\*Context:\*\*\s*`)
	acceptanceCriteriaRegex := regexp.MustCompile(`^\*\*Acceptance Criteria:\*\*\s*$`)
	checkboxRegex := regexp.MustCompile(`^[*-] \[( |x|X)\]`)

	for i, line := range lines {
		// Check for Current Tasks section
		if currentTasksRegex.MatchString(line) {
			hasCurrentTasksSection = true
			inCurrentTasks = true
			continue
		}

		// Check if we're leaving the Current Tasks section
		if inCurrentTasks && strings.HasPrefix(strings.TrimSpace(line), "## ") && !currentTasksRegex.MatchString(line) {
			inCurrentTasks = false
			continue
		}

		// Only validate tasks within the Current Tasks section
		if !inCurrentTasks {
			continue
		}

		// Check for task headers
		if taskHeaderRegex.MatchString(line) {
			taskCount++
			taskTitle := strings.TrimSpace(taskHeaderRegex.FindStringSubmatch(line)[1])

			// Validate task title (should not be empty)
			if strings.TrimSpace(taskTitle) == "" {
				result.Errors = append(result.Errors, fmt.Sprintf("Line %d: Task title is empty", i+1))
				result.Valid = false
			}

			// Look ahead to validate task structure
			taskValid := validateTaskStructure(lines, i+1, contextRegex, acceptanceCriteriaRegex, checkboxRegex)
			if !taskValid {
				result.Errors = append(result.Errors, fmt.Sprintf("Line %d: Task '%s' is missing required structure (Context, Acceptance Criteria, or checkbox items)", i+1, taskTitle))
				result.Valid = false
			}
		}
	}

	// Check for required Current Tasks section
	if !hasCurrentTasksSection {
		result.Errors = append(result.Errors, "Missing required '## Current Tasks' section header")
		result.Valid = false
	}

	// Check if there are tasks outside the Current Tasks section
	if hasCurrentTasksSection && taskCount == 0 {
		result.Warnings = append(result.Warnings, "No tasks found in Current Tasks section")
	}

	return result
}

// validateTaskStructure checks if a task has the required structure
func validateTaskStructure(lines []string, startLine int, contextRegex, acceptanceCriteriaRegex, checkboxRegex *regexp.Regexp) bool {
	hasContext := false
	hasAcceptanceCriteria := false
	hasCheckboxes := false

	// Look at the next 20 lines for task structure
	for i := startLine; i < len(lines) && i < startLine+20; i++ {
		line := lines[i]

		// Stop if we hit another task or section
		if strings.HasPrefix(line, "### ") || strings.HasPrefix(line, "## ") {
			break
		}

		if contextRegex.MatchString(line) {
			hasContext = true
		}

		if acceptanceCriteriaRegex.MatchString(line) {
			hasAcceptanceCriteria = true
		}

		if checkboxRegex.MatchString(line) {
			hasCheckboxes = true
		}
	}

	return hasContext && hasAcceptanceCriteria && hasCheckboxes
}

// ValidateAndFixTasksStructure validates and attempts to fix common structure issues
func ValidateAndFixTasksStructure(md string) (string, ValidationResult) {
	result := ValidateTasksStructure(md)

	if result.Valid {
		return md, result
	}

	lines := strings.Split(md, "\n")
	fixed := false

	// Fix missing Current Tasks section
	if !strings.Contains(md, "## Current Tasks") {
		// Find where to insert the section (after any existing content)
		insertIndex := 0
		for i, line := range lines {
			if strings.TrimSpace(line) != "" {
				insertIndex = i
				break
			}
		}

		// Insert the Current Tasks section
		newLines := make([]string, 0, len(lines)+2)
		newLines = append(newLines, lines[:insertIndex]...)
		newLines = append(newLines, "## Current Tasks", "")
		newLines = append(newLines, lines[insertIndex:]...)
		lines = newLines
		fixed = true
	}

	if fixed {
		result.Valid = true
		result.Errors = []string{}
		result.Warnings = append(result.Warnings, "Fixed missing '## Current Tasks' section")
	}

	return strings.Join(lines, "\n"), result
}
