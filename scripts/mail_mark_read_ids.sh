#!/usr/bin/env bash
set -euo pipefail

# Mark specific Mail.app message IDs as read in iCloud INBOX.
# Usage:
#   bash scripts/mail_mark_read_ids.sh 248 249 250

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <mail-message-id> [id ...]" >&2
  exit 2
fi

osascript - "$@" <<'APPLESCRIPT'
on run argv
	tell application "Mail"
		set theAccount to account "iCloud"
		set inboxBox to mailbox "INBOX" of theAccount
		repeat with s in argv
			try
				set mid to s as integer
				set mlist to (messages of inboxBox whose id is mid)
				if (count of mlist) > 0 then
					set read status of item 1 of mlist to true
				end if
			on error
				-- ignore per-message errors
			end try
		end repeat
	end tell
	return "OK"
end run
APPLESCRIPT
