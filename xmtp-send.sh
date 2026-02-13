#!/bin/bash
# xmtp-send.sh — Shell wrapper for XMTP send
# Usage:
#   xmtp-send.sh <address> <message>
#   xmtp-send.sh --check <address>
#   xmtp-send.sh --info

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if node_modules exists
if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
  echo "❌ Dependencies not installed. Running: npm install" >&2
  cd "$SCRIPT_DIR" && npm install
fi

# Check if .env exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
  echo "❌ Missing .env file. Copy .env.example to .env and configure." >&2
  echo "   cp $SCRIPT_DIR/.env.example $SCRIPT_DIR/.env" >&2
  exit 1
fi

exec node "$SCRIPT_DIR/send.mjs" "$@"
