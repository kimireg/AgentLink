#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   jason_eth_send.sh <to> <value>
# Example:
#   jason_eth_send.sh 0xabc... 0.0001ether

TO="${1:?to address required}"
VALUE="${2:?value required (e.g. 0.0001ether)}"

CFG="$HOME/.openclaw/wallets/jason-eth/wallet.json"
RPC="$(python3 -c 'import json,os; print(json.load(open(os.path.expanduser("~/.openclaw/wallets/jason-eth/wallet.json")))["rpcUrl"])')"
KS="$(python3 -c 'import json,os; print(json.load(open(os.path.expanduser("~/.openclaw/wallets/jason-eth/wallet.json")))["keystorePath"])')"
SVC="$(python3 -c 'import json,os; print(json.load(open(os.path.expanduser("~/.openclaw/wallets/jason-eth/wallet.json")))["keychainService"])')"
ACC="$(python3 -c 'import json,os; print(json.load(open(os.path.expanduser("~/.openclaw/wallets/jason-eth/wallet.json")))["keychainAccount"])')"

PASS="$(security find-generic-password -a "$ACC" -s "$SVC" -w)"
TMPPASS="$(mktemp)"
chmod 600 "$TMPPASS"
printf '%s' "$PASS" > "$TMPPASS"
unset PASS

# Send ETH transfer. Note: this will broadcast to mainnet.
cast send "$TO" --value "$VALUE" --rpc-url "$RPC" --keystore "$KS" --password-file "$TMPPASS"

rm -f "$TMPPASS"
