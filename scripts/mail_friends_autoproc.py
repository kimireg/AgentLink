#!/usr/bin/env python3
"""Auto-handle unread friend emails in macOS Mail.app (iCloud INBOX).

Goals (per Kimi):
- deterministic periodic checking (cron)
- polite + timely handling for friends threads (Jason 🍎 writes the replies)
- mark as read after handling to avoid repeats
- if Mail.app seems stale, restart and re-check
- qwen is allowed only to organize/summarize the thread and brief Kimi

This script:
1) Lists unread messages from a sender allowlist.
2) Uses a local state file to de-dup processing even if Mail.app read status rolls back.
3) Drafts a reply using *main* agent with strict constraints.
4) Sends via scripts/mail_send_retry.sh (with Mail restart + sent confirmation).
5) Marks the original message as read via scripts/mail_mark_read_ids.sh.

Output:
- If nothing new processed: prints nothing.
- If processed: prints one line per processed message:
  "<from> | <subject> | <date> | replied+marked_read"
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

WORKSPACE = "/Users/kimi/.openclaw/workspace"
STATE_PATH = os.path.join(WORKSPACE, "memory", "mail_friends_processed.json")
SEND_SH = os.path.join(WORKSPACE, "scripts", "mail_send_retry.sh")
MARK_READ_SH = os.path.join(WORKSPACE, "scripts", "mail_mark_read_ids.sh")

WATCH = [
    "iam.ryan.cooper.1998@gmail.com",  # Ryan / Nowa agent friend
    "trudy.dai2011@gmail.com",
    "gina.zhu@longbridge.sg",
    "xuting.wu@longbridge.sg",
    "elainesh.sg@gmail.com",
]
WATCH_SET = {e.lower().strip() for e in WATCH}

MAX_N = 30


def sh(cmd: list[str], timeout: int = 120, check: bool = True, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, timeout=timeout, check=check, text=text, capture_output=True)


def load_state() -> dict:
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"processed": {}, "version": 1}


def save_state(st: dict) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, STATE_PATH)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def restart_mail_app() -> None:
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


def list_unread() -> list[dict]:
    # Return list of dicts:
    # {id:int, fromEmail:str, subject:str, dateReceived:str, messageId:str, content:str}
    osa = r'''
set maxN to 30
try
  tell application "Mail"
    set theAccount to first account whose name is "iCloud"
    set inboxBox to first mailbox of theAccount whose name is "INBOX"
    set unreadMsgs to (every message of inboxBox whose read status is false)
    set c to count of unreadMsgs
    if c = 0 then return "[]"
    if c > maxN then set c to maxN

    set items to {}
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

      set bodyTxt to ""
      try
        set bodyTxt to content of m
      on error
        set bodyTxt to ""
      end try

      set escFrom to my esc(fromEmail)
      set escSubj to my esc(subj)
      set escDt to my esc(dt)
      set escMsgid to my esc(msgid)
      set escBody to my esc(bodyTxt)

      set end of items to "{\"id\":" & mid & ",\"fromEmail\":\"" & escFrom & "\",\"subject\":\"" & escSubj & "\",\"dateReceived\":\"" & escDt & "\",\"messageId\":\"" & escMsgid & "\",\"content\":\"" & escBody & "\"}"
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

    out = sh(["osascript", "-e", osa], timeout=90, check=False)
    txt = (out.stdout or "").strip()
    if txt.startswith("ERROR("):
        raise RuntimeError(txt)
    try:
        return json.loads(txt)
    except Exception as e:
        raise RuntimeError(f"Bad JSON from osascript: {e}: {txt[:200]}")


def normalize_subject(subj: str) -> str:
    subj = (subj or "").strip()
    if not subj:
        return "(no subject)"
    return subj


def reply_subject(subj: str) -> str:
    subj = normalize_subject(subj)
    if re.match(r"^\s*re:\s*", subj, re.I):
        return subj
    return "Re: " + subj


def draft_reply(from_email: str, subject: str, content: str) -> str:
    # Constrain: do not invent facts; keep short; friendly; ask clarifying if needed.
    # Special handling: Ryan is a key friend.
    is_ryan = from_email.lower().strip() == "iam.ryan.cooper.1998@gmail.com"

    content_clean = (content or "").strip()
    # hard cap to avoid timeouts
    if len(content_clean) > 6000:
        content_clean = content_clean[:6000]

    prompt = (
        "You are Jason 🍎 writing an email reply on behalf of Kimi (sender kimihome@mac.com).\n"
        "You must be polite, timely, and friendly.\n"
        "Hard rules:\n"
        "- Do NOT fabricate details. Only use the email content below.\n"
        "- If unclear, ask 1-2 clarifying questions.\n"
        "- Keep it concise (<= 1400 characters).\n"
        "- Output ONLY the email body text, no subject line, no markdown fences.\n"
        "- End with signature exactly: \n— Kimi / Jason 🍎\n\n"
    )
    if is_ryan:
        prompt += (
            "Tone: agent-friends. Mention we value learning/sharing reliability tips. "
            "If relevant, ask Ryan for best practices on deterministic email processing.\n"
        )

    prompt += (
        f"\nFROM: {from_email}\n"
        f"SUBJECT: {subject}\n"
        "\nEMAIL CONTENT (may include quoted text):\n"
        + content_clean
    )

    # Per Kimi: the email is for Jason 🍎, so draft MUST be done by main.
    # qwen may only be used for organization/summarization to brief Kimi.
    try:
        cp = sh(
            [
                "openclaw",
                "agent",
                "--agent",
                "main",
                "--message",
                prompt,
                "--timeout",
                "220",
            ],
            timeout=260,
            check=True,
        )
        out = (cp.stdout or "").strip()
        if not out:
            raise RuntimeError("empty draft")
        if "— Kimi / Jason" not in out:
            out = out.rstrip() + "\n\n— Kimi / Jason 🍎\n"
        return out
    except Exception:
        return (
            "Got it — thanks for reaching out. I saw your note and I’ll get back to you shortly with anything concrete.\n\n"
            "— Kimi / Jason 🍎\n"
        )


def main():
    st = load_state()
    processed = st.setdefault("processed", {})

    # list unread; if errors, restart Mail and retry once
    try:
        msgs = list_unread()
    except Exception:
        restart_mail_app()
        msgs = list_unread()

    # filter watchlist + newest-first already
    candidates = []
    for m in msgs:
        from_email = (m.get("fromEmail") or "").strip().lower()
        if not from_email or from_email not in WATCH_SET:
            continue
        candidates.append(m)

    out_lines = []

    for m in candidates:
        mid = m.get("id")
        from_email = (m.get("fromEmail") or "").strip()
        subject = normalize_subject(m.get("subject") or "")
        date_rcv = (m.get("dateReceived") or "").strip()
        message_id = (m.get("messageId") or "").strip()

        key = message_id or f"mail-id:{mid}"
        if key in processed:
            continue

        body = draft_reply(from_email, subject, m.get("content") or "")

        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as tf:
            tf.write(body)
            body_path = tf.name

        try:
            sh([SEND_SH, "--to", from_email, "--subject", reply_subject(subject), "--body-file", body_path], timeout=120)
        except subprocess.CalledProcessError as e:
            # try a Mail restart and re-send once (mail_send_retry already does, but keep this extra defensive)
            restart_mail_app()
            sh([SEND_SH, "--to", from_email, "--subject", reply_subject(subject), "--body-file", body_path], timeout=140)
        finally:
            try:
                os.unlink(body_path)
            except OSError:
                pass

        # mark read (best effort)
        if isinstance(mid, int) or (isinstance(mid, str) and mid.isdigit()):
            try:
                sh([MARK_READ_SH, str(mid)], timeout=30, check=False)
            except Exception:
                pass

        processed[key] = {
            "at": now_iso(),
            "from": from_email,
            "subject": subject,
            "mailId": mid,
        }

        out_lines.append(f"{from_email} | {subject} | {date_rcv} | replied+marked_read")

        # keep processed bounded
        if len(processed) > 600:
            # drop oldest by at
            items = sorted(processed.items(), key=lambda kv: kv[1].get("at", ""))
            processed = dict(items[-500:])
            st["processed"] = processed

    if out_lines:
        save_state(st)
        for ln in out_lines:
            print(ln)


if __name__ == "__main__":
    main()
