#!/usr/bin/env bash
# Check if all tasks are completed

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if tasks.md exists
if [[ ! -f "tasks.md" ]]; then
    echo -e "${RED}❌ tasks.md not found. Run 'make iterate-init' first.${NC}"
    exit 1
fi

# Count total tasks and completed tasks
TOTAL_TASKS=$(grep -c "^- \[" tasks.md || echo "0")
COMPLETED_TASKS=$(grep -c "^- \[x\]" tasks.md || echo "0")
REMAINING_TASKS=$((TOTAL_TASKS - COMPLETED_TASKS))

echo -e "${CYAN}📊 Task Status:${NC}"
echo -e "   Total tasks: ${YELLOW}$TOTAL_TASKS${NC}"
echo -e "   Completed: ${GREEN}$COMPLETED_TASKS${NC}"
echo -e "   Remaining: ${RED}$REMAINING_TASKS${NC}"

if [[ $REMAINING_TASKS -eq 0 && $TOTAL_TASKS -gt 0 ]]; then
    echo -e "${GREEN}✅ All tasks completed!${NC}"
    echo -e "${CYAN}🎉 Project iteration cycle is complete!${NC}"
    
    # Update progress.md with completion
    if [[ -f "progress.md" ]]; then
        echo "" >> progress.md
        echo "## 🎉 All Tasks Completed" >> progress.md
        echo "- **Date**: $(date)" >> progress.md
        echo "- **Status**: All $TOTAL_TASKS tasks completed successfully" >> progress.md
        echo "- **Next Steps**: Project ready for next phase or new feature development" >> progress.md
    fi
    
    # Update CHANGELOG.md with completion
    if [[ -f "CHANGELOG.md" ]]; then
        # Add completion entry to CHANGELOG
        sed -i.tmp '/## \[Unreleased\]/a\
\
### Completed\
- All iteration tasks completed successfully\
- Project ready for next development phase' CHANGELOG.md
        rm -f CHANGELOG.md.tmp
    fi
    
    exit 0
else
    echo -e "${YELLOW}⏳ Tasks remaining. Continue with 'make iterate'.${NC}"
    exit 1
fi
