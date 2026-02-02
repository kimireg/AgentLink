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
# We MUST have an interactive TTY; otherwise bash `read` will fail silently.
if ! tty -s 2>/dev/null; then
  echo "ERROR: No interactive TTY detected. Please run this from a normal Terminal window." >&2
  echo "Tip: run: bash /Users/kimi/.openclaw/workspace/scripts/jason_eth_escrow_init.sh" >&2
  exit 1
fi

TTY_DEV="/dev/tty"
if [[ ! -r "$TTY_DEV" ]]; then
  echo "ERROR: Cannot access $TTY_DEV (device not configured). Try running in a fresh Terminal tab." >&2
  exit 1
fi

read -r -s -p "Set escrow encryption passphrase (Kimi controls; not stored): " ENC1 < "$TTY_DEV"
printf '\n' > "$TTY_DEV"
read -r -s -p "Confirm passphrase: " ENC2 < "$TTY_DEV"
printf '\n' > "$TTY_DEV"

if [[ "$ENC1" != "$ENC2" ]]; then
  echo "ERROR: passphrases do not match" >&2
  exit 1
fi

# Encrypt. Use AES-256-GCM + PBKDF2.
# Use stdin for plaintext, avoid writing to disk.
# Store OpenSSL salted format.
# Encrypt.
# Avoid putting the passphrase on argv. Use a temp file with 0600 perms and delete immediately.
TMPPASS="$(mktemp)"
chmod 600 "$TMPPASS"
printf '%s' "$ENC1" > "$TMPPASS"

# Plaintext (keystore password) comes via stdin; passphrase is read from TMPPASS.
# If this fails, print a clear error (do not leak secrets).
if ! printf '%s' "$PASS" | openssl enc -aes-256-gcm -salt -pbkdf2 -iter 200000 \
  -pass file:"$TMPPASS" -out "$ESCROW_PATH"; then
  code=$?
  rm -f "$TMPPASS" "$ESCROW_PATH"
  unset PASS ENC1 ENC2
  echo "ERROR: openssl encryption failed (exit $code)." >&2
  echo "Tip: run 'openssl version' to verify OpenSSL is available." >&2
  exit $code
fi

rm -f "$TMPPASS"
unset PASS ENC1 ENC2
chmod 600 "$ESCROW_PATH"

echo "OK: escrow written to $ESCROW_PATH (encrypted)."
