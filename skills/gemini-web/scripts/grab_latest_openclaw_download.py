#!/usr/bin/env python3
"""Grab the latest OpenClaw browser download from Chrome History and copy it out.

Why:
- OpenClaw uses a Playwright-controlled Chrome profile.
- Downloads often land in a temp artifacts directory (e.g. /var/folders/.../T/playwright-artifacts-*/<uuid>)
- The file may be ephemeral; copy it to ~/Downloads immediately.

Usage:
  python3 skills/gemini-web/scripts/grab_latest_openclaw_download.py \
    --out /Users/kimi/Downloads/nano_pro_fullsize.png

It will:
- Copy the locked History SQLite DB to a temp file
- Read the most recent row in `downloads`
- Copy `current_path` to --out

Note:
- This script assumes the download is already completed.
"""

import argparse
import os
import shutil
import sqlite3
import sys
import time

DEFAULT_HISTORY = "/Users/kimi/.openclaw/browser/openclaw/user-data/Default/History"


def read_latest_download(history_path: str):
    if not os.path.exists(history_path):
        raise FileNotFoundError(history_path)

    tmp = f"/Users/kimi/.openclaw/workspace/tmp_history_copy_{int(time.time())}.sqlite"
    shutil.copy2(history_path, tmp)

    con = sqlite3.connect(tmp)
    cur = con.cursor()
    row = cur.execute(
        "select id, current_path, target_path, total_bytes, state, start_time from downloads order by start_time desc limit 1"
    ).fetchone()
    con.close()
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", default=DEFAULT_HISTORY)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    row = read_latest_download(args.history)
    if not row:
        print("No downloads found.", file=sys.stderr)
        return 2

    id_, current_path, target_path, total_bytes, state, start_time = row

    if not current_path or not os.path.exists(current_path):
        print(f"Latest download path not found on disk: {current_path}", file=sys.stderr)
        return 3

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    shutil.copy2(current_path, args.out)

    print(
        f"OK id={id_} bytes={total_bytes} state={state} copied_from={current_path} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
