#!/usr/bin/env bash
set -euo pipefail

# Create a nightly diary page under Jason 🍎 日记本 and append a short auto-log.
# Idempotent per-day using a local state file.

META_FILE="/Users/kimi/.openclaw/workspace/memory/notion-jason-diary.json"
STATE_FILE="/Users/kimi/.openclaw/workspace/memory/notion_nightly_diary_state.json"
MEM_DIR="/Users/kimi/.openclaw/workspace/memory"

NOTION_API_KEY="$(python3 - <<'PY'
import json
with open('/Users/kimi/.openclaw/openclaw.json') as f:
  cfg=json.load(f)
print(cfg['skills']['entries']['notion']['apiKey'])
PY
)"

DIARY_PAGE_ID="$(python3 - <<'PY'
import json
m=json.load(open('/Users/kimi/.openclaw/workspace/memory/notion-jason-diary.json'))
print(m['diaryPage']['id'])
PY
)"

TODAY="$(date +%F)"

# idempotency
LAST=""
if [[ -f "$STATE_FILE" ]]; then
  LAST="$(python3 - <<'PY'
import json
try:
  s=json.load(open("/Users/kimi/.openclaw/workspace/memory/notion_nightly_diary_state.json"))
  print(s.get("lastDate",""))
except Exception:
  print("")
PY
)"
fi

if [[ "$LAST" == "$TODAY" ]]; then
  echo "OK: already wrote diary for $TODAY"
  exit 0
fi

TITLE="$TODAY Diary"

# 1) create page
python3 - <<'PY' > /tmp/notion_create_diary_page.json
import json, os
payload={
  "parent": {"page_id": os.environ["DIARY_PAGE_ID"]},
  "properties": {
    "title": {"title": [{"text": {"content": os.environ["TITLE"]}}]}
  }
}
print(json.dumps(payload))
PY

resp="$(curl -sS -X POST https://api.notion.com/v1/pages \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  --data @/tmp/notion_create_diary_page.json)"

PAGE_ID="$(echo "$resp" | python3 - <<'PY'
import json,sys
j=json.load(sys.stdin)
print(j.get('id',''))
PY
)"
PAGE_URL="$(echo "$resp" | python3 - <<'PY'
import json,sys
j=json.load(sys.stdin)
print(j.get('url',''))
PY
)"

if [[ -z "$PAGE_ID" ]]; then
  echo "ERROR: failed to create page: $resp" >&2
  exit 1
fi

# 2) content from local daily memory (best effort)
MEM_FILE="$MEM_DIR/$TODAY.md"
CONTENT=""
if [[ -f "$MEM_FILE" ]]; then
  CONTENT="$(sed -n '1,160p' "$MEM_FILE")"
else
  CONTENT="(No local memory file found for today.)"
fi

# Truncate to keep payload small
CONTENT="${CONTENT:0:1800}"

python3 - <<'PY' > /tmp/notion_diary_blocks.json
import json, os
text=os.environ.get('CONTENT','')
blocks=[
  {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Daily log (auto)"}}]}},
  {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":text}}]}},
  {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Reflection"}}]}},
  {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"(Jason will expand this reflection over time based on your preferences.)"}}]}},
]
print(json.dumps({"children": blocks}))
PY

curl -sS -X PATCH "https://api.notion.com/v1/blocks/$PAGE_ID/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  --data @/tmp/notion_diary_blocks.json >/dev/null

# 3) save state
python3 - <<'PY'
import json
path='/Users/kimi/.openclaw/workspace/memory/notion_nightly_diary_state.json'
json.dump({"lastDate": "%s"}, open(path,'w'), ensure_ascii=False, indent=2)
PY

echo "OK: created $TITLE"
echo "$PAGE_URL"
