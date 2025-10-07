package tasks

import (
    "fmt"
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

// GetCurrentTask returns the first in-progress task (has some but not all AC checked)
func GetCurrentTask(md string) *Task {
    ts := parseTasks(md)
    for _, t := range ts {
        if t.ACChecked > 0 && t.ACChecked < t.ACTotal {
            return &t
        }
    }
    return nil
}

// GetNextPendingTask returns the first pending task (no AC checked)
func GetNextPendingTask(md string) *Task {
    ts := parseTasks(md)
    for _, t := range ts {
        if t.ACChecked == 0 {
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


