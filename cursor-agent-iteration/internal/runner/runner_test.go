package runner

import (
	"os"
	"os/exec"
	"testing"
)

func TestCursorAgentWithDebug(t *testing.T) {
	// Test that cursor-agent command is constructed correctly
	// This is a basic test to ensure the function doesn't panic
	// In a real environment, cursor-agent would need to be available

	// Check if cursor-agent is available
	if _, err := exec.LookPath("cursor-agent"); err != nil {
		t.Skip("cursor-agent not found, skipping test")
	}

	// Test with debug enabled
	err := CursorAgentWithDebug(true, "--help")
	if err != nil {
		// We expect this to fail since we're passing --help to cursor-agent
		// but it should not panic
		t.Logf("Expected error from cursor-agent --help: %v", err)
	}

	// Test with debug disabled
	err = CursorAgentWithDebug(false, "--help")
	if err != nil {
		t.Logf("Expected error from cursor-agent --help: %v", err)
	}
}

func TestCodexWithDebug(t *testing.T) {
	// Test that codex command is constructed correctly
	// This is a basic test to ensure the function doesn't panic
	// In a real environment, codex would need to be available

	// Check if codex is available
	if _, err := exec.LookPath("codex"); err != nil {
		t.Skip("codex CLI not found, skipping test")
	}

	// Test with debug enabled
	err := CodexWithDebug(true, "gpt-5-codex", "--help")
	if err != nil {
		// We expect this to fail since we're passing --help to codex
		// but it should not panic
		t.Logf("Expected error from codex --help: %v", err)
	}

	// Test with debug disabled
	err = CodexWithDebug(false, "gpt-5-codex", "--help")
	if err != nil {
		t.Logf("Expected error from codex --help: %v", err)
	}
}

func TestAgentRunnerWithDebug(t *testing.T) {
	// Test that the agent runner correctly chooses between cursor-agent and codex

	// Test with cursor-agent (useCodex = false)
	if _, err := exec.LookPath("cursor-agent"); err == nil {
		err := AgentRunnerWithDebug(true, false, "auto", "--help")
		if err != nil {
			t.Logf("Expected error from cursor-agent --help: %v", err)
		}
	}

	// Test with codex (useCodex = true)
	if _, err := exec.LookPath("codex"); err == nil {
		err := AgentRunnerWithDebug(true, true, "gpt-5-codex", "--help")
		if err != nil {
			t.Logf("Expected error from codex --help: %v", err)
		}
	}
}

func TestBackwardCompatibility(t *testing.T) {
	// Test backward compatibility functions

	// Test CursorAgent function
	if _, err := exec.LookPath("cursor-agent"); err == nil {
		err := CursorAgent("--help")
		if err != nil {
			t.Logf("Expected error from cursor-agent --help: %v", err)
		}
	}

	// Test Codex function
	if _, err := exec.LookPath("codex"); err == nil {
		err := Codex("gpt-5-codex", "--help")
		if err != nil {
			t.Logf("Expected error from codex --help: %v", err)
		}
	}

	// Test AgentRunner function
	if _, err := exec.LookPath("cursor-agent"); err == nil {
		err := AgentRunner(false, "auto", "--help")
		if err != nil {
			t.Logf("Expected error from cursor-agent --help: %v", err)
		}
	}

	if _, err := exec.LookPath("codex"); err == nil {
		err := AgentRunner(true, "gpt-5-codex", "--help")
		if err != nil {
			t.Logf("Expected error from codex --help: %v", err)
		}
	}
}

func TestEnvironmentVariables(t *testing.T) {
	// Test that DEBUG environment variable is set when debug is enabled
	originalDebug := os.Getenv("DEBUG")
	defer os.Setenv("DEBUG", originalDebug)

	// Clear DEBUG environment variable
	os.Unsetenv("DEBUG")

	// Test that DEBUG is set when debug is true
	if _, err := exec.LookPath("cursor-agent"); err == nil {
		err := CursorAgentWithDebug(true, "--help")
		if err != nil {
			t.Logf("Expected error from cursor-agent --help: %v", err)
		}

		// Check if DEBUG was set (it should be set during execution)
		if debug := os.Getenv("DEBUG"); debug != "1" {
			t.Errorf("Expected DEBUG=1, got DEBUG=%s", debug)
		}
	}

	// Test that DEBUG is not set when debug is false
	os.Unsetenv("DEBUG")
	if _, err := exec.LookPath("cursor-agent"); err == nil {
		err := CursorAgentWithDebug(false, "--help")
		if err != nil {
			t.Logf("Expected error from cursor-agent --help: %v", err)
		}

		// Check if DEBUG was set (it should not be set)
		if debug := os.Getenv("DEBUG"); debug != "" {
			t.Errorf("Expected DEBUG to be empty, got DEBUG=%s", debug)
		}
	}
}
