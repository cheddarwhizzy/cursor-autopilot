package tasks

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


