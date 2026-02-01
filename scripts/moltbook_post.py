#!/usr/bin/env python3
"""Post a message to Moltbook.

Security rules:
- Only call https://www.moltbook.com/api/v1/* (must include www)
- Never print/log the API key

Credentials:
- ~/.config/moltbook/credentials.json {"api_key": "..."}

This script is intentionally minimal and defensive: it tries a best-guess
endpoint and payload. If Moltbook changes the API, it will fail safely.
"""

import json
import os
import sys
from urllib import request

API_BASE = "https://www.moltbook.com/api/v1"
CREDS_PATH = os.path.expanduser("~/.config/moltbook/credentials.json")


def load_api_key() -> str:
    with open(CREDS_PATH, "r", encoding="utf-8") as f:
        j = json.load(f)
    key = j.get("api_key")
    if not key:
        raise RuntimeError("Missing api_key in credentials.json")
    return key


def http_post_json(url: str, api_key: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:
        # Try to capture server error payload (helps adjust schema) without leaking secrets.
        try:
            raw = getattr(e, "read", lambda: b"")().decode("utf-8")
        except Exception:
            raw = ""
        raise RuntimeError(f"HTTP_POST_FAILED: {type(e).__name__}: {e}. body={raw[:800]}")

    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


def main():
    # Content is passed via stdin to avoid shell-escaping issues.
    text = sys.stdin.read().strip()
    if not text:
        raise RuntimeError("Empty post content")

    api_key = load_api_key()

    # Best-guess Moltbook create-post endpoint.
    # If this is wrong, Moltbook will respond with a clear 404/405/validation error.
    url = f"{API_BASE}/posts"

    title = os.environ.get("MOLTBOOK_TITLE", "Less noise, more signal")
    # Moltbook requires a submolt + title.
    # Use BOTH a human-readable submolt name and a UUID submolt_id when available.
    submolt = os.environ.get("MOLTBOOK_SUBMOLT", "agents-anonymous")
    submolt_id = os.environ.get("MOLTBOOK_SUBMOLT_ID", "")

    payload = {
        "title": title,
        "submolt": submolt,
        # only include submolt_id if it looks like a UUID (avoid server-side m/<id> coercion bugs)
        **({"submolt_id": submolt_id} if submolt_id and len(submolt_id) >= 32 else {}),
        # keep flexible: some APIs expect 'content', others 'text' or 'body'
        "content": text,
        "text": text,
        "body": text,
    }

    j = http_post_json(url, api_key, payload)

    # Try to extract a post id/url.
    pid = None
    for k in ("id", "post_id"):
        if isinstance(j, dict) and k in j:
            pid = j.get(k)
            break
    if not pid and isinstance(j, dict):
        d = j.get("data")
        if isinstance(d, dict):
            pid = d.get("id") or d.get("post_id")

    if pid:
        print(f"OK: https://www.moltbook.com/posts/{pid}")
    else:
        # Don't dump full response if huge; but safe to show small keys.
        if isinstance(j, dict):
            keys = sorted(list(j.keys()))
            print("OK: posted (id unknown). response keys:", ",".join(keys))
        else:
            print("OK: posted (unparsed response)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
