package runner

import (
	"fmt"
	"os"
	"os/exec"
)

// CursorAgent runs cursor-agent; when debug is enabled, sets DEBUG=1 and streams stdout/stderr.
func CursorAgentWithDebug(debug bool, args ...string) error {
    if _, err := exec.LookPath("cursor-agent"); err != nil {
        return fmt.Errorf("cursor-agent not found: %w", err)
    }
    if debug {
        // Set DEBUG env to propagate verbosity
        _ = os.Setenv("DEBUG", "1")
    }
    cmd := exec.Command("cursor-agent", args...)
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr
    return cmd.Run()
}

// Backward-compatible helper
func CursorAgent(args ...string) error { return CursorAgentWithDebug(false, args...) }


