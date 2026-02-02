#!/usr/bin/env bash
set -euo pipefail
CFG="$HOME/.openclaw/wallets/jason-eth/wallet.json"
ADDR="$(python3 -c 'import json,os; print(json.load(open(os.path.expanduser("~/.openclaw/wallets/jason-eth/wallet.json")))["address"])')"
RPC="$(python3 -c 'import json,os; print(json.load(open(os.path.expanduser("~/.openclaw/wallets/jason-eth/wallet.json")))["rpcUrl"])')"
cast balance "$ADDR" --rpc-url "$RPC"
