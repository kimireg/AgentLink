#!/usr/bin/env python3
"""Router for iCloud INBOX mail handling.

Design goals (Kimi):
1) Stable periodic checking
2) Timely, polite handling for friend emails (Jason writes + sends + mark read)
3) For other actionable unread: notify Kimi (and optionally draft, but do not auto-send for work/high-risk)
4) After processing: mark as read (for auto-processed friend emails)
5) Mail.app flakiness: on error or suspicious empty, restart Mail.app and re-check

This script is intended to be run by cron. It is safe to run repeatedly.

Behavior:
- Always reads from iCloud -> INBOX.
- If unread from FRIEND_ALLOWLIST exists: run mail_friends_autoproc.py (which replies + marks read + local de-dup).
- If other unread exists: send ONE Telegram summary (de-dup via local state so we don't spam).

Exit:
- prints nothing on success/no-op.
- prints a short summary line if it sent a Telegram or processed friend emails.
"""

import json
import os
import subprocess
from datetime import datetime, timezone

WORKSPACE = "/Users/kimi/.openclaw/workspace"
STATE_PATH = os.path.join(WORKSPACE, "memory", "mail_inbox_router_state.json")
FRIENDS_AUTOPROC = os.path.join(WORKSPACE, "scripts", "mail_friends_autoproc.py")

FRIEND_ALLOWLIST = {
    "iam.ryan.cooper.1998@gmail.com",
    "trudy.dai2011@gmail.com",
    "gina.zhu@longbridge.sg",
    "xuting.wu@longbridge.sg",
    "elainesh.sg@gmail.com",
}

MAX_UNREAD = 40
MAX_NOTIFY = 10


def sh(cmd, timeout=90, check=True):
    return subprocess.run(cmd, timeout=timeout, check=check, text=True, capture_output=True)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_state():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"notified": {}, "version": 1}


def save_state(st):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, STATE_PATH)


def restart_mail_app():
    osa = r'''
try
	tell application "Mail" to quit
on error
end try
repeat 30 times
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
'''
    sh(["osascript", "-e", osa], timeout=60, check=False)


def list_unread():
    # returns list of dicts: {id:int, fromEmail:str, subject:str, dateReceived:str, messageId:str}
    osa = f'''
set maxN to {MAX_UNREAD}
try
  tell application "Mail"
    set theAccount to first account whose name is "iCloud"
    set inboxBox to first mailbox of theAccount whose name is "INBOX"
    set unreadMsgs to (every message of inboxBox whose read status is false)
    set c to count of unreadMsgs
    if c = 0 then return "[]"
    if c > maxN then set c to maxN

    set items to {{}}
    repeat with i from 1 to c
      set m to item i of unreadMsgs
      set fromTxt to sender of m
      set subj to subject of m
      set dt to (date received of m) as string
      set mid to id of m

      set fromEmail to fromTxt
      if fromTxt contains "<" and fromTxt contains ">" then
        set text item delimiters of AppleScript to "<"
        set tmp1 to text item 2 of fromTxt
        set text item delimiters of AppleScript to ">"
        set fromEmail to text item 1 of tmp1
        set text item delimiters of AppleScript to ""
      end if

      set msgid to ""
      try
        set msgid to message id of m
      on error
        set msgid to ""
      end try

      set escFrom to my esc(fromEmail)
      set escSubj to my esc(subj)
      set escDt to my esc(dt)
      set escMsgid to my esc(msgid)

      set end of items to "{{\"id\":" & mid & ",\"fromEmail\":\"" & escFrom & "\",\"subject\":\"" & escSubj & "\",\"dateReceived\":\"" & escDt & "\",\"messageId\":\"" & escMsgid & "\"}}"
    end repeat

    set text item delimiters of AppleScript to ","
    set outText to "[" & (items as string) & "]"
    set text item delimiters of AppleScript to ""
    return outText
  end tell
on error errMsg number errNum
  return "ERROR(" & errNum & "): " & errMsg
end try

on esc(t)
  if t is missing value then return ""
  set s to t as string
  set s to my replace(s, "\\", "\\\\")
  set s to my replace(s, "\"", "\\\"")
  set s to my replace(s, return, "\\n")
  set s to my replace(s, linefeed, "\\n")
  return s
end esc

on replace(theText, oldString, newString)
  set text item delimiters of AppleScript to oldString
  set theItems to text items of theText
  set text item delimiters of AppleScript to newString
  set theText to theItems as string
  set text item delimiters of AppleScript to ""
  return theText
end replace
'''

    cp = sh(["osascript", "-e", osa], timeout=90, check=False)
    txt = (cp.stdout or "").strip()
    if txt.startswith("ERROR("):
        raise RuntimeError(txt)
    return json.loads(txt)


def send_telegram(text: str):
    # use openclaw CLI to send; deterministic target
    sh([
        "openclaw", "message", "send",
        "--target", "469144235",
        "--message", text,
    ], timeout=40)


def main():
    st = load_state()
    notified = st.setdefault("notified", {})

    try:
        msgs = list_unread()
    except Exception:
        restart_mail_app()
        msgs = list_unread()

    friends = []
    others = []
    for m in msgs:
        em = (m.get("fromEmail") or "").strip().lower()
        if not em:
            continue
        if em in FRIEND_ALLOWLIST:
            friends.append(m)
        else:
            others.append(m)

    summary_bits = []

    if friends:
        # delegate to friend autoproc (handles send + mark-read + its own de-dup)
        cp = sh(["bash", "-lc", f"python3 {FRIENDS_AUTOPROC}"], timeout=220, check=False)
        out = (cp.stdout or "").strip()
        if out:
            summary_bits.append(f"friends_processed={len(out.splitlines())}")

    # Notify for others (de-dup per messageId/mailId)
    new_other_lines = []
    for m in others[:MAX_NOTIFY]:
        mid = m.get("id")
        msgid = (m.get("messageId") or "").strip()
        key = msgid or f"mail-id:{mid}"
        if key in notified:
            continue
        notified[key] = {"at": now_iso(), "from": m.get("fromEmail"), "subject": m.get("subject"), "mailId": mid}
        dt = (m.get("dateReceived") or "").strip()
        frm = (m.get("fromEmail") or "").strip()
        subj = (m.get("subject") or "").strip() or "(no subject)"
        new_other_lines.append(f"- {dt} | {frm} | {subj}")

    # keep bounded
    if len(notified) > 800:
        items = sorted(notified.items(), key=lambda kv: kv[1].get("at", ""))
        notified = dict(items[-600:])
        st["notified"] = notified

    if new_other_lines:
        save_state(st)
        msg = "📧 新邮件提醒（kimihome@mac.com）\n\n" + "\n".join(new_other_lines) + "\n\n（我可以帮你起草回复；工作/高风险邮件我会先给你 draft。）"
        send_telegram(msg)
        summary_bits.append(f"notified_others={len(new_other_lines)}")

    if summary_bits:
        print("OK " + ",".join(summary_bits))


if __name__ == "__main__":
    main()
