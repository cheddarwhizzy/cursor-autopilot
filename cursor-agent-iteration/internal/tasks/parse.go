package tasks

import (
	"fmt"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

var (
	// Updated regex to allow optional emojis and other characters before "Task:"
	reTaskHeader = regexp.MustCompile(`^###\s+(?:[^\s]+\s+)?Task:\s+(.+)\s*$`)
	reACHeader   = regexp.MustCompile(`^\*\*Acceptance Criteria:\*\*\s*$`)
	reACItem     = regexp.MustCompile(`^[*-] \[( |x|X)\]`)
	reACChecked  = regexp.MustCompile(`\[(x|X)\]`)
)

type Task struct {
	Title     string
	ACTotal   int
	ACChecked int
	Status    string // "pending", "in-progress", "completed", "blocked"
}

func parseTasks(md string) []Task {
	lines := strings.Split(md, "\n")
	var tasks []Task
	var cur *Task
	inAC := false
	inCurrentTasks := false

	for _, line := range lines {
		// Check if we've reached the "## Current Tasks" section
		if strings.TrimSpace(line) == "## Current Tasks" {
			inCurrentTasks = true
			continue
		}

		// Only parse tasks if we're in the Current Tasks section
		if !inCurrentTasks {
			continue
		}

		// Stop parsing if we hit another major section (##)
		if strings.HasPrefix(strings.TrimSpace(line), "## ") && strings.TrimSpace(line) != "## Current Tasks" {
			break
		}

		if m := reTaskHeader.FindStringSubmatch(line); m != nil {
			if cur != nil {
				tasks = append(tasks, *cur)
			}
			title := strings.TrimSpace(m[1])

			// tasks.md no longer contains status emojis - all tasks are pending by default
			// Status is determined by progress.md
			cur = &Task{Title: title, Status: "pending"}
			inAC = false
			continue
		}
		if cur == nil {
			continue
		}
		if reACHeader.MatchString(line) {
			inAC = true
			continue
		}
		if inAC && reACItem.MatchString(line) {
			cur.ACTotal++
			if reACChecked.MatchString(line) {
				cur.ACChecked++
			}
			continue
		}
		if strings.HasPrefix(line, "### ") && !reTaskHeader.MatchString(line) {
			// end section
			if cur != nil {
				tasks = append(tasks, *cur)
				cur = nil
			}
			inAC = false
			continue
		}
	}
	if cur != nil {
		tasks = append(tasks, *cur)
	}
	return tasks
}

func StatusReport(md string) string {
	ts := parseTasks(md)
	total, done, prog, pend := 0, 0, 0, 0
	var doneL, progL, pendL []string
	for _, t := range ts {
		total++
		switch {
		case t.Status == "completed" || (t.ACTotal > 0 && t.ACChecked == t.ACTotal):
			done++
			doneL = append(doneL, fmt.Sprintf("  - %s", t.Title))
		case t.Status == "in-progress" || t.ACChecked > 0:
			prog++
			progL = append(progL, fmt.Sprintf("  - %s (%d/%d criteria completed)", t.Title, t.ACChecked, t.ACTotal))
		case t.Status == "blocked":
			pend++
			pendL = append(pendL, fmt.Sprintf("  - ⚠️ %s (blocked)", t.Title))
		default:
			pend++
			pendL = append(pendL, fmt.Sprintf("  - %s", t.Title))
		}
	}
	var b strings.Builder
	b.WriteString("📊 Task Status Overview\n")
	b.WriteString("======================\n\n")

	// Show current task status at the top
	current := GetCurrentTask(md)
	if current != nil {
		b.WriteString(fmt.Sprintf("🎯 CURRENT TASK: %s (%d/%d criteria completed)\n\n", current.Title, current.ACChecked, current.ACTotal))
	} else if len(ts) > 0 {
		next := GetNextPendingTask(md)
		if next != nil {
			b.WriteString(fmt.Sprintf("🎯 NEXT TASK: %s\n\n", next.Title))
		} else {
			b.WriteString("🎯 ALL TASKS COMPLETED! 🎉\n\n")
		}
	}

	b.WriteString(fmt.Sprintf("Total Tasks: %d\n", total))
	b.WriteString(fmt.Sprintf("✅ Completed: %d\n", done))
	b.WriteString(fmt.Sprintf("🔄 In Progress: %d\n", prog))
	b.WriteString(fmt.Sprintf("⏳ Pending: %d\n\n", pend))
	if done > 0 {
		b.WriteString("✅ Completed Tasks:\n")
		b.WriteString(strings.Join(doneL, "\n"))
		b.WriteString("\n\n")
	}
	if prog > 0 {
		b.WriteString("🔄 In Progress Tasks:\n")
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

// ArchiveCompleted is deprecated - use ArchiveCompletedTasks instead
// This function is kept for backwards compatibility
func ArchiveCompleted(md string, outdir string) (archived string, remaining string, archiveFile string, err error) {
	_ = osMkdirAll(outdir)
	ts := time.Now().Format("2006-01-02_15-04-05")
	archiveFile = filepath.Join(outdir, fmt.Sprintf("completed_%s.md", ts))

	lines := strings.Split(md, "\n")
	var outRem, outArc []string
	inTask := false
	inAC := false
	keep := true
	acTotal := 0
	acChecked := 0
	var buf []string
	flush := func() {
		if len(buf) == 0 {
			return
		}
		if keep {
			outRem = append(outRem, buf...)
		} else {
			outArc = append(outArc, buf...)
		}
		buf = buf[:0]
	}
	for _, line := range lines {
		if m := reTaskHeader.FindStringSubmatch(line); m != nil {
			// finish previous
			if inTask {
				// decide keep based on AC
				keep = !(acTotal > 0 && acChecked == acTotal)
				flush()
			}
			// start new
			inTask = true
			inAC = false
			acTotal, acChecked = 0, 0
			keep = true
			buf = append(buf, line)
			continue
		}
		if inTask && reACHeader.MatchString(line) {
			inAC = true
			buf = append(buf, line)
			continue
		}
		if inTask && inAC && reACItem.MatchString(line) {
			acTotal++
			if reACChecked.MatchString(line) {
				acChecked++
			}
			buf = append(buf, line)
			continue
		}
		if inTask && strings.HasPrefix(line, "### ") && !reTaskHeader.MatchString(line) {
			// end of task section
			keep = !(acTotal > 0 && acChecked == acTotal)
			flush()
			inTask = false
			inAC = false
			buf = append(buf, line)
			continue
		}
		buf = append(buf, line)
	}
	// final flush
	if inTask {
		keep = !(acTotal > 0 && acChecked == acTotal)
		flush()
	} else {
		flush()
	}

	archived = strings.Join(outArc, "\n")
	remaining = strings.Join(outRem, "\n")
	return archived, remaining, archiveFile, nil
}

// osMkdirAll is a small wrapper to allow testing without importing os in tests
var osMkdirAll = func(path string) error { return nil }
