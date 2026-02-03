#!/bin/bash
set -euo pipefail

# Read-only check: find recent unread in iCloud Inbox (kimihome@mac.com).
# Output a short summary to stdout ONLY when there is actionable unread.
# Do NOT mark messages as read.

osascript <<'APPLESCRIPT'
set cutoffDate to (current date) - (2 * hours)
set out to ""
set found to 0

tell application "Mail"
	-- iCloud inbox
	set theInbox to inbox
	set unreadMessages to (messages of theInbox whose read status is false and date received is greater than cutoffDate)
	repeat with m in unreadMessages
		try
			set found to found + 1
			set s to (sender of m) as text
			set subj to (subject of m) as text
			set d to (date received of m) as text
			set out to out & found & ") " & d & " | " & s & " | " & subj & linefeed
		on error
		end try
		if found >= 5 then exit repeat
	end repeat
end tell

if found is 0 then
	return "NO_SIGNAL"
end if

return out
APPLESCRIPT
