#!/usr/bin/env bash
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

PROMPT_FILE="./prompts/initialize-iteration-universal.md"
TARGET_DIR="${1:-.}"
MODEL="${MODEL:-gpt-4o-mini}"   # override with: MODEL="gpt-4o" ./scripts/init-iterate.sh

if ! command -v cursor-agent >/dev/null 2>&1; then
  echo "Installing cursor-agent..."
  curl https://cursor.com/install -fsS | bash
  echo "Note: You may need to add ~/.local/bin to PATH and restart your shell"
  export PATH="$HOME/.local/bin:$PATH"
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "❌ Missing prompt file: $PROMPT_FILE"
  exit 1
fi

echo "⚙️  Generating prompts/iterate.md + tasks.md (universal detection)"
cursor-agent --print --force --model "$MODEL" "$(cat "$PROMPT_FILE")"

echo "✅ Created/updated: prompts/iterate.md, tasks.md"
echo "➡️  Start the loop with:"
echo "   cursor-agent --print --force --prompt prompts/iterate.md"
