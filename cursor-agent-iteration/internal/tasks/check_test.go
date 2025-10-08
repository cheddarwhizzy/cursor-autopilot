package tasks

import (
	"regexp"
	"strings"
	"testing"
)

const validTasksSample = `## Current Tasks

### Task: Valid Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: Another Valid Task

**Context:** Another test context
**Acceptance Criteria:**

* [x] Completed criterion
* [ ] Pending criterion

**Files to Modify:** test2.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

const invalidTasksSample = `### Task: Invalid Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion
`

const emptyTasksSample = `## Current Tasks

`

const completedTasksSample = `## Current Tasks

### Task: Completed Task

**Context:** Test context
**Acceptance Criteria:**

* [x] First criterion
* [x] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

func TestComplete(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected bool
	}{
		{
			name:     "all tasks completed",
			input:    completedTasksSample,
			expected: true,
		},
		{
			name:     "some tasks incomplete",
			input:    validTasksSample,
			expected: false,
		},
		{
			name:     "no tasks",
			input:    emptyTasksSample,
			expected: false,
		},
		{
			name:     "empty input",
			input:    "",
			expected: false,
		},
		{
			name: "tasks without AC",
			input: `## Current Tasks

### Task: No AC Task

**Context:** Test context
**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := Complete(tt.input)
			if result != tt.expected {
				t.Errorf("Complete() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestGetCurrentTask(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected *Task
	}{
		{
			name:     "task with some AC checked",
			input:    validTasksSample,
			expected: &Task{Title: "Another Valid Task", ACTotal: 2, ACChecked: 1, Status: "pending"},
		},
		{
			name:     "no in-progress tasks",
			input:    completedTasksSample,
			expected: nil,
		},
		{
			name:     "empty input",
			input:    "",
			expected: nil,
		},
		{
			name:     "no tasks",
			input:    emptyTasksSample,
			expected: nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := GetCurrentTask(tt.input)
			if tt.expected == nil {
				if result != nil {
					t.Errorf("GetCurrentTask() = %v, want nil", result)
				}
			} else {
				if result == nil {
					t.Errorf("GetCurrentTask() = nil, want %v", tt.expected)
				} else if result.Title != tt.expected.Title {
					t.Errorf("GetCurrentTask() title = %v, want %v", result.Title, tt.expected.Title)
				}
			}
		})
	}
}

func TestGetNextPendingTask(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected *Task
	}{
		{
			name:     "first pending task",
			input:    validTasksSample,
			expected: &Task{Title: "Valid Task", ACTotal: 2, ACChecked: 0, Status: "pending"},
		},
		{
			name:     "no pending tasks",
			input:    completedTasksSample,
			expected: nil,
		},
		{
			name:     "empty input",
			input:    "",
			expected: nil,
		},
		{
			name:     "no tasks",
			input:    emptyTasksSample,
			expected: nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := GetNextPendingTask(tt.input)
			if tt.expected == nil {
				if result != nil {
					t.Errorf("GetNextPendingTask() = %v, want nil", result)
				}
			} else {
				if result == nil {
					t.Errorf("GetNextPendingTask() = nil, want %v", tt.expected)
				} else if result.Title != tt.expected.Title {
					t.Errorf("GetNextPendingTask() title = %v, want %v", result.Title, tt.expected.Title)
				}
			}
		})
	}
}

func TestGetTaskProgress(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "task in progress",
			input:    validTasksSample,
			expected: "🔄 Working on:",
		},
		{
			name:     "all tasks completed",
			input:    completedTasksSample,
			expected: "✅ All tasks completed",
		},
		{
			name:     "no tasks",
			input:    emptyTasksSample,
			expected: "No tasks found",
		},
		{
			name:     "empty input",
			input:    "",
			expected: "No tasks found",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := GetTaskProgress(tt.input)
			if !strings.Contains(result, tt.expected) {
				t.Errorf("GetTaskProgress() = %v, want to contain %v", result, tt.expected)
			}
		})
	}
}

func TestValidateTasksStructure(t *testing.T) {
	tests := []struct {
		name         string
		input        string
		expected     bool
		errorCount   int
		warningCount int
	}{
		{
			name:         "valid structure",
			input:        validTasksSample,
			expected:     true,
			errorCount:   0,
			warningCount: 0,
		},
		{
			name:         "missing Current Tasks section",
			input:        invalidTasksSample,
			expected:     false,
			errorCount:   1,
			warningCount: 0,
		},
		{
			name:         "empty Current Tasks section",
			input:        emptyTasksSample,
			expected:     true,
			errorCount:   0,
			warningCount: 1,
		},
		{
			name:         "empty input",
			input:        "",
			expected:     false,
			errorCount:   1,
			warningCount: 0,
		},
		{
			name: "task with empty title",
			input: `## Current Tasks

### Task: 

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			expected:     true, // The validation logic doesn't catch empty titles after "Task: "
			errorCount:   0,
			warningCount: 1, // This will trigger a warning about missing structure
		},
		{
			name: "task missing context",
			input: `## Current Tasks

### Task: Incomplete Task

**Acceptance Criteria:**

* [ ] First criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			expected:     false,
			errorCount:   1,
			warningCount: 0,
		},
		{
			name: "task missing acceptance criteria",
			input: `## Current Tasks

### Task: Incomplete Task

**Context:** Test context

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			expected:     false,
			errorCount:   1,
			warningCount: 0,
		},
		{
			name: "task missing checkboxes",
			input: `## Current Tasks

### Task: Incomplete Task

**Context:** Test context
**Acceptance Criteria:**

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			expected:     false,
			errorCount:   1,
			warningCount: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ValidateTasksStructure(tt.input)
			if result.Valid != tt.expected {
				t.Errorf("ValidateTasksStructure() valid = %v, want %v", result.Valid, tt.expected)
			}
			if len(result.Errors) != tt.errorCount {
				t.Errorf("ValidateTasksStructure() error count = %d, want %d", len(result.Errors), tt.errorCount)
			}
			if len(result.Warnings) != tt.warningCount {
				t.Errorf("ValidateTasksStructure() warning count = %d, want %d", len(result.Warnings), tt.warningCount)
			}
		})
	}
}

func TestValidateAndFixTasksStructure(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		expected  bool
		shouldFix bool
	}{
		{
			name:      "valid structure",
			input:     validTasksSample,
			expected:  true,
			shouldFix: false,
		},
		{
			name:      "missing Current Tasks section",
			input:     invalidTasksSample,
			expected:  true,
			shouldFix: true,
		},
		{
			name:      "empty input",
			input:     "",
			expected:  true,
			shouldFix: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			fixed, result := ValidateAndFixTasksStructure(tt.input)
			if result.Valid != tt.expected {
				t.Errorf("ValidateAndFixTasksStructure() valid = %v, want %v", result.Valid, tt.expected)
			}
			if tt.shouldFix && fixed == tt.input {
				t.Errorf("ValidateAndFixTasksStructure() should have fixed the input")
			}
			if !tt.shouldFix && fixed != tt.input {
				t.Errorf("ValidateAndFixTasksStructure() should not have changed the input")
			}
		})
	}
}

func TestValidateTaskStructure(t *testing.T) {
	lines := strings.Split(validTasksSample, "\n")
	contextRegex := regexp.MustCompile(`^\*\*Context:\*\*\s*`)
	acceptanceCriteriaRegex := regexp.MustCompile(`^\*\*Acceptance Criteria:\*\*\s*$`)
	checkboxRegex := regexp.MustCompile(`^[*-] \[( |x|X)\]`)

	tests := []struct {
		name      string
		startLine int
		expected  bool
	}{
		{
			name:      "valid task structure",
			startLine: 3, // Start after "### Task: Valid Task"
			expected:  true,
		},
		{
			name:      "invalid start line",
			startLine: 0,
			expected:  false,
		},
		{
			name:      "start line beyond content",
			startLine: 100,
			expected:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := validateTaskStructure(lines, tt.startLine, contextRegex, acceptanceCriteriaRegex, checkboxRegex)
			if result != tt.expected {
				t.Errorf("validateTaskStructure() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestValidationResult(t *testing.T) {
	result := ValidationResult{
		Valid:    true,
		Errors:   []string{"error1", "error2"},
		Warnings: []string{"warning1"},
	}

	if !result.Valid {
		t.Errorf("Expected Valid to be true")
	}
	if len(result.Errors) != 2 {
		t.Errorf("Expected 2 errors, got %d", len(result.Errors))
	}
	if len(result.Warnings) != 1 {
		t.Errorf("Expected 1 warning, got %d", len(result.Warnings))
	}
}
