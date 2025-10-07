package tasks

import (
    "fmt"
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

// MarkTaskInProgress marks the first pending task as in-progress by updating the task header
func MarkTaskInProgress(md string) (string, error) {
    lines := strings.Split(md, "\n")
    inCurrentTasks := false
    taskFound := false
    
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
        
        // Stop processing if we hit another major section (##)
        if strings.HasPrefix(strings.TrimSpace(line), "## ") && strings.TrimSpace(line) != "## Current Tasks" {
            break
        }
        
        // Look for task headers that don't already have emoji status
        if reTaskHeader.MatchString(line) && !strings.Contains(line, "🔄") && !strings.Contains(line, "✅") && !strings.Contains(line, "⚠️") {
            // Found a pending task - mark it as in progress
            taskTitle := reTaskHeader.FindStringSubmatch(line)[1]
            lines[i] = fmt.Sprintf("### Task: 🔄 %s", strings.TrimSpace(taskTitle))
            taskFound = true
            break
        }
    }
    
    if !taskFound {
        return md, fmt.Errorf("no pending task found to mark as in-progress")
    }
    
    return strings.Join(lines, "\n"), nil
}


