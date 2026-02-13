#!/bin/bash
# xmtp-send.sh — Shell wrapper for XMTP send
# Usage:
#   ./xmtp-send.sh <address> <message>
#   ./xmtp-send.sh --check <address>
#   ./xmtp-send.sh --info

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure we're using Node 22 LTS if nvm is available
if command -v nvm &>/dev/null; then
  nvm use 22 --silent 2>/dev/null
fi

node "$SCRIPT_DIR/send.mjs" "$@"
