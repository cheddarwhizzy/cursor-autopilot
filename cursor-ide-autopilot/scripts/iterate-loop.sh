#!/usr/bin/env bash
# Continuous iteration loop until all tasks are completed

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

ITERATION_COUNT=0
MAX_ITERATIONS=50  # Safety limit to prevent infinite loops

echo -e "${BLUE}🔄 Starting continuous iteration loop${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop at any time${NC}"
echo ""

# Trap Ctrl+C to show final status
trap 'echo -e "\n${YELLOW}🛑 Stopped by user${NC}"; ./scripts/check-complete.sh; exit 0' INT

while true; do
    ITERATION_COUNT=$((ITERATION_COUNT + 1))
    
    echo -e "${CYAN}🔄 Iteration #$ITERATION_COUNT${NC}"
    echo "=================================="
    
    # Check if we've hit the safety limit
    if [[ $ITERATION_COUNT -gt $MAX_ITERATIONS ]]; then
        echo -e "${RED}⚠️  Maximum iterations ($MAX_ITERATIONS) reached. Stopping for safety.${NC}"
        echo -e "${YELLOW}If tasks are still remaining, you may need to run 'make iterate' manually.${NC}"
        break
    fi
    
    # Check completion status first (with file lock)
    TASKS_FILE="tasks.md"
    if acquire_file_lock "$TASKS_FILE"; then
        if ./scripts/check-complete.sh; then
            release_file_lock "$TASKS_FILE"
            echo -e "${GREEN}🎉 All tasks completed! Loop finished successfully.${NC}"
            break
        fi
        release_file_lock "$TASKS_FILE"
    else
        echo -e "${RED}❌ Could not acquire lock for tasks.md, skipping iteration${NC}"
        sleep 5
        continue
    fi
    
    echo ""
    echo -e "${CYAN}⚡ Running iteration...${NC}"
    
    # Run the iteration (this will also use file locking internally)
    if make iterate; then
        echo -e "${GREEN}✅ Iteration #$ITERATION_COUNT completed successfully${NC}"
    else
        echo -e "${RED}❌ Iteration #$ITERATION_COUNT failed${NC}"
        echo -e "${YELLOW}⚠️  Stopping loop due to iteration failure${NC}"
        echo -e "${CYAN}💡 You may need to fix issues manually and run 'make iterate' again${NC}"
        break
    fi
    
    echo ""
    echo -e "${CYAN}📊 Current status:${NC}"
    ./scripts/check-complete.sh || true
    echo ""
    
    # Small delay between iterations
    sleep 2
done

echo ""
echo -e "${BLUE}🏁 Iteration loop finished${NC}"
echo -e "${CYAN}📊 Final status:${NC}"
./scripts/check-complete.sh || true
