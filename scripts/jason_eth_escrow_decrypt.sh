#!/usr/bin/env bash
set -euo pipefail

# Decrypt escrow file to stdout (for recovery).
# NOTE: This prints the keystore password to stdout; use only during recovery.

ESCROW_PATH="$HOME/.openclaw/wallets/jason-eth/escrow.enc"

if [[ ! -f "$ESCROW_PATH" ]]; then
  echo "ERROR: missing escrow file at $ESCROW_PATH" >&2
  exit 1
fi

read -r -s -p "Enter escrow passphrase: " ENC
echo

# Decrypt and print to stdout
openssl enc -d -aes-256-gcm -pbkdf2 -iter 200000 -pass stdin -in "$ESCROW_PATH" <<<"$ENC"
