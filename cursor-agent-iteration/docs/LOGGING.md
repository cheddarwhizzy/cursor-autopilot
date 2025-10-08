# Comprehensive Logging Guide

This document describes the comprehensive logging added to the `cursor-iter` tool to track task execution flow.

## Overview

Enhanced logging has been added to the following commands:
- `cursor-iter add-feature` - Feature design and task creation
- `cursor-iter iterate` - Single iteration execution
- `cursor-iter iterate-loop` - Continuous iteration loop

## Enabling Debug Mode

To enable detailed logging, use the `--debug` flag or set the `DEBUG` environment variable:

```bash
# Using flag
cursor-iter iterate --debug

# Using environment variable
DEBUG=1 cursor-iter iterate

# Both work for all commands
cursor-iter add-feature --debug
cursor-iter iterate-loop --debug
```

## Logging Levels

### Standard Output (Always Shown)
- Task selection and status
- Cursor-agent process start/completion
- Task completion verification
- Overall progress updates

### Debug Output (Only with --debug flag)
- File reads from tasks.md and progress.md
- Task detail extraction
- Prompt building
- Status rechecking after completion
- Retry logic

## Example Log Output

### `cursor-iter iterate --debug`

```
[14:32:15] ✅ Acquired file lock successfully - safe to proceed
[14:32:15] 📖 Reading tasks from: tasks.md
[14:32:15] ✅ Successfully read tasks.md (2543 bytes)
[14:32:15] 📖 Reading progress from: progress.md
[14:32:15] ✅ Successfully read progress.md (1234 bytes)
[14:32:15] 🔍 Checking for in-progress tasks...
[14:32:15] 📊 Found 1 in-progress tasks (max allowed: 10)
[14:32:15] 🎯 Selected in-progress task to continue: 'Implement user authentication'
[14:32:15] 🔄 Continuing in-progress task: 'Implement user authentication' (2/5 criteria)
[14:32:15] 📋 Extracting full task details from tasks.md...
[14:32:15] ✅ Task details extracted (856 bytes)
[14:32:15] 📝 Building prompt for cursor-agent...
[14:32:15] 🔓 Released file lock before running cursor-agent
[14:32:15] 🚀 Sending task to cursor-agent: 'Implement user authentication'
[14:32:15] 🤖 Using cursor-agent (model: auto)
[14:32:15] 📊 Task progress: 2/5 acceptance criteria completed
[14:32:15] 🤖 Starting cursor-agent process...
... cursor-agent output ...
[14:38:42] ✅ cursor-agent process completed successfully (duration: 6m27s)
[14:38:42] 🔍 Rechecking task status after cursor-agent completion...
[14:38:42] 📖 Re-reading tasks.md to check for updates...
[14:38:42] ✅ Re-read tasks.md (2687 bytes)
[14:38:42] 📖 Re-reading progress.md to check for completion status...
[14:38:42] ✅ Re-read progress.md (1345 bytes)
[14:38:42] 🔍 Checking if task 'Implement user authentication' is now marked as completed...
[14:38:42] ⚠️ Task not yet complete: Implement user authentication - run 'iterate' again to continue
[14:38:42] 💡 Task will be retried on next iteration
[14:38:42] 📊 Updated progress: 🔄 Working on: Implement user authentication (3/5 criteria)
```

### `cursor-iter iterate-loop --debug`

```
[15:10:23] 🚀 Starting iterate-loop (max in-progress: 10)
[15:10:23] ✅ Acquired file lock successfully - safe to proceed
[15:10:23] 📖 Reading tasks from: tasks.md
[15:10:23] ✅ Successfully read tasks.md (3421 bytes)
[15:10:23] 📖 Reading progress from: progress.md
[15:10:23] ✅ Successfully read progress.md (876 bytes)
[15:10:23] Iteration #1 - 🔄 Working on: Setup database schema (0/3 criteria)
[15:10:23] 🔍 Checking for in-progress tasks...
[15:10:23] 📊 Found 1 in-progress tasks (max allowed: 10)
[15:10:23] 🎯 Selected in-progress task to continue: 'Setup database schema'
[15:10:23] 🔄 Continuing in-progress task: 'Setup database schema' (0/3 criteria)
[15:10:23] 📋 Extracting full task details from tasks.md...
[15:10:23] ✅ Task details extracted (654 bytes)
[15:10:23] 📝 Building prompt for cursor-agent...
[15:10:23] 🔓 Released file lock before running cursor-agent
[15:10:23] 🔄 Starting iteration for task: Setup database schema
[15:10:23] 🚀 Sending task to cursor-agent: 'Setup database schema'
[15:10:23] 🤖 Using cursor-agent (model: auto)
[15:10:23] 📊 Task progress: 0/3 acceptance criteria completed
[15:10:23] 🤖 Starting cursor-agent process...
... cursor-agent output ...
[15:15:34] ✅ cursor-agent process completed successfully (duration: 5m11s)
[15:15:34] 🔍 Rechecking task status after cursor-agent completion...
[15:15:34] 📖 Re-reading tasks.md to check for updates...
[15:15:34] ✅ Re-read tasks.md (3456 bytes)
[15:15:34] 📖 Re-reading progress.md to check for completion status...
[15:15:34] ✅ Re-read progress.md (1023 bytes)
[15:15:34] 🔍 Checking if task 'Setup database schema' is now marked as completed...
[15:15:34] ✅ Task completed: Setup database schema
[15:15:34] 📊 Updated progress: ⏳ Next task: Create user authentication endpoints
[15:15:36] ✅ Acquired file lock successfully - safe to proceed
[15:15:36] 📖 Reading tasks from: tasks.md
[15:15:36] ✅ Successfully read tasks.md (3456 bytes)
[15:15:36] 📖 Reading progress from: progress.md
[15:15:36] ✅ Successfully read progress.md (1023 bytes)
[15:15:36] Iteration #2 - ⏳ Next task: Create user authentication endpoints
[15:15:36] 🔍 Checking for in-progress tasks...
[15:15:36] 📊 Found 0 in-progress tasks (max allowed: 10)
[15:15:36] 🔍 Looking for next pending task...
[15:15:36] 🎯 Found next pending task: 'Create user authentication endpoints'
[15:15:36] 📝 Marking task as in-progress in progress.md...
[15:15:36] ✅ Successfully marked task as in-progress in progress.md
[15:15:36] 📝 Started new task: 'Create user authentication endpoints'
... continues with next task ...
```

### `cursor-iter add-feature --debug`

```
[16:20:45] 📖 Checking for existing tasks.md at: tasks.md
[16:20:45] ✅ Found existing tasks.md
[16:20:45] ✅ Acquired file lock successfully - safe to proceed
[16:20:45] 🚀 Sending feature design request to cursor-agent...
[16:20:45] 🤖 Using cursor-agent (model: auto)
[16:20:45] 🤖 Starting cursor-agent process...
[16:20:45] 📝 Command: cursor-agent [--print --force <prompt_content>]
... cursor-agent output ...
[16:23:12] ✅ cursor-agent process completed successfully (duration: 2m27s)
[16:23:12] 📊 Output size: 15234 bytes
[16:23:12] 🔍 Parsing patches from cursor-agent output...
[16:23:12] ✅ Successfully parsed patches
[16:23:12] 📊 Found 5 patches
[16:23:12] 📄 Patch 1: architecture.md (2345 bytes)
[16:23:12] 📄 Patch 2: tasks.md (4567 bytes)
[16:23:12] 📄 Patch 3: test_plan.md (1234 bytes)
[16:23:12] 📄 Patch 4: decisions.md (876 bytes)
[16:23:12] 📄 Patch 5: src/auth.ts (3456 bytes)
[16:23:12] 🔍 Filtering patches to only include control files...
[16:23:12] ✅ Including control file: architecture.md
[16:23:12] ✅ Including control file: tasks.md
[16:23:12] ✅ Including control file: test_plan.md
[16:23:12] ✅ Including control file: decisions.md
[16:23:12] ⏭️ Skipping implementation file: src/auth.ts
[16:23:12] 📝 Applying 4 patches to control files...
[16:23:12] ✅ Applied patch to architecture.md
[16:23:12] ✅ Applied patch to tasks.md
[16:23:12] ✅ Applied patch to test_plan.md
[16:23:12] ✅ Applied patch to decisions.md
[16:23:12] ✅ Feature analysis complete! Applied 4 patches to control files
[16:23:12] 📝 Tasks have been added to tasks.md and will be processed by iterate-loop
[16:23:12] 💡 You can now run 'cursor-iter iterate-loop' to start processing tasks
```

**Key additions:**
- Shows the actual command being executed
- Displays execution duration
- Shows output size from cursor-agent

## Task Status File Source Clarity

The `task-status` command now clearly indicates which file is being checked:

```
📊 Task Status Overview
======================
Status tracked in: progress.md (✅ completed, 🔄 in-progress)
Task list from: tasks.md (⏳ pending)

🎯 CURRENT TASK: Implement user authentication (2/5 criteria completed)

Total Tasks: 12 (from tasks.md)
✅ Completed: 3 (from progress.md)
🔄 In Progress: 1 (from progress.md)
⏳ Pending: 8 (not in progress.md)

✅ Completed Tasks (from progress.md):
  - Setup project structure
  - Configure database
  - Create user model

🔄 In Progress Tasks (from progress.md):
  - Implement user authentication (2/5 criteria completed)

⏳ Pending Tasks (next 5):
  - Add password reset
  - Create profile page
  - Add email verification
  - Implement OAuth
  - Add two-factor auth
  ... and 3 more
```

**Key clarifications:**
- Header explains which file tracks which status
- Each count shows its source file
- "Pending" means not yet in progress.md
- Makes the two-file system transparent

## Key Logging Points

### 1. File Operations
- **Read operations**: Shows when tasks.md and progress.md are read
- **File sizes**: Displays byte count to verify data was read
- **Lock acquisition**: Shows when file locks are acquired and released

### 2. Task Selection
- **In-progress detection**: Shows how many in-progress tasks exist
- **Task continuation**: Logs when continuing an in-progress task
- **New task start**: Logs when starting a new pending task
- **Progress marking**: Shows when tasks are marked in-progress

### 3. Cursor-Agent Execution
- **Task identification**: Clear log of which task is being sent
- **Model selection**: Shows which model is being used
- **Progress state**: Shows current acceptance criteria completion
- **Process timing**: Shows duration of cursor-agent execution

### 4. Post-Execution Verification
- **Status recheck**: Shows files being re-read after execution
- **Completion check**: Logs whether task is now complete
- **Retry notification**: Indicates if task needs retry

### 5. Add-Feature Specific
- **Patch parsing**: Shows number and types of patches found
- **Patch filtering**: Shows which files are included/excluded
- **File application**: Shows each control file being updated

## Benefits of Enhanced Logging

1. **Transparency**: See exactly what the tool is doing at each step
2. **Debugging**: Identify where issues occur in the workflow
3. **Progress Tracking**: Monitor long-running operations
4. **Verification**: Confirm tasks are being processed correctly
5. **Retry Logic**: Understand when and why tasks are retried

## Performance Impact

- Standard logging: Minimal impact (only key events)
- Debug logging: Slight overhead from additional I/O operations
- File sizes are logged to help identify performance issues

## Tips

1. **Use debug mode during development** to understand the workflow
2. **Use standard mode in production** for cleaner output
3. **Check file sizes** if you notice slow performance
4. **Monitor retry messages** to identify stuck tasks
5. **Watch for lock warnings** to detect concurrent execution issues

## Troubleshooting

If you see issues:
- Check for file lock warnings (indicates concurrent processes)
- Verify file sizes are reasonable (large files slow down processing)
- Monitor retry counts (frequent retries may indicate task issues)
- Check cursor-agent duration (long times may indicate complex tasks)

