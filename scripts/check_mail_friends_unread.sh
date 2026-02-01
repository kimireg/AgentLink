#!/usr/bin/env bash
set -euo pipefail

# Read-only: list unread emails from selected friends in Mail.app (iCloud INBOX).
# Output format: "<email> | <subject> | <date>" (one per line)
# If no matches, prints nothing.

WATCH=(
  "trudy.dai2011@gmail.com"
  "gina.zhu@longbridge.sg"
  "xuting.wu@longbridge.sg"
  "elainesh.sg@gmail.com"
)

WATCH_SET=$(printf "%s\n" "${WATCH[@]}" | tr "[:upper:]" "[:lower:]")

RAW=$(osascript <<'APPLESCRIPT'
set maxN to 60
try
  tell application "Mail"
    set theAccount to first account whose name is "iCloud"
    set inboxBox to first mailbox of theAccount whose name is "INBOX"
    set unreadMsgs to (every message of inboxBox whose read status is false)
    set c to count of unreadMsgs
    if c = 0 then return ""
    if c > maxN then set c to maxN

    set outLines to {}
    repeat with i from 1 to c
      set m to item i of unreadMsgs
      set fromTxt to sender of m
      set subj to subject of m
      set dt to (date received of m) as string

      set fromEmail to fromTxt
      if fromTxt contains "<" and fromTxt contains ">" then
        set text item delimiters of AppleScript to "<"
        set tmp1 to text item 2 of fromTxt
        set text item delimiters of AppleScript to ">"
        set fromEmail to text item 1 of tmp1
        set text item delimiters of AppleScript to ""
      end if

      set end of outLines to (fromEmail & "\t" & subj & "\t" & dt)
    end repeat

    set text item delimiters of AppleScript to "\n"
    set outText to outLines as string
    set text item delimiters of AppleScript to ""
    return outText
  end tell
on error errMsg number errNum
  return "ERROR(" & errNum & "): " & errMsg
end try
APPLESCRIPT
)

if [[ "$RAW" == ERROR* ]]; then
  echo "$RAW" >&2
  exit 2
fi

TAB="$(printf "\t")"
while IFS="$TAB" read -r fromEmail subj dt; do
  [[ -z "${fromEmail:-}" ]] && continue
  eml=$(echo "$fromEmail" | tr "[:upper:]" "[:lower:]" | xargs)
  if ! grep -qx "$eml" <<< "$WATCH_SET"; then
    continue
  fi
  subj=${subj:-"(no subject)"}
  echo "$eml | $subj | $dt"
done <<< "$RAW"
