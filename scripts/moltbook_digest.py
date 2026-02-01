#!/usr/bin/env python3
"""Moltbook digest (read-only).

- Uses ~/.config/moltbook/credentials.json (api_key)
- Fetches hot posts and formats a concise Chinese summary.
- NEVER prints or logs the API key.
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


def http_get_json(url: str, api_key: str):
    req = request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    with request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")
    return json.loads(data)


def main():
    api_key = load_api_key()

    # Hot feed
    url = f"{API_BASE}/posts?sort=hot&limit=25"
    j = http_get_json(url, api_key)

    # The API may return either {posts:[...]} or {success:true, posts:[...]}
    posts = j.get("posts") or j.get("data") or j.get("results")
    if posts is None and isinstance(j, list):
        posts = j
    if not posts:
        print("EMPTY")
        return

    def post_url(p):
        pid = p.get("id") or p.get("post_id")
        if not pid:
            return ""
        return f"https://www.moltbook.com/post/{pid}"

    # pick top 12-ish with best signal
    picked = []
    for p in posts:
        title = (p.get("title") or "").strip()
        content = (p.get("content") or "").strip()
        link = (p.get("url") or "").strip()
        if not (title or content or link):
            continue
        # skip ultra-short low-signal
        if len(title) < 4 and len(content) < 40 and not link:
            continue
        picked.append(p)
        if len(picked) >= 15:
            break

    if not picked:
        print("EMPTY")
        return

    lines = []
    lines.append("🦞 Moltbook 热门摘要（hot）")
    lines.append(f"共抓取 {len(posts)} 条，精选 {len(picked)} 条")

    for idx, p in enumerate(picked, 1):
        title = (p.get("title") or "").strip()
        content = (p.get("content") or "").strip().replace("\n", " ")
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

        label_parts = []
        if submolt:
            label_parts.append(f"r/{submolt}")
        if author:
            label_parts.append(f"@{author}")
        score = None
        if isinstance(up, int) and isinstance(down, int):
            score = up - down
        if score is not None:
            label_parts.append(f"score:{score}")

        label = " | ".join(label_parts)

        if title:
            summary = title
        else:
            summary = content[:80] + ("…" if len(content) > 80 else "")

        url2 = post_url(p)
        if not url2 and p.get("id"):
            url2 = str(p.get("id"))

        lines.append(f"{idx}. {summary}")
        if label:
            lines.append(f"   {label}")
        if p.get("url"):
            lines.append(f"   link: {p.get('url')}")
        if url2:
            lines.append(f"   molt: {url2}")

    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # do not leak secrets
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
