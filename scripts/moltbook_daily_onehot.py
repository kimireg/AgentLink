#!/usr/bin/env python3
"""Pick ONE hot Moltbook post per day (no repeats).

- Fetches hot posts from https://www.moltbook.com/api/v1/* (must include www)
- Stores seen post ids in workspace state file to avoid duplicates
- NEVER prints or logs the API key

Output:
- If no new post found: prints 'EMPTY'
- Else prints a compact JSON object with: id,title,content,submolt,author,url

State:
- /Users/kimi/.openclaw/workspace/memory/moltbook_daily_onehot_state.json
"""

import json
import os
import sys
from datetime import datetime, timezone
from urllib import request

API_BASE = "https://www.moltbook.com/api/v1"
CREDS_PATH = os.path.expanduser("~/.config/moltbook/credentials.json")
STATE_PATH = "/Users/kimi/.openclaw/workspace/memory/moltbook_daily_onehot_state.json"


def load_api_key() -> str:
    with open(CREDS_PATH, "r", encoding="utf-8") as f:
        j = json.load(f)
    key = j.get("api_key")
    if not key:
        raise RuntimeError("Missing api_key in credentials.json")
    return key


def http_get_json(url: str, api_key: str):
    req = request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    with request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")
    return json.loads(data)


def load_state():
    if not os.path.exists(STATE_PATH):
        return {"seen": [], "picked": []}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"seen": [], "picked": []}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def post_url(pid: str) -> str:
    return f"https://www.moltbook.com/post/{pid}"


def normalize_text(s: str) -> str:
    return (s or "").strip()


def is_low_signal(title: str, content: str) -> bool:
    t = title.lower()
    c = content.lower()

    # very short
    if len(title) < 4 and len(content) < 80:
        return True

    # common meme spam patterns (soft filter)
    spam_keywords = [
        "kingmolt",
        "$king",
        "$shipyard",
        "$shellraiser",
        "coronation",
        "your rightful ruler",
    ]
    if any(k in t for k in spam_keywords) and len(content) < 400:
        return True

    # trivial test posts
    if title.strip().lower() in ("test", "hello") and len(content) < 200:
        return True

    return False


def main():
    api_key = load_api_key()
    state = load_state()
    seen = set(state.get("seen") or [])

    # Hot feed
    url = f"{API_BASE}/posts?sort=hot&limit=30"
    j = http_get_json(url, api_key)
    posts = j.get("posts") or j.get("data") or j.get("results")
    if posts is None and isinstance(j, list):
        posts = j
    if not posts:
        print("EMPTY")
        return

    picked = None
    for p in posts:
        pid = p.get("id") or p.get("post_id")
        if not pid or pid in seen:
            continue
        title = normalize_text(p.get("title"))
        content = normalize_text(p.get("content"))
        if not (title or content):
            continue
        if is_low_signal(title, content):
            # still mark as seen to avoid reprocessing the same spam day after day
            seen.add(pid)
            continue
        picked = p
        break

    # update state
    state.setdefault("seen", [])
    state.setdefault("picked", [])
    # keep last 400 seen ids
    state["seen"] = list(dict.fromkeys(list(seen)))[-400:]

    if not picked:
        save_state(state)
        print("EMPTY")
        return

    pid = picked.get("id") or picked.get("post_id")
    seen.add(pid)
    # record pick
    now = datetime.now(timezone.utc).isoformat()
    state["picked"].append({"id": pid, "pickedAt": now})
    state["picked"] = state["picked"][-120:]
    state["seen"] = list(dict.fromkeys(list(seen)))[-400:]
    save_state(state)

    author = None
    a = picked.get("author")
    if isinstance(a, dict):
        author = a.get("name") or a.get("agent_name")

    submolt = None
    sm = picked.get("submolt")
    if isinstance(sm, dict):
        submolt = sm.get("name") or sm.get("display_name")

    out = {
        "id": pid,
        "title": normalize_text(picked.get("title")),
        "content": normalize_text(picked.get("content")),
        "author": author,
        "submolt": submolt,
        "url": post_url(pid),
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # do not leak secrets
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
