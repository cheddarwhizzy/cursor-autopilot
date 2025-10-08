package tasks

import (
	"strings"
	"testing"
)

func TestIsTaskCompletedAfterRun(t *testing.T) {
	tests := []struct {
		name       string
		tasksMd    string
		progressMd string
		taskTitle  string
		expected   bool
	}{
		{
			name: "task completed in progress.md",
			tasksMd: `## Current Tasks

### Task: Test Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			progressMd: `# Progress Log

## Completed Tasks

- ✅ [2025-01-08 19:00] Test Task - completed successfully
`,
			taskTitle: "Test Task",
			expected:  true,
		},
		{
			name: "task with all AC checked",
			tasksMd: `## Current Tasks

### Task: Test Task

**Context:** Test context
**Acceptance Criteria:**

* [x] First criterion
* [x] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			progressMd: `# Progress Log

## Completed Tasks
`,
			taskTitle: "Test Task",
			expected:  true,
		},
		{
			name: "task not completed",
			tasksMd: `## Current Tasks

### Task: Test Task

**Context:** Test context
**Acceptance Criteria:**

* [x] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			progressMd: `# Progress Log

## Completed Tasks
`,
			taskTitle: "Test Task",
			expected:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := IsTaskCompletedAfterRun(tt.tasksMd, tt.progressMd, tt.taskTitle)
			if result != tt.expected {
				t.Errorf("IsTaskCompletedAfterRun() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestCountInProgressTasks(t *testing.T) {
	tests := []struct {
		name       string
		tasksMd    string
		progressMd string
		expected   int
	}{
		{
			name: "two in-progress tasks",
			tasksMd: `## Current Tasks

### Task: 🔄 First In-Progress Task

**Context:** Test context
**Acceptance Criteria:**

* [x] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: 🔄 Second In-Progress Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test2.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: Pending Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test3.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			progressMd: `# Progress Log

## Completed Tasks
`,
			expected: 2,
		},
		{
			name: "one in-progress task with partial AC",
			tasksMd: `## Current Tasks

### Task: Test Task

**Context:** Test context
**Acceptance Criteria:**

* [x] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			progressMd: `# Progress Log

## Completed Tasks
`,
			expected: 1,
		},
		{
			name: "no in-progress tasks",
			tasksMd: `## Current Tasks

### Task: Pending Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			progressMd: `# Progress Log

## Completed Tasks
`,
			expected: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := CountInProgressTasks(tt.tasksMd, tt.progressMd)
			if result != tt.expected {
				t.Errorf("CountInProgressTasks() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestGetAllInProgressTasks(t *testing.T) {
	tests := []struct {
		name          string
		tasksMd       string
		progressMd    string
		expectedCount int
		expectedFirst string
	}{
		{
			name: "multiple in-progress tasks",
			tasksMd: `## Current Tasks

### Task: 🔄 First In-Progress Task

**Context:** Test context
**Acceptance Criteria:**

* [x] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: 🔄 Second In-Progress Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test2.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: Pending Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test3.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			progressMd:    `# Progress Log\n\n## Completed Tasks\n`,
			expectedCount: 2,
			expectedFirst: "First In-Progress Task",
		},
		{
			name: "no in-progress tasks",
			tasksMd: `## Current Tasks

### Task: Pending Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			progressMd:    `# Progress Log\n\n## Completed Tasks\n`,
			expectedCount: 0,
			expectedFirst: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := GetAllInProgressTasks(tt.tasksMd, tt.progressMd)
			if len(result) != tt.expectedCount {
				t.Errorf("GetAllInProgressTasks() returned %v tasks, want %v", len(result), tt.expectedCount)
			}
			if tt.expectedCount > 0 && result[0].Title != tt.expectedFirst {
				t.Errorf("GetAllInProgressTasks() first task = %v, want %v", result[0].Title, tt.expectedFirst)
			}
		})
	}
}

func TestExtractTaskDetails(t *testing.T) {
	tests := []struct {
		name             string
		tasksMd          string
		taskTitle        string
		expectedContains []string
	}{
		{
			name: "extract complete task details",
			tasksMd: `## Current Tasks

### Task: Add user authentication

**Context:** Implement JWT-based authentication
**Acceptance Criteria:**

* [ ] Create authentication middleware
* [ ] Add JWT token generation
* [ ] Implement login endpoint

**Files to Modify:** auth.go, middleware.go
**Tests:** unit / integration
**Labels:** [type:feature] [priority:high]
**Dependencies:** None

### Task: Another Task

**Context:** Something else
**Acceptance Criteria:**

* [ ] Do something

**Files to Modify:** other.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			taskTitle: "Add user authentication",
			expectedContains: []string{
				"### Task: Add user authentication",
				"**Context:** Implement JWT-based authentication",
				"**Acceptance Criteria:**",
				"* [ ] Create authentication middleware",
				"* [ ] Add JWT token generation",
				"* [ ] Implement login endpoint",
				"**Files to Modify:** auth.go, middleware.go",
				"**Tests:** unit / integration",
				"**Labels:** [type:feature] [priority:high]",
				"**Dependencies:** None",
			},
		},
		{
			name: "extract task with emoji",
			tasksMd: `## Current Tasks

### Task: 🔄 In Progress Task

**Context:** Working on this
**Acceptance Criteria:**

* [x] First step
* [ ] Second step

**Files to Modify:** progress.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			taskTitle: "In Progress Task",
			expectedContains: []string{
				"### Task: 🔄 In Progress Task",
				"**Context:** Working on this",
				"* [x] First step",
				"* [ ] Second step",
			},
		},
		{
			name: "task not found",
			tasksMd: `## Current Tasks

### Task: Existing Task

**Context:** Some context
**Acceptance Criteria:**

* [ ] Criterion

**Files to Modify:** file.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`,
			taskTitle: "Nonexistent Task",
			expectedContains: []string{
				"Task not found in tasks.md",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ExtractTaskDetails(tt.tasksMd, tt.taskTitle)
			for _, expected := range tt.expectedContains {
				if !strings.Contains(result, expected) {
					t.Errorf("ExtractTaskDetails() result missing expected string:\n  Expected: %q\n  Got: %q", expected, result)
				}
			}
		})
	}
}

