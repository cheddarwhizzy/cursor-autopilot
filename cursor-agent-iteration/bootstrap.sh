#!/usr/bin/env bash
# Cursor Agent Iteration System - Bootstrap Script (Go CLI)
# Usage: curl -fsSL https://raw.githubusercontent.com/cheddarwhizzy/cursor-autopilot/main/cursor-agent-iteration/bootstrap.sh | bash

set -euo pipefail

mkdir -p bin

OWNER="cheddarwhizzy"
REPO="cursor-autopilot"
API_URL="https://api.github.com/repos/${OWNER}/${REPO}/releases/latest"
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) ARCH="amd64" ;;
  arm64|aarch64) ARCH="arm64" ;;
esac
BIN_NAME="cursor-iter_${OS}_${ARCH}"
BIN_URL=""
if command -v jq >/dev/null 2>&1; then
  BIN_URL=$(curl -fsSL "$API_URL" | jq -r ".assets[] | select(.name == \"$BIN_NAME\") | .browser_download_url")
fi

if [[ -n "$BIN_URL" ]]; then
  curl -fsSL "$BIN_URL" -o bin/cursor-iter
  chmod +x bin/cursor-iter
else
  echo "could not resolve latest binary download url" >&2
  exit 1
fi

exec ./bin/cursor-iter "$@"
