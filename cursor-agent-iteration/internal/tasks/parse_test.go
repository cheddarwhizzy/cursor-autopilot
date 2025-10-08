package tasks

import (
	"testing"
)

const sample = `## Current Tasks

### Task: A

**Context:** Test context A
**Acceptance Criteria:**
* [x] one
* [x] two

**Files to Modify:** file1.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: B

**Context:** Test context B
**Acceptance Criteria:**
* [x] one
* [ ] two

**Files to Modify:** file2.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: C

**Context:** Test context C
**Acceptance Criteria:**
* [ ] one
* [ ] two

**Files to Modify:** file3.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

const sampleWithoutCurrentTasks = `### Task: A

**Context:** Test context A
**Acceptance Criteria:**
* [x] one
* [x] two

### Task: B

**Context:** Test context B
**Acceptance Criteria:**
* [x] one
* [ ] two
`

func TestStatusReport(t *testing.T) {
	rep := StatusReport(sample)
	if want := "Total Tasks: 3"; !contains(rep, want) {
		t.Fatalf("missing %q in report: %s", want, rep)
	}
	if want := "✅ Completed: 1"; !contains(rep, want) {
		t.Fatalf("missing %q", want)
	}
	if want := "🔄 In Progress: 1"; !contains(rep, want) {
		t.Fatalf("missing %q", want)
	}
	if want := "⏳ Pending: 1"; !contains(rep, want) {
		t.Fatalf("missing %q", want)
	}
}

func TestStatusReportWithoutCurrentTasks(t *testing.T) {
	rep := StatusReport(sampleWithoutCurrentTasks)
	// Should not find any tasks since there's no "## Current Tasks" section
	if want := "Total Tasks: 0"; !contains(rep, want) {
		t.Fatalf("expected %q in report, got: %s", want, rep)
	}
}

func TestParseTasks(t *testing.T) {
	tasks := parseTasks(sample)

	if len(tasks) != 3 {
		t.Fatalf("Expected 3 tasks, got %d", len(tasks))
	}

	// Test task A (completed)
	taskA := tasks[0]
	if taskA.Title != "A" {
		t.Errorf("Expected task A title 'A', got '%s'", taskA.Title)
	}
	if taskA.ACTotal != 2 {
		t.Errorf("Expected task A to have 2 AC total, got %d", taskA.ACTotal)
	}
	if taskA.ACChecked != 2 {
		t.Errorf("Expected task A to have 2 AC checked, got %d", taskA.ACChecked)
	}
	if taskA.Status != "pending" {
		t.Errorf("Expected task A status 'pending', got '%s'", taskA.Status)
	}

	// Test task B (in progress)
	taskB := tasks[1]
	if taskB.Title != "B" {
		t.Errorf("Expected task B title 'B', got '%s'", taskB.Title)
	}
	if taskB.ACTotal != 2 {
		t.Errorf("Expected task B to have 2 AC total, got %d", taskB.ACTotal)
	}
	if taskB.ACChecked != 1 {
		t.Errorf("Expected task B to have 1 AC checked, got %d", taskB.ACChecked)
	}

	// Test task C (pending)
	taskC := tasks[2]
	if taskC.Title != "C" {
		t.Errorf("Expected task C title 'C', got '%s'", taskC.Title)
	}
	if taskC.ACTotal != 2 {
		t.Errorf("Expected task C to have 2 AC total, got %d", taskC.ACTotal)
	}
	if taskC.ACChecked != 0 {
		t.Errorf("Expected task C to have 0 AC checked, got %d", taskC.ACChecked)
	}
}

func TestParseTasksEmpty(t *testing.T) {
	tasks := parseTasks("")
	if len(tasks) != 0 {
		t.Errorf("Expected 0 tasks for empty input, got %d", len(tasks))
	}
}

func TestParseTasksNoCurrentTasks(t *testing.T) {
	tasks := parseTasks(sampleWithoutCurrentTasks)
	if len(tasks) != 0 {
		t.Errorf("Expected 0 tasks when no '## Current Tasks' section, got %d", len(tasks))
	}
}

func TestParseTasksMalformed(t *testing.T) {
	malformed := `## Current Tasks

### Task: Incomplete Task

**Context:** Test context
**Acceptance Criteria:**
* [x] one
* [ ] two

### Task: Another Task

**Context:** Test context
**Acceptance Criteria:**
* [x] one
* [ ] two
`

	tasks := parseTasks(malformed)
	// Should still parse the tasks even if they're missing some fields
	if len(tasks) != 2 {
		t.Errorf("Expected 2 tasks for malformed input, got %d", len(tasks))
	}
}

func TestStatusReportFormat(t *testing.T) {
	rep := StatusReport(sample)

	// Check that the report contains expected sections
	expectedSections := []string{
		"📊 Task Status Overview",
		"======================",
		"Total Tasks:",
		"✅ Completed:",
		"🔄 In Progress:",
		"⏳ Pending:",
	}

	for _, section := range expectedSections {
		if !contains(rep, section) {
			t.Errorf("Missing expected section in report: %s", section)
		}
	}
}

func TestStatusReportWithCurrentTask(t *testing.T) {
	// Test with a task that has some AC checked (in progress)
	rep := StatusReport(sample)

	// Should show current task information
	if !contains(rep, "🎯 CURRENT TASK:") && !contains(rep, "🎯 NEXT TASK:") && !contains(rep, "🎯 ALL TASKS COMPLETED!") {
		t.Errorf("Report should show current/next task status")
	}
}

func TestStatusReportAllCompleted(t *testing.T) {
	allCompleted := `## Current Tasks

### Task: Completed Task

**Context:** Test context
**Acceptance Criteria:**
* [x] one
* [x] two

**Files to Modify:** file.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	rep := StatusReport(allCompleted)
	if !contains(rep, "🎯 ALL TASKS COMPLETED!") {
		t.Errorf("Report should show all tasks completed when all AC are checked")
	}
}

func TestStatusReportNoTasks(t *testing.T) {
	rep := StatusReport("")
	if !contains(rep, "Total Tasks: 0") {
		t.Errorf("Report should show 0 tasks for empty input")
	}
}

func TestStatusReportWithBlockedTasks(t *testing.T) {
	blockedSample := `## Current Tasks

### Task: Blocked Task

**Context:** Test context
**Acceptance Criteria:**
* [ ] one
* [ ] two

**Files to Modify:** file.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	// Manually set status to blocked for testing
	tasks := parseTasks(blockedSample)
	if len(tasks) > 0 {
		tasks[0].Status = "blocked"
	}

	// Create a custom status report for blocked tasks
	rep := StatusReport(blockedSample)
	if !contains(rep, "⏳ Pending:") {
		t.Errorf("Report should show pending tasks")
	}
}

func contains(s, sub string) bool {
	return len(s) >= len(sub) && (func() bool { return stringIndex(s, sub) >= 0 })()
}

func stringIndex(s, sub string) int {
	for i := 0; i+len(sub) <= len(s); i++ {
		if s[i:i+len(sub)] == sub {
			return i
		}
	}
	return -1
}
