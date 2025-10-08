# Run Agent Command Examples

The `cursor-iter run-agent` command allows you to send ad-hoc requests directly to cursor-agent or codex without going through the full task iteration system. This is perfect for quick updates, policy changes, or one-off improvements.

## Basic Usage

```bash
cursor-iter run-agent --prompt "your request here"
```

## Common Use Cases

### 1. Update Build Requirements

Add build validation to your control files:

```bash
cursor-iter run-agent --prompt "add to our control files that pnpm build should succeed before marking any tasks as completed. Fix any issues during build and retry until it builds successfully before marking as complete"
```

**What this does:**
- Updates `qa_checklist.md` or relevant control files
- Adds build validation requirements
- Ensures tasks aren't marked complete until build succeeds

### 2. Add Policy to QA Checklist

Add new quality requirements:

```bash
cursor-iter run-agent --prompt "add a policy to qa_checklist.md that all API endpoints must have rate limiting"
```

**What this does:**
- Updates `qa_checklist.md` with new policy
- Documents the rate limiting requirement
- Ensures future tasks follow this guideline

### 3. Update Architecture Documentation

Document architectural changes:

```bash
cursor-iter run-agent --prompt "update architecture.md to document our new caching strategy using Redis"
```

**What this does:**
- Reads current `architecture.md`
- Adds documentation about Redis caching
- Maintains consistency with existing architecture

### 4. Refactor Logging

Apply codebase-wide improvements:

```bash
cursor-iter run-agent --prompt "refactor all logging to use structured logging with JSON format"
```

**What this does:**
- Scans codebase for logging statements
- Refactors to structured logging
- Updates tests as needed
- Commits changes

### 5. Add Error Handling

Improve code quality:

```bash
cursor-iter run-agent --prompt "add error handling middleware to all API routes"
```

**What this does:**
- Reviews API routes
- Adds appropriate error handling
- Updates tests
- Documents changes in `decisions.md`

### 6. Update Testing Requirements

Modify test coverage policies:

```bash
cursor-iter run-agent --prompt "update test_plan.md to require integration tests for all API endpoints"
```

**What this does:**
- Updates `test_plan.md`
- Adds integration test requirements
- Documents the new testing standard

### 7. Add Security Requirements

Enhance security policies:

```bash
cursor-iter run-agent --prompt "add to qa_checklist.md that all user inputs must be validated and sanitized"
```

**What this does:**
- Updates `qa_checklist.md`
- Adds input validation requirements
- Documents security best practices

## Advanced Usage

### Using Codex CLI

Use Codex instead of cursor-agent:

```bash
cursor-iter run-agent --codex --prompt "your request here"
```

### Debug Mode

Enable detailed logging:

```bash
cursor-iter run-agent --debug --prompt "your request here"
```

**Debug output includes:**
- Control files detected
- Enhanced prompt size
- Agent execution details
- Completion status

### Specify Model

Use a specific model:

```bash
# With cursor-agent
cursor-iter run-agent --model gpt-4o --prompt "your request here"

# With codex
cursor-iter run-agent --codex --model gpt-5-codex --prompt "your request here"
```

## Control File References

The `run-agent` command automatically includes references to these control files:

- `architecture.md` - System architecture and design
- `decisions.md` - Architectural Decision Records (ADRs)
- `tasks.md` - Task backlog and current work
- `progress.md` - Completed tasks and progress history
- `test_plan.md` - Testing strategy and coverage
- `qa_checklist.md` - Quality assurance requirements
- `CHANGELOG.md` - Change history
- `context.md` - Project context (if available)

The agent will automatically read these files for context and update them as needed.

## When to Use `run-agent` vs Other Commands

### Use `run-agent` for:
- ✅ Quick policy changes
- ✅ Control file updates
- ✅ Small refactoring tasks
- ✅ Documentation updates
- ✅ One-off improvements
- ✅ Adding new requirements to existing files

### Use `add-feature` for:
- 🎯 New features requiring architecture design
- 🎯 Multi-task implementations
- 🎯 Complex features needing planning
- 🎯 Features requiring multiple iterations

### Use `iterate` for:
- 🔄 Working on tasks from `tasks.md`
- 🔄 Following the full iteration process
- 🔄 Implementing planned features

## Tips for Effective Requests

### Be Specific
```bash
# ❌ Vague
cursor-iter run-agent --prompt "improve the code"

# ✅ Specific
cursor-iter run-agent --prompt "add input validation to all form handlers using Zod schemas"
```

### Mention Target Files
```bash
# ✅ Clear target
cursor-iter run-agent --prompt "add to qa_checklist.md that all database queries must use prepared statements"
```

### Include Context
```bash
# ✅ Provides context
cursor-iter run-agent --prompt "update architecture.md to document the new microservices architecture we're migrating to, including service boundaries and communication patterns"
```

### Specify Quality Requirements
```bash
# ✅ Includes quality criteria
cursor-iter run-agent --prompt "refactor authentication middleware to use JWT tokens, add comprehensive tests, and update documentation in decisions.md"
```

## Example Workflow

Here's a typical workflow using `run-agent`:

```bash
# 1. Add a new quality requirement
cursor-iter run-agent --prompt "add to qa_checklist.md that all API responses must follow the JSON:API specification"

# 2. Update architecture to reflect the change
cursor-iter run-agent --prompt "update architecture.md to document our adoption of JSON:API for all REST endpoints"

# 3. Check what was updated
cursor-iter task-status

# 4. Continue with regular iteration
cursor-iter iterate
```

## Troubleshooting

### Request Not Working as Expected

If the agent doesn't make the expected changes:

1. **Be more specific** about which files to update
2. **Include context** about why the change is needed
3. **Use debug mode** to see what's happening:
   ```bash
   cursor-iter run-agent --debug --prompt "your request"
   ```

### Control Files Not Being Updated

If control files aren't being updated:

1. **Explicitly mention the file** in your prompt:
   ```bash
   cursor-iter run-agent --prompt "update qa_checklist.md to add..."
   ```

2. **Check if files exist**:
   ```bash
   ls -la *.md
   ```

3. **Initialize if needed**:
   ```bash
   cursor-iter iterate-init
   ```

### Agent Running Too Long

If the agent seems stuck:

1. Use more focused requests
2. Break large changes into smaller requests
3. Use `add-feature` for complex changes instead

## Comparison with Other Commands

| Command | Use Case | Output | When to Use |
|---------|----------|--------|-------------|
| `run-agent` | Ad-hoc requests | Direct changes | Quick updates, policy changes |
| `add-feature` | Feature design | Tasks in `tasks.md` | New features, complex work |
| `iterate` | Task execution | Progress in `progress.md` | Implementing planned tasks |
| `iterate-loop` | Automated execution | All tasks completed | Continuous automation |

## Best Practices

1. **Start small** - Test with simple requests first
2. **Review changes** - Check what was updated after each request
3. **Use version control** - Commit before running ad-hoc requests
4. **Be explicit** - Mention file names and specific requirements
5. **Check status** - Run `cursor-iter task-status` after updates
6. **Document decisions** - Ask the agent to update `decisions.md` for important changes

## Security Considerations

The `run-agent` command has full access to your codebase. Always:

- Review changes before committing
- Use in trusted repositories only
- Avoid passing sensitive data in prompts
- Keep control files in version control
- Test changes in a safe environment first

## Need Help?

```bash
# Show command help
cursor-iter run-agent

# Show all commands
cursor-iter --help

# Check task status
cursor-iter task-status
```

---

For more information, see the main [README.md](../README.md).

