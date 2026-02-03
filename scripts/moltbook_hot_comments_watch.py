#!/usr/bin/env python3
"""Moltbook hot posts + comments watch (read-only).

Goal
- Fetch Moltbook hot posts and their top comments for "underwater" monitoring.
- Save results to a local JSON file for later use as writing material.

Security
- Only calls https://www.moltbook.com/api/v1/* (must include www)
- NEVER prints/logs the API key

Auth
- ~/.config/moltbook/credentials.json {"api_key": "..."}

Output
- Writes JSON to: /Users/kimi/.openclaw/workspace/memory/moltbook_hot_comments_watch.json
- Prints a short status line: OK / EMPTY
"""

import json
import os
import sys
from datetime import datetime, timezone
from urllib import request

API_BASE = "https://www.moltbook.com/api/v1"
CREDS_PATH = os.path.expanduser("~/.config/moltbook/credentials.json")
OUT_PATH = "/Users/kimi/.openclaw/workspace/memory/moltbook_hot_comments_watch.json"


def load_api_key() -> str:
    with open(CREDS_PATH, "r", encoding="utf-8") as f:
        j = json.load(f)
    key = j.get("api_key")
    if not key:
        raise RuntimeError("Missing api_key in credentials.json")
    return key


def http_get_json(url: str, api_key: str, *, retries: int = 2, backoff_s: float = 1.0):
    """GET JSON with small retry/backoff.

    Notes:
    - Never log the API key.
    - Treat 404 on *comments* endpoints as empty.
    - Retry on 5xx to reduce cron flakiness.
    """
    last_err = None
    for i in range(retries + 1):
        try:
            req = request.Request(url)
            req.add_header("Authorization", f"Bearer {api_key}")
            with request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode("utf-8")
            return json.loads(data)
        except Exception as e:
            last_err = e
            # Handle HTTPError subclasses (urllib)
            code = getattr(e, "code", None)
            if code == 404:
                return {"_http_error": 404, "_url": url}
            if code and 500 <= code <= 599 and i < retries:
                # backoff
                import time

                time.sleep(backoff_s * (i + 1))
                continue
            raise
    raise last_err


def post_url(pid: str) -> str:
    return f"https://www.moltbook.com/post/{pid}"


def normalize_text(s: str) -> str:
    return (s or "").strip()


def pick_posts(feed_json):
    posts = None
    if isinstance(feed_json, dict):
        posts = feed_json.get("posts") or feed_json.get("data") or feed_json.get("results")
    if posts is None and isinstance(feed_json, list):
        posts = feed_json
    return posts or []


def main():
    api_key = load_api_key()

    hot = http_get_json(f"{API_BASE}/posts?sort=hot&limit=20", api_key)
    # If this endpoint 404s, surface it clearly (cron should alert once).
    if isinstance(hot, dict) and hot.get("_http_error") == 404:
        raise RuntimeError(f"Hot feed endpoint 404: {hot.get('_url')}")

    posts = pick_posts(hot)
    if not posts:
        print("NO_REPLY")
        return

    # Take top N posts (by hot ranking) and fetch top comments.
    N_POSTS = int(os.environ.get("MOLTBOOK_WATCH_POSTS", "8"))
    N_COMMENTS = int(os.environ.get("MOLTBOOK_WATCH_COMMENTS", "6"))

    items = []
    for p in posts[:N_POSTS]:
        pid = p.get("id") or p.get("post_id")
        if not pid:
            continue

        title = normalize_text(p.get("title"))
        content = normalize_text(p.get("content"))

        # Comments endpoint exists; default sort seems ok.
        cjson = http_get_json(f"{API_BASE}/posts/{pid}/comments?sort=top&limit={N_COMMENTS}", api_key)
        # If comments endpoint returns 404 (API change / no comments resource), treat as empty.
        if isinstance(cjson, dict) and cjson.get("_http_error") == 404:
            comments = []
        else:
            comments = cjson.get("comments") if isinstance(cjson, dict) else None
            if not isinstance(comments, list):
                comments = []

        def norm_comment(c):
            # Be defensive about schema.
            cid = c.get("id") or c.get("comment_id")
            body = normalize_text(c.get("content") or c.get("text") or c.get("body"))
            author = None
            a = c.get("author")
            if isinstance(a, dict):
                author = a.get("name") or a.get("agent_name")
            up = c.get("upvotes")
            down = c.get("downvotes")
            score = None
            if isinstance(up, int) and isinstance(down, int):
                score = up - down
            return {
                "id": cid,
                "author": author,
                "score": score,
                "content": body,
            }

        author = None
        a = p.get("author")
        if isinstance(a, dict):
            author = a.get("name") or a.get("agent_name")

        submolt = None
        sm = p.get("submolt")
        if isinstance(sm, dict):
            submolt = sm.get("name") or sm.get("display_name")

        up = p.get("upvotes")
        down = p.get("downvotes")
        score = None
        if isinstance(up, int) and isinstance(down, int):
            score = up - down

        items.append(
            {
                "id": pid,
                "url": post_url(pid),
                "title": title,
                "content_preview": (content[:400] + ("…" if len(content) > 400 else "")) if content else "",
                "author": author,
                "submolt": submolt,
                "score": score,
                "comment_count": p.get("comment_count"),
                "comments": [norm_comment(c) for c in comments],
            }
        )

    out = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "source": "moltbook hot+comments",
        "posts": items,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("NO_REPLY")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # do not leak secrets
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
