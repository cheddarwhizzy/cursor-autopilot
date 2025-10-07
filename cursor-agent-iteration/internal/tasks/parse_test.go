package tasks

import "testing"

const sample = `### Task: A

**Acceptance Criteria:**
* [x] one
* [x] two

### Task: B

**Acceptance Criteria:**
* [x] one
* [ ] two

### Task: C

**Acceptance Criteria:**
* [ ] one
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

func contains(s, sub string) bool { return len(s) >= len(sub) && (func() bool { return stringIndex(s, sub) >= 0 })() }

func stringIndex(s, sub string) int {
    for i := 0; i+len(sub) <= len(s); i++ {
        if s[i:i+len(sub)] == sub {
            return i
        }
    }
    return -1
}


