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
# NOTE: when executed via non-interactive shells, `read` may not have a TTY.
# Force reading from /dev/tty so the prompt appears when run in Terminal.
if [[ ! -t 0 ]] && [[ ! -r /dev/tty ]]; then
  echo "ERROR: No TTY available for passphrase prompt. Run this in an interactive Terminal." >&2
  exit 1
fi

read -r -s -p "Set escrow encryption passphrase (Kimi controls; not stored): " ENC1 < /dev/tty
printf '\n' > /dev/tty
read -r -s -p "Confirm passphrase: " ENC2 < /dev/tty
printf '\n' > /dev/tty

if [[ "$ENC1" != "$ENC2" ]]; then
  echo "ERROR: passphrases do not match" >&2
  exit 1
fi

# Encrypt. Use AES-256-GCM + PBKDF2.
# Use stdin for plaintext, avoid writing to disk.
# Store OpenSSL salted format.
# Encrypt using a dedicated fd for the passphrase to avoid leaking it via argv.
# Plaintext (keystore password) comes via stdin; passphrase is provided on fd 3.
printf '%s' "$PASS" | openssl enc -aes-256-gcm -salt -pbkdf2 -iter 200000 \
  -pass file:/dev/fd/3 -out "$ESCROW_PATH" 3<<<"$ENC1" 2>/dev/null

unset PASS ENC1 ENC2
chmod 600 "$ESCROW_PATH"

echo "OK: escrow written to $ESCROW_PATH (encrypted)."
