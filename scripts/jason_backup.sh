#!/usr/bin/env bash
set -euo pipefail

# Jason Backup (OpenClaw) — daily local backups
# Goal: maximize restore capability by capturing OpenClaw config + workspace + key local auth state.

BACKUP_ROOT="/Users/kimi/Jason Backup"
DATE_TAG="$(date +%F)"
TS_TAG="$(date +%F_%H-%M-%S)"
DEST_DIR="$BACKUP_ROOT/$DATE_TAG"

mkdir -p "$DEST_DIR"

# Sources (best-effort; some may not exist)
SOURCES=(
  "/Users/kimi/.openclaw"
  "/Users/kimi/.openclaw/workspace"
  "/Users/kimi/.claude"
  "/Users/kimi/.claude.json"
  "/Users/kimi/.bashrc"
  "/Users/kimi/.zshrc"
  "/Users/kimi/.config/bird"
  "/Users/kimi/.config/bird/config.json5"
)

# Build tar list of existing sources only
EXISTING=()
for p in "${SOURCES[@]}"; do
  if [[ -e "$p" ]]; then
    EXISTING+=("$p")
  fi
done

ARCHIVE="$DEST_DIR/jason-backup-$TS_TAG.tgz"
MANIFEST="$DEST_DIR/manifest-$TS_TAG.txt"

{
  echo "Jason Backup"
  echo "timestamp: $(date -Iseconds)"
  echo "archive: $ARCHIVE"
  echo "included:"
  for p in "${EXISTING[@]}"; do
    echo "- $p"
  done
} > "$MANIFEST"

# Create archive (use -C / to preserve paths cleanly)
# We store absolute-ish paths by stripping leading '/'
pushd / >/dev/null
# shellcheck disable=SC2068
tar -czf "$ARCHIVE" ${EXISTING[@]/#\//} "$MANIFEST" 
popd >/dev/null

# Retention: keep last 10 days (by date folder name) under BACKUP_ROOT
# Remove directories older than 10 days.
find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -name "????-??-??" -mtime +9 -print0 | xargs -0 -r rm -rf

# Optional: prune empty dirs
find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -empty -print0 | xargs -0 -r rmdir

echo "OK: $ARCHIVE"
