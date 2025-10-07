#!/usr/bin/env bash
# Add new feature/requirements to the project

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Add New Feature/Requirements${NC}"
echo ""

# Check if cursor-agent is available
if ! command -v cursor-agent >/dev/null 2>&1; then
    echo -e "${RED}❌ cursor-agent not found. Please install it first.${NC}"
    echo -e "${YELLOW}Run: curl https://cursor.com/install -fsS | bash${NC}"
    exit 1
fi

# Check if tasks.md exists
if [[ ! -f "tasks.md" ]]; then
    echo -e "${RED}❌ tasks.md not found. Run 'make iterate-init' first.${NC}"
    exit 1
fi

echo -e "${CYAN}📝 Please describe the new feature/requirements:${NC}"
echo -e "${YELLOW}(You can use multiple lines. Press Ctrl+D when finished)${NC}"
echo ""

# Read multiline input
FEATURE_DESCRIPTION=$(cat)

if [[ -z "$FEATURE_DESCRIPTION" ]]; then
    echo -e "${RED}❌ No feature description provided.${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}🔍 Analyzing current codebase and designing architecture...${NC}"

# Create a comprehensive prompt for feature analysis
FEATURE_PROMPT="
SYSTEM
You are a staff-level engineer tasked with adding a new feature to an existing project. Your job is to:

1. Analyze the current codebase structure and technology stack
2. Design the architecture for the new feature
3. Plan the integration with existing components
4. Create detailed implementation tasks
5. Identify testing requirements
6. Consider security, performance, and maintainability

NEW FEATURE REQUIREMENTS:
$FEATURE_DESCRIPTION

DELIVERABLES:
1. Update architecture.md with new feature design
2. Add comprehensive tasks to tasks.md for implementing this feature
3. Update test_plan.md with testing requirements
4. Add any new dependencies to decisions.md as ADRs

REQUIREMENTS:
- Analyze the existing codebase structure first
- Design the feature to integrate seamlessly with existing architecture
- Break down implementation into logical, testable tasks
- Include acceptance criteria for each task
- Consider edge cases and error handling
- Plan for testing (unit, integration, e2e as appropriate)
- Update documentation appropriately

CONTEXT:
Current repository structure, existing technologies, and current tasks are available in the control files.

USER
Please analyze the codebase and add the new feature: $FEATURE_DESCRIPTION

Design the architecture, create implementation tasks, and update all relevant control files.
"

echo -e "${CYAN}⚡ Generating feature architecture and tasks...${NC}"

# Run cursor-agent with the feature prompt
cursor-agent --print --force "$FEATURE_PROMPT"

echo ""
echo -e "${GREEN}✅ Feature added successfully!${NC}"
echo ""
echo -e "${CYAN}📋 Next Steps:${NC}"
echo -e "   1. ${YELLOW}make iterate-complete${NC}     # Check current task status"
echo -e "   2. ${YELLOW}make iterate-loop${NC}         # Run iterations until all tasks complete"
echo -e "   3. ${YELLOW}make archive-completed${NC}    # Archive completed tasks (optional)"
echo ""
echo -e "${CYAN}📚 Updated Files:${NC}"
echo -e "   - ${YELLOW}architecture.md${NC} - Updated with new feature design"
echo -e "   - ${YELLOW}tasks.md${NC} - Added new implementation tasks"
echo -e "   - ${YELLOW}test_plan.md${NC} - Updated with testing requirements"
echo -e "   - ${YELLOW}decisions.md${NC} - Added architectural decisions"
