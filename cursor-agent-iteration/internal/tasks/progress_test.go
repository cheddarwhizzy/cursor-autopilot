package tasks

import (
	"strings"
	"testing"
)

const sampleProgressMd = `# Progress Log

## In Progress

- 🔄 [2025-01-08 19:00] Test Task 1 - working on it
- 🔄 [2025-01-08 19:05] Test Task 2 - making progress

## Completed Tasks

- ✅ [2025-01-08 18:30] Previous Task - completed successfully
- ✅ [2025-01-08 18:45] Another Task - finished
`

const emptyProgressMd = `# Progress Log

## Completed Tasks

`

const malformedProgressMd = `# Progress Log

## In Progress

- Invalid entry format
- 🔄 [2025-01-08 19:00] Valid Task - working on it

## Completed Tasks

- ✅ [2025-01-08 18:30] Valid Completed Task - done
- Invalid completed entry
`

func TestParseProgress(t *testing.T) {
	entries := ParseProgress(sampleProgressMd)

	// Should have 4 entries total
	if len(entries) != 4 {
		t.Fatalf("Expected 4 progress entries, got %d", len(entries))
	}

	// Check in-progress tasks
	if entry, exists := entries["Test Task 1"]; !exists {
		t.Errorf("Expected 'Test Task 1' to be in progress")
	} else if entry.Status != "in-progress" {
		t.Errorf("Expected 'Test Task 1' status to be 'in-progress', got '%s'", entry.Status)
	}

	if entry, exists := entries["Test Task 2"]; !exists {
		t.Errorf("Expected 'Test Task 2' to be in progress")
	} else if entry.Status != "in-progress" {
		t.Errorf("Expected 'Test Task 2' status to be 'in-progress', got '%s'", entry.Status)
	}

	// Check completed tasks
	if entry, exists := entries["Previous Task"]; !exists {
		t.Errorf("Expected 'Previous Task' to be completed")
	} else if entry.Status != "completed" {
		t.Errorf("Expected 'Previous Task' status to be 'completed', got '%s'", entry.Status)
	}

	if entry, exists := entries["Another Task"]; !exists {
		t.Errorf("Expected 'Another Task' to be completed")
	} else if entry.Status != "completed" {
		t.Errorf("Expected 'Another Task' status to be 'completed', got '%s'", entry.Status)
	}
}

func TestParseProgressEmpty(t *testing.T) {
	entries := ParseProgress("")
	if len(entries) != 0 {
		t.Errorf("Expected 0 entries for empty input, got %d", len(entries))
	}
}

func TestParseProgressMalformed(t *testing.T) {
	entries := ParseProgress(malformedProgressMd)

	// Should parse valid entries and ignore invalid ones
	if len(entries) != 2 {
		t.Errorf("Expected 2 valid entries, got %d", len(entries))
	}

	// Check that valid entries are parsed
	if _, exists := entries["Valid Task"]; !exists {
		t.Errorf("Expected 'Valid Task' to be parsed")
	}

	if _, exists := entries["Valid Completed Task"]; !exists {
		t.Errorf("Expected 'Valid Completed Task' to be parsed")
	}
}

func TestLogTaskCompletion(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		taskTitle string
		notes     string
		expected  string
	}{
		{
			name:      "empty progress file",
			input:     "",
			taskTitle: "New Task",
			notes:     "completed successfully",
			expected:  "- ✅ [",
		},
		{
			name:      "existing progress file",
			input:     sampleProgressMd,
			taskTitle: "New Task",
			notes:     "completed successfully",
			expected:  "- ✅ [",
		},
		{
			name:      "task without notes",
			input:     sampleProgressMd,
			taskTitle: "Simple Task",
			notes:     "",
			expected:  "- ✅ [",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := LogTaskCompletion(tt.input, tt.taskTitle, tt.notes)

			if !strings.Contains(result, tt.expected) {
				t.Errorf("LogTaskCompletion() result should contain %s", tt.expected)
			}

			if !strings.Contains(result, tt.taskTitle) {
				t.Errorf("LogTaskCompletion() result should contain task title '%s'", tt.taskTitle)
			}

			if tt.notes != "" && !strings.Contains(result, tt.notes) {
				t.Errorf("LogTaskCompletion() result should contain notes '%s'", tt.notes)
			}
		})
	}
}

func TestMarkTaskInProgress(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		taskTitle string
		expected  string
	}{
		{
			name:      "empty progress file",
			input:     "",
			taskTitle: "New Task",
			expected:  "- 🔄 [",
		},
		{
			name:      "existing progress file",
			input:     sampleProgressMd,
			taskTitle: "New Task",
			expected:  "- 🔄 [",
		},
		{
			name:      "progress file without In Progress section",
			input:     emptyProgressMd,
			taskTitle: "New Task",
			expected:  "## In Progress",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := MarkTaskInProgress(tt.input, tt.taskTitle)

			if !strings.Contains(result, tt.expected) {
				t.Errorf("MarkTaskInProgress() result should contain %s", tt.expected)
			}

			if !strings.Contains(result, tt.taskTitle) {
				t.Errorf("MarkTaskInProgress() result should contain task title '%s'", tt.taskTitle)
			}
		})
	}
}

func TestMoveTaskToCompleted(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		taskTitle string
		notes     string
		expected  string
	}{
		{
			name:      "move from in progress to completed",
			input:     sampleProgressMd,
			taskTitle: "Test Task 1",
			notes:     "completed successfully",
			expected:  "- ✅ [",
		},
		{
			name:      "task not in progress",
			input:     sampleProgressMd,
			taskTitle: "Non-existent Task",
			notes:     "completed",
			expected:  "- ✅ [",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := MoveTaskToCompleted(tt.input, tt.taskTitle, tt.notes)

			if !strings.Contains(result, tt.expected) {
				t.Errorf("MoveTaskToCompleted() result should contain %s", tt.expected)
			}

			if !strings.Contains(result, tt.taskTitle) {
				t.Errorf("MoveTaskToCompleted() result should contain task title '%s'", tt.taskTitle)
			}

			// Check that the task is no longer in the In Progress section
			if tt.taskTitle == "Test Task 1" {
				lines := strings.Split(result, "\n")
				inProgressSection := false
				for _, line := range lines {
					if strings.TrimSpace(line) == "## In Progress" {
						inProgressSection = true
						continue
					}
					if inProgressSection && strings.Contains(line, tt.taskTitle) && strings.Contains(line, "🔄") {
						t.Errorf("Task should not be in In Progress section after completion")
					}
					if strings.TrimSpace(line) == "## Completed Tasks" {
						inProgressSection = false
					}
				}
			}
		})
	}
}

func TestIsTaskCompleted(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		taskTitle string
		expected  bool
	}{
		{
			name:      "completed task",
			input:     sampleProgressMd,
			taskTitle: "Previous Task",
			expected:  true,
		},
		{
			name:      "in progress task",
			input:     sampleProgressMd,
			taskTitle: "Test Task 1",
			expected:  false,
		},
		{
			name:      "non-existent task",
			input:     sampleProgressMd,
			taskTitle: "Non-existent Task",
			expected:  false,
		},
		{
			name:      "empty progress",
			input:     "",
			taskTitle: "Any Task",
			expected:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsTaskCompleted(tt.input, tt.taskTitle)
			if result != tt.expected {
				t.Errorf("IsTaskCompleted() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestIsTaskInProgress(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		taskTitle string
		expected  bool
	}{
		{
			name:      "in progress task",
			input:     sampleProgressMd,
			taskTitle: "Test Task 1",
			expected:  true,
		},
		{
			name:      "completed task",
			input:     sampleProgressMd,
			taskTitle: "Previous Task",
			expected:  false,
		},
		{
			name:      "non-existent task",
			input:     sampleProgressMd,
			taskTitle: "Non-existent Task",
			expected:  false,
		},
		{
			name:      "empty progress",
			input:     "",
			taskTitle: "Any Task",
			expected:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsTaskInProgress(tt.input, tt.taskTitle)
			if result != tt.expected {
				t.Errorf("IsTaskInProgress() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestGetCompletedTasks(t *testing.T) {
	completedTasks := GetCompletedTasks(sampleProgressMd)

	expectedTasks := []string{"Previous Task", "Another Task"}
	if len(completedTasks) != len(expectedTasks) {
		t.Errorf("Expected %d completed tasks, got %d", len(expectedTasks), len(completedTasks))
	}

	for _, expectedTask := range expectedTasks {
		found := false
		for _, task := range completedTasks {
			if task == expectedTask {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected completed task '%s' not found", expectedTask)
		}
	}
}

func TestGetInProgressTasks(t *testing.T) {
	inProgressTasks := GetInProgressTasks(sampleProgressMd)

	expectedTasks := []string{"Test Task 1", "Test Task 2"}
	if len(inProgressTasks) != len(expectedTasks) {
		t.Errorf("Expected %d in-progress tasks, got %d", len(expectedTasks), len(inProgressTasks))
	}

	for _, expectedTask := range expectedTasks {
		found := false
		for _, task := range inProgressTasks {
			if task == expectedTask {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected in-progress task '%s' not found", expectedTask)
		}
	}
}

func TestGetNextPendingTaskWithProgress(t *testing.T) {
	tasksMd := `## Current Tasks

### Task: Test Task 1

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: Test Task 2

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test2.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	progressMd := `# Progress Log

## In Progress

- 🔄 [2025-01-08 19:00] Test Task 1 - working on it

## Completed Tasks

- ✅ [2025-01-08 18:30] Previous Task - completed
`

	task := GetNextPendingTaskWithProgress(tasksMd, progressMd)
	if task == nil {
		t.Errorf("Expected to find next pending task")
	} else if task.Title != "Test Task 2" {
		t.Errorf("Expected next pending task to be 'Test Task 2', got '%s'", task.Title)
	}
}

func TestGetCurrentTaskWithProgress(t *testing.T) {
	tasksMd := `## Current Tasks

### Task: Test Task 1

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	progressMd := `# Progress Log

## In Progress

- 🔄 [2025-01-08 19:00] Test Task 1 - working on it

## Completed Tasks

`

	task := GetCurrentTaskWithProgress(tasksMd, progressMd)
	if task == nil {
		t.Errorf("Expected to find current task")
	} else if task.Title != "Test Task 1" {
		t.Errorf("Expected current task to be 'Test Task 1', got '%s'", task.Title)
	}
}

func TestCompleteAllChecked(t *testing.T) {
	tasksMd := `## Current Tasks

### Task: Test Task 1

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	progressMd := `# Progress Log

## Completed Tasks

- ✅ [2025-01-08 18:30] Test Task 1 - completed
`

	result := CompleteAllChecked(tasksMd, progressMd)
	if !result {
		t.Errorf("Expected all tasks to be completed")
	}
}

func TestStatusReportWithProgress(t *testing.T) {
	tasksMd := `## Current Tasks

### Task: Test Task 1

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: Test Task 2

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test2.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	progressMd := `# Progress Log

## In Progress

- 🔄 [2025-01-08 19:00] Test Task 1 - working on it

## Completed Tasks

- ✅ [2025-01-08 18:30] Previous Task - completed
`

	report := StatusReportWithProgress(tasksMd, progressMd)

	expectedSections := []string{
		"📊 Task Status Overview",
		"Status tracked in: progress.md",
		"Task list from: tasks.md",
		"Total Tasks: 2",
		"✅ Completed: 0",
		"🔄 In Progress: 1",
		"⏳ Pending: 1",
	}

	for _, section := range expectedSections {
		if !strings.Contains(report, section) {
			t.Errorf("Status report should contain: %s", section)
		}
	}
}

func TestGetTaskProgressWithProgress(t *testing.T) {
	tasksMd := `## Current Tasks

### Task: Test Task 1

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	progressMd := `# Progress Log

## In Progress

- 🔄 [2025-01-08 19:00] Test Task 1 - working on it

## Completed Tasks

`

	progress := GetTaskProgressWithProgress(tasksMd, progressMd)
	if !strings.Contains(progress, "🔄 Working on: Test Task 1") {
		t.Errorf("Expected progress to show current task, got: %s", progress)
	}
}

func TestIsTaskCompletedAfterRun(t *testing.T) {
	tasksMd := `## Current Tasks

### Task: Test Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	progressMd := `# Progress Log

## Completed Tasks

- ✅ [2025-01-08 19:00] Test Task - completed successfully
`

	result := IsTaskCompletedAfterRun(tasksMd, progressMd, "Test Task")
	if !result {
		t.Errorf("Expected task to be completed after run")
	}
}

func TestCountInProgressTasks(t *testing.T) {
	tasksMd := `## Current Tasks

### Task: Test Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	progressMd := `# Progress Log

## In Progress

- 🔄 [2025-01-08 19:00] Test Task - working on it

## Completed Tasks

`

	count := CountInProgressTasks(tasksMd, progressMd)
	if count != 1 {
		t.Errorf("Expected 1 in-progress task, got %d", count)
	}
}

func TestGetAllInProgressTasks(t *testing.T) {
	tasksMd := `## Current Tasks

### Task: Test Task 1

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: Test Task 2

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test2.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	progressMd := `# Progress Log

## In Progress

- 🔄 [2025-01-08 19:00] Test Task 1 - working on it
- 🔄 [2025-01-08 19:05] Test Task 2 - making progress

## Completed Tasks

`

	tasks := GetAllInProgressTasks(tasksMd, progressMd)
	if len(tasks) != 2 {
		t.Errorf("Expected 2 in-progress tasks, got %d", len(tasks))
	}

	expectedTitles := []string{"Test Task 1", "Test Task 2"}
	for i, expectedTitle := range expectedTitles {
		if tasks[i].Title != expectedTitle {
			t.Errorf("Expected task %d title to be '%s', got '%s'", i, expectedTitle, tasks[i].Title)
		}
	}
}

func TestArchiveCompletedTasks(t *testing.T) {
	tasksMd := `## Current Tasks

### Task: Test Task 1

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: Test Task 2

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test2.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	progressMd := `# Progress Log

## In Progress

- 🔄 [2025-01-08 19:00] Test Task 1 - working on it

## Completed Tasks

- ✅ [2025-01-08 18:30] Test Task 2 - completed successfully
`

	archived, remainingProgress, updatedTasks, archiveFile, err := ArchiveCompletedTasks(tasksMd, progressMd, "/tmp")
	if err != nil {
		t.Fatalf("ArchiveCompletedTasks() error = %v", err)
	}

	// Check that archive file path is set
	if archiveFile == "" {
		t.Errorf("Expected archive file path to be set")
	}

	// Check that archived content contains completed task
	if !strings.Contains(archived, "Test Task 2") {
		t.Errorf("Archived content should contain completed task")
	}

	// Check that remaining progress doesn't contain completed task
	if strings.Contains(remainingProgress, "Test Task 2") {
		t.Errorf("Remaining progress should not contain completed task")
	}

	// Check that updated tasks doesn't contain completed task
	if strings.Contains(updatedTasks, "Test Task 2") {
		t.Errorf("Updated tasks should not contain completed task")
	}
}

func TestExtractTaskDetails(t *testing.T) {
	tasksMd := `## Current Tasks

### Task: Test Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: Another Task

**Context:** Another context
**Acceptance Criteria:**

* [ ] Another criterion

**Files to Modify:** another.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	// Test extracting existing task
	result := ExtractTaskDetails(tasksMd, "Test Task")
	if !strings.Contains(result, "### Task: Test Task") {
		t.Errorf("Extracted task details should contain task header")
	}
	if !strings.Contains(result, "**Context:** Test context") {
		t.Errorf("Extracted task details should contain context")
	}
	if !strings.Contains(result, "**Acceptance Criteria:**") {
		t.Errorf("Extracted task details should contain acceptance criteria")
	}

	// Test extracting non-existent task
	result = ExtractTaskDetails(tasksMd, "Non-existent Task")
	if !strings.Contains(result, "Task not found in tasks.md") {
		t.Errorf("Should return error message for non-existent task")
	}
}
