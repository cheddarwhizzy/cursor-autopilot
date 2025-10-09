package runner

import (
	"bytes"
	"fmt"
	"math/rand"
	"os"
	"os/exec"
	"strings"
	"time"
)

// timestamp returns a formatted timestamp for logging
func timestamp() string {
	return time.Now().Format("15:04:05")
}

// isRaceConditionError checks if the error message indicates a race condition
func isRaceConditionError(stderr string) bool {
	return strings.Contains(stderr, "cli-config.json.tmp") ||
		strings.Contains(stderr, "ENOENT") && strings.Contains(stderr, "cli-config.json")
}

// CursorAgent runs cursor-agent; when debug is enabled, sets DEBUG=1 and streams stdout/stderr.
// Uses a small random startup delay to prevent race conditions when spawning multiple processes.
// Automatically retries on race condition errors with exponential backoff.
// Set CURSOR_AGENT_NO_STAGGER=1 to disable startup delay.
// Set CURSOR_AGENT_MAX_RETRIES=N to change max retries (default: 3).
func CursorAgentWithDebug(debug bool, args ...string) error {
	// Check that cursor-agent exists
	if _, err := exec.LookPath("cursor-agent"); err != nil {
		return fmt.Errorf("cursor-agent not found: %w", err)
	}

	if debug {
		// Set DEBUG env to propagate verbosity
		_ = os.Setenv("DEBUG", "1")
		fmt.Printf("[%s] 🤖 Starting cursor-agent process...\n", timestamp())
	}

	// Get max retries from environment or use default
	maxRetries := 3
	if envRetries := os.Getenv("CURSOR_AGENT_MAX_RETRIES"); envRetries != "" {
		fmt.Sscanf(envRetries, "%d", &maxRetries)
	}

	var lastErr error
	var stderrCapture bytes.Buffer

	for attempt := 0; attempt <= maxRetries; attempt++ {
		if attempt > 0 {
			// Exponential backoff: 500ms, 1s, 2s
			backoff := time.Duration(500*(1<<uint(attempt-1))) * time.Millisecond
			if debug {
				fmt.Printf("[%s] 🔄 Retry attempt %d/%d after %v (race condition detected)\n", 
					timestamp(), attempt, maxRetries, backoff)
			}
			time.Sleep(backoff)
		}

		// Add a small random delay to stagger startups and avoid config file race conditions
		// This prevents multiple cursor-agent processes from writing cli-config.json simultaneously
		if os.Getenv("CURSOR_AGENT_NO_STAGGER") != "1" {
			baseDelay := 50
			if attempt > 0 {
				// Increase base delay on retries
				baseDelay = 200 + (attempt * 100)
			}
			staggerDelay := time.Duration(baseDelay+rand.Intn(150)) * time.Millisecond
			if debug {
				fmt.Printf("[%s] ⏱️  Startup stagger: %v (prevents config race condition)\n", timestamp(), staggerDelay)
			}
			time.Sleep(staggerDelay)
		}

		startTime := time.Now()
		
		// Capture stderr to detect race condition errors
		stderrCapture.Reset()
		cmd := exec.Command("cursor-agent", args...)
		cmd.Stdout = os.Stdout
		cmd.Stderr = &stderrCapture
		
		err := cmd.Run()
		
		// Also print stderr to user
		if stderrCapture.Len() > 0 {
			fmt.Fprint(os.Stderr, stderrCapture.String())
		}

		duration := time.Since(startTime)

		if err == nil {
			if debug {
				if attempt > 0 {
					fmt.Printf("[%s] ✅ cursor-agent succeeded on retry %d (duration: %v)\n", 
						timestamp(), attempt, duration)
				} else {
					fmt.Printf("[%s] ✅ cursor-agent process completed successfully (duration: %v)\n", 
						timestamp(), duration)
				}
			}
			return nil
		}

		// Check if it's a race condition error that we should retry
		stderrStr := stderrCapture.String()
		if isRaceConditionError(stderrStr) && attempt < maxRetries {
			if debug {
				fmt.Printf("[%s] ⚠️  Race condition detected in attempt %d, will retry...\n", 
					timestamp(), attempt+1)
			}
			lastErr = err
			continue
		}

		// Not a race condition or out of retries
		if debug {
			fmt.Printf("[%s] ❌ cursor-agent process failed after %v: %v\n", timestamp(), duration, err)
		}
		return err
	}

	// Exhausted all retries
	if debug {
		fmt.Printf("[%s] ❌ cursor-agent failed after %d retries\n", timestamp(), maxRetries)
	}
	return fmt.Errorf("cursor-agent failed after %d retries: %w", maxRetries, lastErr)
}

// CodexWithDebug runs codex with the specified model; when debug is enabled, streams stdout/stderr.
func CodexWithDebug(debug bool, model string, args ...string) error {
	if _, err := exec.LookPath("codex"); err != nil {
		return fmt.Errorf("codex CLI not found: %w", err)
	}
	if debug {
		// Set DEBUG env to propagate verbosity
		_ = os.Setenv("DEBUG", "1")
		fmt.Printf("[%s] 🤖 Starting codex process (model: %s)...\n", timestamp(), model)
	}

	// Build the command with model and exec
	cmdArgs := []string{"--model", model, "exec"}
	cmdArgs = append(cmdArgs, args...)

	startTime := time.Now()
	cmd := exec.Command("codex", cmdArgs...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()

	if debug {
		duration := time.Since(startTime)
		if err != nil {
			fmt.Printf("[%s] ❌ codex process failed after %v: %v\n", timestamp(), duration, err)
		} else {
			fmt.Printf("[%s] ✅ codex process completed successfully (duration: %v)\n", timestamp(), duration)
		}
	}

	return err
}

// AgentRunner runs either cursor-agent or codex based on the useCodex flag
func AgentRunnerWithDebug(debug bool, useCodex bool, model string, args ...string) error {
	if useCodex {
		return CodexWithDebug(debug, model, args...)
	}
	return CursorAgentWithDebug(debug, args...)
}

// CursorAgentWithOutput runs cursor-agent and captures output
func CursorAgentWithOutput(debug bool, args ...string) (string, error) {
	if _, err := exec.LookPath("cursor-agent"); err != nil {
		return "", fmt.Errorf("cursor-agent not found: %w", err)
	}

	if debug {
		fmt.Printf("[%s] 🤖 Starting cursor-agent process...\n", timestamp())
		fmt.Printf("[%s] 📝 Command: cursor-agent %v\n", timestamp(), args)
	}

	startTime := time.Now()
	cmd := exec.Command("cursor-agent", args...)
	output, err := cmd.Output()

	if debug {
		duration := time.Since(startTime)
		if err != nil {
			fmt.Printf("[%s] ❌ cursor-agent process failed after %v: %v\n", timestamp(), duration, err)
		} else {
			fmt.Printf("[%s] ✅ cursor-agent process completed successfully (duration: %v)\n", timestamp(), duration)
			fmt.Printf("[%s] 📊 Output size: %d bytes\n", timestamp(), len(output))
		}
	}

	return string(output), err
}

// CodexWithOutput runs codex and captures output
func CodexWithOutput(debug bool, model string, args ...string) (string, error) {
	if _, err := exec.LookPath("codex"); err != nil {
		return "", fmt.Errorf("codex CLI not found: %w", err)
	}

	// Build the command with model and exec
	cmdArgs := []string{"--model", model, "exec"}
	cmdArgs = append(cmdArgs, args...)

	if debug {
		fmt.Printf("[%s] 🤖 Starting codex process (model: %s)...\n", timestamp(), model)
		fmt.Printf("[%s] 📝 Command: codex %v\n", timestamp(), cmdArgs)
	}

	startTime := time.Now()
	cmd := exec.Command("codex", cmdArgs...)
	output, err := cmd.Output()

	if debug {
		duration := time.Since(startTime)
		if err != nil {
			fmt.Printf("[%s] ❌ codex process failed after %v: %v\n", timestamp(), duration, err)
		} else {
			fmt.Printf("[%s] ✅ codex process completed successfully (duration: %v)\n", timestamp(), duration)
			fmt.Printf("[%s] 📊 Output size: %d bytes\n", timestamp(), len(output))
		}
	}

	return string(output), err
}

// Backward-compatible helpers
func CursorAgent(args ...string) error         { return CursorAgentWithDebug(false, args...) }
func Codex(model string, args ...string) error { return CodexWithDebug(false, model, args...) }
func AgentRunner(useCodex bool, model string, args ...string) error {
	return AgentRunnerWithDebug(false, useCodex, model, args...)
}
