package testutils

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

// TestFile represents a test file with content
type TestFile struct {
	Name    string
	Content string
	Mode    os.FileMode
}

// TestDir represents a test directory structure
type TestDir struct {
	Name  string
	Files []TestFile
	Dirs  []TestDir
}

// CreateTestDir creates a test directory structure
func CreateTestDir(t *testing.T, structure TestDir) string {
	rootDir := t.TempDir()
	createTestDirRecursive(t, rootDir, structure)
	return rootDir
}

// createTestDirRecursive recursively creates the test directory structure
func createTestDirRecursive(t *testing.T, basePath string, structure TestDir) {
	dirPath := filepath.Join(basePath, structure.Name)

	// Create directory
	err := os.MkdirAll(dirPath, 0755)
	if err != nil {
		t.Fatalf("Failed to create directory %s: %v", dirPath, err)
	}

	// Create files
	for _, file := range structure.Files {
		filePath := filepath.Join(dirPath, file.Name)
		mode := file.Mode
		if mode == 0 {
			mode = 0644
		}
		err := os.WriteFile(filePath, []byte(file.Content), mode)
		if err != nil {
			t.Fatalf("Failed to create file %s: %v", filePath, err)
		}
	}

	// Create subdirectories
	for _, subDir := range structure.Dirs {
		createTestDirRecursive(t, dirPath, subDir)
	}
}

// CreateTestTasksFile creates a test tasks.md file
func CreateTestTasksFile(t *testing.T, dir string, content string) string {
	filePath := filepath.Join(dir, "tasks.md")
	err := os.WriteFile(filePath, []byte(content), 0644)
	if err != nil {
		t.Fatalf("Failed to create tasks.md: %v", err)
	}
	return filePath
}

// CreateTestProgressFile creates a test progress.md file
func CreateTestProgressFile(t *testing.T, dir string, content string) string {
	filePath := filepath.Join(dir, "progress.md")
	err := os.WriteFile(filePath, []byte(content), 0644)
	if err != nil {
		t.Fatalf("Failed to create progress.md: %v", err)
	}
	return filePath
}

// SampleTasksContent returns sample tasks.md content
func SampleTasksContent() string {
	return `## Current Tasks

### Task: Test Task 1

**Context:** First test task
**Acceptance Criteria:**

* [ ] First criterion
* [ ] Second criterion

**Files to Modify:** file1.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None

### Task: Test Task 2

**Context:** Second test task
**Acceptance Criteria:**

* [x] Completed criterion
* [ ] Pending criterion

**Files to Modify:** file2.go
**Tests:** unit
**Labels:** [type:feature]
**Dependencies:** None
`
}

// SampleProgressContent returns sample progress.md content
func SampleProgressContent() string {
	return `# Progress Log

## Completed Tasks

- ✅ [2025-01-08 19:00] Previous Task - completed successfully

## In Progress

- 🔄 [2025-01-08 19:00] Test Task 2 - working on it
`
}

// SampleArchitectureContent returns sample architecture.md content
func SampleArchitectureContent() string {
	return `# Architecture Overview

## System Components

### Core Components
- Task management system
- Progress tracking
- Agent integration

### Data Flow
1. Tasks are defined in tasks.md
2. Progress is tracked in progress.md
3. Agents process tasks and update progress
`
}

// SampleDecisionsContent returns sample decisions.md content
func SampleDecisionsContent() string {
	return `# Architectural Decision Records

## ADR-001: Task Management

**Status:** Accepted

**Context:** Need to manage tasks and progress

**Decision:** Use markdown files for task and progress tracking

**Consequences:**
- Simple and human-readable
- Version control friendly
- Easy to edit manually
`
}

// SampleTestPlanContent returns sample test_plan.md content
func SampleTestPlanContent() string {
	return `# Test Plan

## Unit Tests
- Task parsing and validation
- Progress tracking
- Agent integration

## Integration Tests
- End-to-end workflow
- File operations
- Command execution

## Test Coverage
- Target: 80% code coverage
- Focus on critical paths
`
}

// MockTimeProvider provides a mock time for testing
type MockTimeProvider struct {
	FixedTime time.Time
}

// Now returns the fixed time
func (m *MockTimeProvider) Now() time.Time {
	return m.FixedTime
}

// SetTime sets the fixed time
func (m *MockTimeProvider) SetTime(t time.Time) {
	m.FixedTime = t
}

// NewMockTimeProvider creates a new mock time provider
func NewMockTimeProvider() *MockTimeProvider {
	return &MockTimeProvider{
		FixedTime: time.Date(2025, 1, 8, 19, 0, 0, 0, time.UTC),
	}
}

// AssertFileExists checks if a file exists
func AssertFileExists(t *testing.T, filePath string) {
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		t.Errorf("Expected file to exist: %s", filePath)
	}
}

// AssertFileNotExists checks if a file does not exist
func AssertFileNotExists(t *testing.T, filePath string) {
	if _, err := os.Stat(filePath); !os.IsNotExist(err) {
		t.Errorf("Expected file to not exist: %s", filePath)
	}
}

// AssertFileContent checks if a file contains expected content
func AssertFileContent(t *testing.T, filePath string, expectedContent string) {
	content, err := os.ReadFile(filePath)
	if err != nil {
		t.Fatalf("Failed to read file %s: %v", filePath, err)
	}

	if string(content) != expectedContent {
		t.Errorf("File content mismatch in %s:\nExpected:\n%s\nGot:\n%s", filePath, expectedContent, string(content))
	}
}

// AssertFileContains checks if a file contains a substring
func AssertFileContains(t *testing.T, filePath string, expectedSubstring string) {
	content, err := os.ReadFile(filePath)
	if err != nil {
		t.Fatalf("Failed to read file %s: %v", filePath, err)
	}

	if !contains(string(content), expectedSubstring) {
		t.Errorf("File %s does not contain expected substring: %s", filePath, expectedSubstring)
	}
}

// AssertDirExists checks if a directory exists
func AssertDirExists(t *testing.T, dirPath string) {
	info, err := os.Stat(dirPath)
	if err != nil {
		t.Errorf("Expected directory to exist: %s", dirPath)
		return
	}
	if !info.IsDir() {
		t.Errorf("Expected %s to be a directory", dirPath)
	}
}

// AssertDirNotExists checks if a directory does not exist
func AssertDirNotExists(t *testing.T, dirPath string) {
	if _, err := os.Stat(dirPath); !os.IsNotExist(err) {
		t.Errorf("Expected directory to not exist: %s", dirPath)
	}
}

// CleanupTestFiles removes test files
func CleanupTestFiles(t *testing.T, filePaths ...string) {
	for _, filePath := range filePaths {
		if err := os.RemoveAll(filePath); err != nil {
			t.Logf("Warning: Failed to remove test file %s: %v", filePath, err)
		}
	}
}

// CreateTempFile creates a temporary file with content
func CreateTempFile(t *testing.T, content string) string {
	tmpFile, err := os.CreateTemp("", "cursor-iter-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}

	_, err = tmpFile.WriteString(content)
	if err != nil {
		t.Fatalf("Failed to write to temp file: %v", err)
	}

	err = tmpFile.Close()
	if err != nil {
		t.Fatalf("Failed to close temp file: %v", err)
	}

	return tmpFile.Name()
}

// ReadTempFile reads content from a temporary file
func ReadTempFile(t *testing.T, filePath string) string {
	content, err := os.ReadFile(filePath)
	if err != nil {
		t.Fatalf("Failed to read temp file %s: %v", filePath, err)
	}
	return string(content)
}

// WriteTempFile writes content to a temporary file
func WriteTempFile(t *testing.T, filePath string, content string) {
	err := os.WriteFile(filePath, []byte(content), 0644)
	if err != nil {
		t.Fatalf("Failed to write to temp file %s: %v", filePath, err)
	}
}

// Helper function to check if a string contains a substring
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (func() bool {
		for i := 0; i <= len(s)-len(substr); i++ {
			if s[i:i+len(substr)] == substr {
				return true
			}
		}
		return false
	})()
}
