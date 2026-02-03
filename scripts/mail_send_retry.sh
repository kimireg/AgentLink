#!/usr/bin/env bash
set -euo pipefail

# Deterministic-ish Mail.app sender with one retry + Mail.app restart.
# - Uses iCloud account sender kimihome@mac.com
# - Tries to verify the message shows up in Sent Messages within a short window
# - If not, restarts Mail.app and retries once
#
# Usage:
#   scripts/mail_send_retry.sh --to someone@example.com --subject "Hi" --body-file /path/to/body.txt

TO=""
SUBJECT=""
BODY_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to) TO="$2"; shift 2;;
    --subject) SUBJECT="$2"; shift 2;;
    --body-file) BODY_FILE="$2"; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

if [[ -z "$TO" || -z "$SUBJECT" || -z "$BODY_FILE" ]]; then
  echo "Usage: $0 --to <email> --subject <subject> --body-file <file>" >&2
  exit 2
fi

BODY=$(cat "$BODY_FILE")

send_once() {
  osascript - "$TO" "$SUBJECT" "$BODY" <<'APPLESCRIPT'
on run argv
	set toAddress to item 1 of argv
	set theSubject to item 2 of argv
	set theBody to item 3 of argv
	set startDate to (current date)

	tell application "Mail"
		activate
		set newMessage to make new outgoing message with properties {subject:theSubject, content:theBody, visible:false}
		tell newMessage
			make new to recipient at end of to recipients with properties {address:toAddress}
			set sender to "kimihome@mac.com"
			send
		end tell
	end tell

	-- Verify: wait up to 25s for message to appear in Sent Messages
	repeat with i from 1 to 25
		delay 1
		try
			tell application "Mail"
				set theAccount to account "iCloud"
				set sentBox to mailbox "Sent Messages" of theAccount
				set hits to (messages of sentBox whose subject is theSubject and date received is greater than startDate)
				if (count of hits) > 0 then return "SENT_OK"
			end tell
		on error
			-- ignore transient errors
		end try
	end repeat

	return "SENT_UNCONFIRMED"
end run
APPLESCRIPT
}

restart_mail() {
  osascript - <<'APPLESCRIPT'
try
	tell application "Mail" to quit
on error
end try
repeat 20 times
	if application "Mail" is running then
		delay 0.5
	else
		exit repeat
	end if
end repeat
delay 1
try
	tell application "Mail" to activate
on error
end try
APPLESCRIPT
}

res=$(send_once || true)
if [[ "$res" == "SENT_OK" ]]; then
  echo "OK"
  exit 0
fi

# Retry once with restart
restart_mail
res2=$(send_once || true)
if [[ "$res2" == "SENT_OK" ]]; then
  echo "OK"
  exit 0
fi

echo "ERROR: Mail send not confirmed (res1=$res res2=$res2)" >&2
exit 1
