#!/usr/bin/env bash
# Archive completed tasks to keep tasks.md minimal

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Load file locking utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/file_lock.sh"

echo -e "${BLUE}📦 Archiving Completed Tasks${NC}"
echo ""

# Check if tasks.md exists
if [[ ! -f "tasks.md" ]]; then
    echo -e "${RED}❌ tasks.md not found.${NC}"
    exit 1
fi

# Create completed_tasks directory if it doesn't exist
mkdir -p completed_tasks

# Get current date for archive file
ARCHIVE_DATE=$(date +"%Y-%m-%d_%H-%M-%S")
ARCHIVE_FILE="completed_tasks/completed_${ARCHIVE_DATE}.md"

# Count completed tasks
COMPLETED_TASKS=$(grep -c "^- \[x\]" tasks.md || echo "0")

if [[ $COMPLETED_TASKS -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  No completed tasks found to archive.${NC}"
    exit 0
fi

echo -e "${CYAN}📊 Found $COMPLETED_TASKS completed tasks to archive${NC}"

# Acquire file locks for files that will be modified
CONTROL_FILES=("tasks.md" "progress.md")
LOCKED_FILES=()

echo -e "${CYAN}🔒 Acquiring file locks for control files...${NC}"
for file in "${CONTROL_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        if acquire_file_lock "$file"; then
            LOCKED_FILES+=("$file")
            echo -e "${GREEN}✅ Locked: $file${NC}"
        else
            echo -e "${RED}❌ Could not acquire lock for $file${NC}"
            # Release any locks we already acquired
            for locked_file in "${LOCKED_FILES[@]}"; do
                release_file_lock "$locked_file"
            done
            exit 1
        fi
    fi
done

# Set up cleanup trap to release all locks on exit
cleanup() {
    echo -e "${CYAN}🧹 Cleaning up and releasing file locks...${NC}"
    for locked_file in "${LOCKED_FILES[@]}"; do
        release_file_lock "$locked_file"
    done
}
trap cleanup EXIT INT TERM

# Extract completed tasks
echo "# Completed Tasks - $ARCHIVE_DATE" > "$ARCHIVE_FILE"
echo "" >> "$ARCHIVE_FILE"
echo "Archived from tasks.md on $(date)" >> "$ARCHIVE_FILE"
echo "" >> "$ARCHIVE_FILE"
grep -A 20 "^- \[x\]" tasks.md >> "$ARCHIVE_FILE" || true

# Remove completed tasks from tasks.md
# This is more complex - we need to remove the completed task and all its content until the next task
TEMP_FILE=$(mktemp)

# Process tasks.md line by line
in_completed_task=false
task_content=()

while IFS= read -r line; do
    if [[ $line =~ ^- \[x\] ]]; then
        # Start of completed task
        in_completed_task=true
        task_content=("$line")
    elif [[ $line =~ ^- \[ \] ]] && [[ $in_completed_task == true ]]; then
        # Start of new incomplete task - end of completed task
        in_completed_task=false
        # Don't include this line in task_content, it belongs to the next task
    elif [[ $in_completed_task == true ]]; then
        # Part of completed task
        task_content+=("$line")
    else
        # Not part of a completed task
        if [[ $in_completed_task == false ]]; then
            echo "$line" >> "$TEMP_FILE"
        fi
    fi
done < tasks.md

# Handle case where the last task was completed
if [[ $in_completed_task == true ]]; then
    # Don't add anything to TEMP_FILE - the completed task is already archived
    true
fi

# Replace tasks.md with the filtered version
mv "$TEMP_FILE" tasks.md

echo -e "${GREEN}✅ Archived $COMPLETED_TASKS completed tasks to $ARCHIVE_FILE${NC}"
echo -e "${CYAN}📁 Archive location: completed_tasks/${NC}"

# Update progress.md (already locked above)
if [[ -f "progress.md" ]]; then
    echo "" >> progress.md
    echo "## 📦 Task Archive - $ARCHIVE_DATE" >> progress.md
    echo "- **Tasks Archived**: $COMPLETED_TASKS" >> progress.md
    echo "- **Archive File**: $ARCHIVE_FILE" >> progress.md
    echo "- **Reason**: Keep tasks.md focused on current work" >> progress.md
    echo -e "${CYAN}📝 Updated progress.md with archive information${NC}"
fi

# Show remaining tasks
REMAINING_TASKS=$(grep -c "^- \[ \]" tasks.md || echo "0")
echo -e "${CYAN}📊 Remaining tasks: $REMAINING_TASKS${NC}"
