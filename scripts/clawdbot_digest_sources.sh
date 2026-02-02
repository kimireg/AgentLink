#!/usr/bin/env bash
set -euo pipefail

# Fetch sources for Clawdbot weekly digest without Brave web_search.
# Outputs a compact JSON payload to stdout.

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

fetch() {
  local url="$1"
  curl -fsSL \
    -H "User-Agent: ${UA}" \
    -H "Accept: application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8" \
    "$url"
}

# Reddit RSS (new) — use old.reddit.com to avoid 403 blocks
REDDIT_RSS_1="https://old.reddit.com/r/clawdbot/new/.rss?limit=20"
REDDIT_RSS_2="https://old.reddit.com/r/OpenClaw/search.rss?q=clawdbot&restrict_sr=1&sort=new&t=week"

# GitHub releases Atom
GH_RELEASES="https://github.com/clawdbot/clawdbot/releases.atom"

r1="$(fetch "$REDDIT_RSS_1" || true)"
r2="$(fetch "$REDDIT_RSS_2" || true)"
gh="$(fetch "$GH_RELEASES" || true)"

R1="$r1" R2="$r2" GH="$gh" python3 - <<'PY'
import json, os
out={
  'reddit':{
    'r_clawdbot_new_rss': os.environ.get('R1',''),
    'r_openclaw_search_rss': os.environ.get('R2',''),
  },
  'github':{
    'releases_atom': os.environ.get('GH',''),
  }
}
print(json.dumps(out, ensure_ascii=False))
PY
