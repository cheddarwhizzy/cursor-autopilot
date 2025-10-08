package runner

import (
	"fmt"
	"os"
	"os/exec"
	"time"
)

// timestamp returns a formatted timestamp for logging
func timestamp() string {
	return time.Now().Format("15:04:05")
}

// CursorAgent runs cursor-agent; when debug is enabled, sets DEBUG=1 and streams stdout/stderr.
func CursorAgentWithDebug(debug bool, args ...string) error {
	if _, err := exec.LookPath("cursor-agent"); err != nil {
		return fmt.Errorf("cursor-agent not found: %w", err)
	}
	if debug {
		// Set DEBUG env to propagate verbosity
		_ = os.Setenv("DEBUG", "1")
		fmt.Printf("[%s] 🤖 Starting cursor-agent process...\n", timestamp())
	}

	startTime := time.Now()
	cmd := exec.Command("cursor-agent", args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err := cmd.Run()

	if debug {
		duration := time.Since(startTime)
		if err != nil {
			fmt.Printf("[%s] ❌ cursor-agent process failed after %v: %v\n", timestamp(), duration, err)
		} else {
			fmt.Printf("[%s] ✅ cursor-agent process completed successfully (duration: %v)\n", timestamp(), duration)
		}
	}

	return err
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
