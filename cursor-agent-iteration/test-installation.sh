#!/usr/bin/env bash
# Test script for Cursor Agent Iteration System installation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Cursor Agent Iteration System Installation${NC}"
echo ""

# Test 1: Check if we're in a git repository
echo -e "${CYAN}Test 1: Git repository check${NC}"
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Git repository detected${NC}"
else
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Test 2: Check if cursor-agent is available
echo -e "${CYAN}Test 2: cursor-agent availability${NC}"
if command -v cursor-agent >/dev/null 2>&1; then
    echo -e "${GREEN}✅ cursor-agent is installed${NC}"
    cursor-agent --version 2>/dev/null || echo -e "${YELLOW}⚠️  cursor-agent version not available${NC}"
else
    echo -e "${YELLOW}⚠️  cursor-agent not found, will install during setup${NC}"
fi

# Test 3: Check if Makefile exists
echo -e "${CYAN}Test 3: Makefile check${NC}"
if [[ -f "Makefile" ]]; then
    echo -e "${GREEN}✅ Makefile exists${NC}"
else
    echo -e "${YELLOW}⚠️  No Makefile found, will create one${NC}"
fi

# Test 4: Check directory structure
echo -e "${CYAN}Test 4: Directory structure${NC}"
if [[ -d "prompts" ]]; then
    echo -e "${GREEN}✅ prompts/ directory exists${NC}"
else
    echo -e "${YELLOW}⚠️  prompts/ directory will be created${NC}"
fi

if [[ -d "scripts" ]]; then
    echo -e "${GREEN}✅ scripts/ directory exists${NC}"
else
    echo -e "${YELLOW}⚠️  scripts/ directory will be created${NC}"
fi

# Test 5: Check for existing iteration files
echo -e "${CYAN}Test 5: Existing iteration files${NC}"
if [[ -f "prompts/iterate.md" ]]; then
    echo -e "${YELLOW}⚠️  prompts/iterate.md already exists${NC}"
else
    echo -e "${GREEN}✅ prompts/iterate.md will be created${NC}"
fi

if [[ -f "tasks.md" ]]; then
    echo -e "${YELLOW}⚠️  tasks.md already exists${NC}"
else
    echo -e "${GREEN}✅ tasks.md will be created${NC}"
fi

# Test 6: Check for control files
echo -e "${CYAN}Test 6: Control files check${NC}"
CONTROL_FILES=("architecture.md" "progress.md" "decisions.md" "test_plan.md" "qa_checklist.md" "CHANGELOG.md")
for file in "${CONTROL_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${YELLOW}⚠️  $file already exists${NC}"
    else
        echo -e "${GREEN}✅ $file will be created${NC}"
    fi
done

echo ""
echo -e "${GREEN}🎉 Installation test complete!${NC}"
echo ""
echo -e "${CYAN}📋 Ready to install? Run:${NC}"
echo -e "   ${YELLOW}./install.sh${NC}"
echo ""
echo -e "${CYAN}📚 After installation, run:${NC}"
echo -e "   ${YELLOW}make iterate-init${NC}     # Initialize the system"
echo -e "   ${YELLOW}make iterate${NC}          # Start iterating"
