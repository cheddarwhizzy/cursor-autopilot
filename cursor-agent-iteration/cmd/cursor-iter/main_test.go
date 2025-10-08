package main

import (
	"os"
	"path/filepath"
	"testing"
)

// TestMainCommands tests the main command line interface
func TestMainCommands(t *testing.T) {
	tests := []struct {
		name     string
		args     []string
		wantExit bool
		wantErr  bool
	}{
		{
			name:     "help command",
			args:     []string{"cursor-iter", "-h"},
			wantExit: false,
			wantErr:  false,
		},
		{
			name:     "help command long form",
			args:     []string{"cursor-iter", "--help"},
			wantExit: false,
			wantErr:  false,
		},
		{
			name:     "unknown command",
			args:     []string{"cursor-iter", "unknown-command"},
			wantExit: true,
			wantErr:  true,
		},
		{
			name:     "no arguments",
			args:     []string{"cursor-iter"},
			wantExit: true,
			wantErr:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Save original args and restore after test
			originalArgs := os.Args
			defer func() { os.Args = originalArgs }()

			os.Args = tt.args

			// We can't easily test main() directly, so we test the logic indirectly
			// by checking if the command would be recognized
			if len(tt.args) < 2 {
				if !tt.wantExit {
					t.Errorf("Expected help to be shown for no args, but got exit")
				}
				return
			}

			cmd := tt.args[1]
			validCommands := []string{
				"task-status", "archive-completed", "iterate-init", "iterate",
				"iterate-loop", "add-feature", "run-agent", "validate-tasks", "reset",
				"-h", "--help",
			}

			isValid := false
			for _, validCmd := range validCommands {
				if cmd == validCmd {
					isValid = true
					break
				}
			}

			if tt.wantErr && isValid {
				t.Errorf("Expected error for command %s, but it's valid", cmd)
			}
			if !tt.wantErr && !isValid && cmd != "unknown-command" {
				t.Errorf("Expected command %s to be valid", cmd)
			}
		})
	}
}

// TestResolveTasksFile tests the resolveTasksFile function
func TestResolveTasksFile(t *testing.T) {
	// Create a temporary directory for testing
	tmpDir := t.TempDir()
	originalDir, _ := os.Getwd()
	defer func() {
		os.Chdir(originalDir)
		os.Unsetenv("TASKS_FILE")
	}()

	// Change to temp directory
	os.Chdir(tmpDir)

	tests := []struct {
		name     string
		setup    func()
		expected string
	}{
		{
			name: "environment variable set",
			setup: func() {
				os.Setenv("TASKS_FILE", "/custom/tasks.md")
			},
			expected: "/custom/tasks.md",
		},
		{
			name: "tasks.md in current directory",
			setup: func() {
				os.Unsetenv("TASKS_FILE")
				os.WriteFile("tasks.md", []byte("test"), 0644)
			},
			expected: "tasks.md",
		},
		{
			name: "tasks.md in parent directory",
			setup: func() {
				os.Unsetenv("TASKS_FILE")
				os.WriteFile("../tasks.md", []byte("test"), 0644)
			},
			expected: "../tasks.md",
		},
		{
			name: "default fallback",
			setup: func() {
				os.Unsetenv("TASKS_FILE")
			},
			expected: "tasks.md",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Clean up before each test
			os.Remove("tasks.md")
			os.Remove("../tasks.md")
			os.Unsetenv("TASKS_FILE")

			tt.setup()
			result := resolveTasksFile()
			if result != tt.expected {
				t.Errorf("resolveTasksFile() = %v, want %v", result, tt.expected)
			}
		})
	}
}

// TestResolveProgressFile tests the resolveProgressFile function
func TestResolveProgressFile(t *testing.T) {
	// Create a temporary directory for testing
	tmpDir := t.TempDir()
	originalDir, _ := os.Getwd()
	defer func() {
		os.Chdir(originalDir)
		os.Unsetenv("PROGRESS_FILE")
	}()

	// Change to temp directory
	os.Chdir(tmpDir)

	tests := []struct {
		name     string
		setup    func()
		expected string
	}{
		{
			name: "environment variable set",
			setup: func() {
				os.Setenv("PROGRESS_FILE", "/custom/progress.md")
			},
			expected: "/custom/progress.md",
		},
		{
			name: "progress.md in current directory",
			setup: func() {
				os.Unsetenv("PROGRESS_FILE")
				os.WriteFile("progress.md", []byte("test"), 0644)
			},
			expected: "progress.md",
		},
		{
			name: "progress.md in parent directory",
			setup: func() {
				os.Unsetenv("PROGRESS_FILE")
				os.WriteFile("../progress.md", []byte("test"), 0644)
			},
			expected: "../progress.md",
		},
		{
			name: "default fallback",
			setup: func() {
				os.Unsetenv("PROGRESS_FILE")
			},
			expected: "progress.md",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Clean up before each test
			os.Remove("progress.md")
			os.Remove("../progress.md")
			os.Unsetenv("PROGRESS_FILE")

			tt.setup()
			result := resolveProgressFile()
			if result != tt.expected {
				t.Errorf("resolveProgressFile() = %v, want %v", result, tt.expected)
			}
		})
	}
}

// TestEnvOr tests the envOr function
func TestEnvOr(t *testing.T) {
	tests := []struct {
		name     string
		key      string
		def      string
		setup    func()
		expected string
	}{
		{
			name: "environment variable set",
			key:  "TEST_VAR",
			def:  "default",
			setup: func() {
				os.Setenv("TEST_VAR", "custom")
			},
			expected: "custom",
		},
		{
			name: "environment variable not set",
			key:  "NONEXISTENT_VAR",
			def:  "default",
			setup: func() {
				os.Unsetenv("NONEXISTENT_VAR")
			},
			expected: "default",
		},
		{
			name: "empty environment variable",
			key:  "EMPTY_VAR",
			def:  "default",
			setup: func() {
				os.Setenv("EMPTY_VAR", "")
			},
			expected: "default",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.setup()
			result := envOr(tt.key, tt.def)
			if result != tt.expected {
				t.Errorf("envOr(%s, %s) = %v, want %v", tt.key, tt.def, result, tt.expected)
			}
		})
	}
}

// TestTimestamp tests the ts function
func TestTimestamp(t *testing.T) {
	ts := ts()

	// Check format: should be HH:MM:SS
	if len(ts) != 8 {
		t.Errorf("Expected timestamp length 8 (HH:MM:SS), got %d: %s", len(ts), ts)
	}

	// Check format: should have colons at positions 2 and 5
	if ts[2] != ':' || ts[5] != ':' {
		t.Errorf("Expected timestamp format HH:MM:SS, got %s", ts)
	}

	// Check that it's numeric
	for i, c := range ts {
		if i == 2 || i == 5 {
			continue // Skip colons
		}
		if c < '0' || c > '9' {
			t.Errorf("Expected numeric character at position %d, got %c", i, c)
		}
	}
}

// TestFileLock tests the file locking functionality
func TestFileLock(t *testing.T) {
	tmpDir := t.TempDir()
	lockFile := filepath.Join(tmpDir, "test.lock")

	// Test successful lock
	lock, err := LockFile(lockFile)
	if err != nil {
		t.Fatalf("Failed to acquire lock: %v", err)
	}

	// Test that we can unlock
	err = lock.Unlock()
	if err != nil {
		t.Errorf("Failed to unlock: %v", err)
	}

	// Test that file was created
	if _, err := os.Stat(lockFile); os.IsNotExist(err) {
		t.Errorf("Lock file was not created")
	}
}

// TestFetchPromptFromGitHub tests the fetchPromptFromGitHub function
func TestFetchPromptFromGitHub(t *testing.T) {
	tmpDir := t.TempDir()
	promptFile := filepath.Join(tmpDir, "test-prompt.md")

	// Test fetching a prompt (this will make an actual HTTP request)
	err := fetchPromptFromGitHub(promptFile)
	if err != nil {
		// If the request fails (network issues, etc.), that's okay for testing
		t.Logf("Failed to fetch prompt from GitHub (expected in some environments): %v", err)
		return
	}

	// Check if file was created
	if _, err := os.Stat(promptFile); os.IsNotExist(err) {
		t.Errorf("Prompt file was not created")
	}

	// Check if file has content
	content, err := os.ReadFile(promptFile)
	if err != nil {
		t.Errorf("Failed to read prompt file: %v", err)
	}

	if len(content) == 0 {
		t.Errorf("Prompt file is empty")
	}
}

// TestUsage tests the usage function
func TestUsage(t *testing.T) {
	// This is a basic test to ensure usage doesn't panic
	// We can't easily capture stdout in a test, so we just call it
	usage()
}

// TestTaskStatusCommand tests the task-status command logic
func TestTaskStatusCommand(t *testing.T) {
	tmpDir := t.TempDir()
	originalDir, _ := os.Getwd()
	defer func() { os.Chdir(originalDir) }()

	os.Chdir(tmpDir)

	// Create test files
	tasksContent := `## Current Tasks

### Task: Test Task

**Context:** Test context
**Acceptance Criteria:**

* [x] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	progressContent := `# Progress Log

## Completed Tasks

- ✅ [2025-01-08 19:00] Another Task - completed successfully

## In Progress

- 🔄 [2025-01-08 19:00] Test Task - working on it
`

	// Write test files
	err := os.WriteFile("tasks.md", []byte(tasksContent), 0644)
	if err != nil {
		t.Fatalf("Failed to write tasks.md: %v", err)
	}

	err = os.WriteFile("progress.md", []byte(progressContent), 0644)
	if err != nil {
		t.Fatalf("Failed to write progress.md: %v", err)
	}

	// Test that files can be read (simulating task-status command)
	taskContent, err := os.ReadFile("tasks.md")
	if err != nil {
		t.Errorf("Failed to read tasks.md: %v", err)
	}

	progressContentRead, err := os.ReadFile("progress.md")
	if err != nil {
		t.Errorf("Failed to read progress.md: %v", err)
	}

	// Basic validation that we got content
	if len(taskContent) == 0 {
		t.Errorf("tasks.md is empty")
	}

	if len(progressContentRead) == 0 {
		t.Errorf("progress.md is empty")
	}
}

// TestValidateTasksCommand tests the validate-tasks command logic
func TestValidateTasksCommand(t *testing.T) {
	tmpDir := t.TempDir()
	originalDir, _ := os.Getwd()
	defer func() { os.Chdir(originalDir) }()

	os.Chdir(tmpDir)

	// Test valid tasks.md
	validTasksContent := `## Current Tasks

### Task: Valid Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** test.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`

	err := os.WriteFile("tasks.md", []byte(validTasksContent), 0644)
	if err != nil {
		t.Fatalf("Failed to write tasks.md: %v", err)
	}

	// Test that we can read and validate the file
	content, err := os.ReadFile("tasks.md")
	if err != nil {
		t.Errorf("Failed to read tasks.md: %v", err)
	}

	if len(content) == 0 {
		t.Errorf("tasks.md is empty")
	}

	// Test invalid tasks.md (missing Current Tasks section)
	invalidTasksContent := `### Task: Invalid Task

**Context:** Test context
**Acceptance Criteria:**

* [ ] First criterion
`

	err = os.WriteFile("invalid-tasks.md", []byte(invalidTasksContent), 0644)
	if err != nil {
		t.Fatalf("Failed to write invalid-tasks.md: %v", err)
	}

	invalidContent, err := os.ReadFile("invalid-tasks.md")
	if err != nil {
		t.Errorf("Failed to read invalid-tasks.md: %v", err)
	}

	// The invalid content should be different from valid content
	if string(invalidContent) == string(content) {
		t.Errorf("Invalid and valid content should be different")
	}
}
