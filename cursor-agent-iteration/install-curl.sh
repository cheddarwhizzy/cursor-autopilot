#!/usr/bin/env bash
# One-liner installer for Cursor Agent Iteration System
# Usage: curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/cursor-cli-headleess-agent/cursor-agent-iteration/install-curl.sh | bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Installing Cursor Agent Iteration System${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository. Please run this script from your project root.${NC}"
    exit 1
fi

# Download and run the bootstrap script directly
echo -e "${CYAN}📥 Downloading and running bootstrap...${NC}"
curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/cursor-cli-headleess-agent/cursor-agent-iteration/bootstrap.sh | bash

echo ""
echo -e "${GREEN}🎉 Installation complete!${NC}"
echo -e "${CYAN}Run 'make iterate-init' to get started.${NC}"
