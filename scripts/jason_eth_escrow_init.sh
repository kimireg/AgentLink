#!/usr/bin/env bash
set -euo pipefail

# Create an encrypted escrow copy of the Jason ETH keystore password.
# - Reads keystore password from macOS Keychain (service eth.jason.keystore.pass, account jason)
# - Encrypts it with a Kimi-controlled passphrase (prompted, not stored)
# - Writes to ~/.openclaw/wallets/jason-eth/escrow.enc
# - Does NOT print secrets

ESCROW_PATH="$HOME/.openclaw/wallets/jason-eth/escrow.enc"
mkdir -p "$(dirname "$ESCROW_PATH")"

# Read password from Keychain
PASS="$(security find-generic-password -a jason -s eth.jason.keystore.pass -w)"

# Prompt for encryption passphrase (Kimi controls this)
read -r -s -p "Set escrow encryption passphrase (Kimi controls; not stored): " ENC1
echo
read -r -s -p "Confirm passphrase: " ENC2
echo

if [[ "$ENC1" != "$ENC2" ]]; then
  echo "ERROR: passphrases do not match" >&2
  exit 1
fi

# Encrypt. Use AES-256-GCM + PBKDF2.
# Use stdin for plaintext, avoid writing to disk.
# Store OpenSSL salted format.
printf '%s' "$PASS" | openssl enc -aes-256-gcm -salt -pbkdf2 -iter 200000 -pass stdin -out "$ESCROW_PATH" <<<"$ENC1" 2>/dev/null

unset PASS ENC1 ENC2
chmod 600 "$ESCROW_PATH"

echo "OK: escrow written to $ESCROW_PATH (encrypted)."
