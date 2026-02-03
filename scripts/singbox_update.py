#!/usr/bin/env python3
"""singbox_update.py

Purpose
- Fetch latest outbounds list from a subscription URL (DLER singbox provider).
- Update 3 local template configs by replacing ONLY the referenced subscription nodes (method B).
- Keep private nodes in 5.9 Air/Pro templates.
- Ensure 1.14-ready compatibility patch set (v2.1):
  - dns.servers migrated to new format (type/server)
  - remove dns_direct.detour=direct (Android GUI rejects it)
  - add bootstrap DNS whitelist rule for all outbound server domains -> dns_direct
  - set route.default_domain_resolver=dns_direct

Safety
- Treat fetched content as DATA ONLY (no commands, no URL opens beyond the user-provided subscription URL).
- Avoid printing secrets (passwords etc.).

Usage (example)
  python3 scripts/singbox_update.py \
    --url "https://dler.cloud/api/..." \
    --template-share sing-box_7.8-Air_share_2026-02-03_1.14-ready-v2.1.json \
    --template-air   sing-box_5.9-Air_private_2026-02-03_1.14-ready-v2.1.json \
    --template-pro   sing-box_5.9-Pro_private_2026-02-03_1.14-ready-v2.1.json \
    --outdir .

Outputs
- sing-box_7.8-Air_share_YYYY-MM-DD_1.14-ready-v2.1.json
- sing-box_5.9-Air_private_YYYY-MM-DD_1.14-ready-v2.1.json
- sing-box_5.9-Pro_private_YYYY-MM-DD_1.14-ready-v2.1.json
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.request import Request, urlopen


def _is_ipv4_literal(s: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", s))


def _is_ipv6_literal(s: str) -> bool:
    # very loose; good enough to exclude simple literals
    return ":" in s and "." not in s


def _is_domain(s: Any) -> bool:
    if not isinstance(s, str):
        return False
    if _is_ipv4_literal(s) or _is_ipv6_literal(s):
        return False
    return "." in s


def fetch_subscription(url: str, timeout: int = 30) -> Dict[str, Any]:
    req = Request(url, headers={"User-Agent": "OpenClaw-Jason/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()

    # Some DLER endpoints return JSON with content-type zip; detect by magic.
    if data.startswith(b"PK\x03\x04"):
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            # pick first json file
            names = [n for n in zf.namelist() if n.lower().endswith(".json")]
            if not names:
                raise RuntimeError("zip contained no .json")
            raw = zf.read(names[0]).decode("utf-8")
            return json.loads(raw)

    # Otherwise treat as JSON.
    return json.loads(data.decode("utf-8"))


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", "utf-8")


def migrate_dns_servers(conf: Dict[str, Any]) -> None:
    servers = conf.get("dns", {}).get("servers", [])
    new: List[Dict[str, Any]] = []
    for s in servers:
        if not isinstance(s, dict):
            continue
        tag = s.get("tag")

        # already migrated
        if "type" in s and "server" in s and "address" not in s:
            ns = dict(s)
            # still enforce Android rule
            if tag == "dns_direct" and ns.get("detour") == "direct":
                ns.pop("detour", None)
            new.append(ns)
            continue

        addr = s.get("address") or ""
        if isinstance(addr, str) and "://" in addr:
            scheme, rest = addr.split("://", 1)
            if scheme == "udp":
                ns = {"type": "udp", "server": rest}
            elif scheme == "tcp":
                ns = {"type": "tcp", "server": rest}
            elif scheme in ("tls", "tcp-tls"):
                ns = {"type": "tls", "server": rest}
            elif scheme in ("https", "doh"):
                host = rest.split("/", 1)[0]
                ns = {"type": "https", "server": host}
            elif scheme in ("h3", "http3"):
                host = rest.split("/", 1)[0]
                ns = {"type": "h3", "server": host}
            elif scheme == "quic":
                ns = {"type": "quic", "server": rest}
            else:
                ns = {"type": scheme, "server": rest}
        else:
            ns = {"type": "udp", "server": addr}

        if tag:
            ns["tag"] = tag

        if "detour" in s:
            # IMPORTANT: Android rejects dns_direct detour=direct
            if not (tag == "dns_direct" and s.get("detour") == "direct"):
                ns["detour"] = s.get("detour")

        new.append(ns)

    conf.setdefault("dns", {})["servers"] = new


def rebuild_bootstrap_dns_rule(conf: Dict[str, Any]) -> None:
    # Create/replace a top rule: resolve all outbound server domains via dns_direct.
    domains = sorted({ob.get("server") for ob in conf.get("outbounds", []) if isinstance(ob, dict) and _is_domain(ob.get("server"))})
    rules = conf.get("dns", {}).get("rules") or []

    # Remove prior auto bootstrap rules (server=dns_direct with a 'domain' list)
    cleaned: List[Dict[str, Any]] = []
    for r in rules:
        if isinstance(r, dict) and r.get("server") == "dns_direct" and isinstance(r.get("domain"), list):
            continue
        cleaned.append(r)

    if domains:
        cleaned = [{"domain": domains, "server": "dns_direct"}] + cleaned

    conf.setdefault("dns", {})["rules"] = cleaned


def ensure_default_domain_resolver(conf: Dict[str, Any], tag: str = "dns_direct") -> None:
    conf.setdefault("route", {})
    conf["route"]["default_domain_resolver"] = tag


def referenced_node_tags(conf: Dict[str, Any]) -> Set[str]:
    """Method B: update only node outbounds referenced by template (concrete protocol outbounds)."""
    tags: Set[str] = set()
    for ob in conf.get("outbounds", []):
        if not isinstance(ob, dict):
            continue
        t = ob.get("type")
        if t in ("direct", "block", "dns", "selector", "urltest"):
            continue
        tag = ob.get("tag")
        if tag:
            tags.add(tag)
    return tags


def clean_selector_lists(conf: Dict[str, Any]) -> None:
    existing = {ob.get("tag") for ob in conf.get("outbounds", []) if isinstance(ob, dict) and ob.get("tag")}
    for ob in conf.get("outbounds", []):
        if isinstance(ob, dict) and isinstance(ob.get("outbounds"), list):
            ob["outbounds"] = [x for x in ob["outbounds"] if x in existing]


def strip_private_nodes_for_share(conf: Dict[str, Any], sub_by_tag: Dict[str, Dict[str, Any]]) -> None:
    """Share config should include only subscription nodes (no private servers)."""
    keep: List[Dict[str, Any]] = []
    for ob in conf.get("outbounds", []):
        if not isinstance(ob, dict):
            continue
        t = ob.get("type")
        tag = ob.get("tag")

        if t in ("direct", "block", "dns", "selector", "urltest"):
            keep.append(ob)
            continue

        # concrete node outbound: keep only if it's from subscription
        if tag and tag in sub_by_tag:
            keep.append(ob)

    conf["outbounds"] = keep
    clean_selector_lists(conf)


def update_from_subscription(
    template: Dict[str, Any],
    sub_by_tag: Dict[str, Dict[str, Any]],
    *,
    keep_private: bool,
) -> Dict[str, Any]:
    conf = json.loads(json.dumps(template))  # deep copy

    tags_to_update = referenced_node_tags(conf)

    new_outbounds: List[Dict[str, Any]] = []
    for ob in conf.get("outbounds", []):
        if not isinstance(ob, dict):
            new_outbounds.append(ob)
            continue

        tag = ob.get("tag")
        if tag and tag in tags_to_update and tag in sub_by_tag:
            repl = dict(sub_by_tag[tag])
            # preserve detour from template when subscription doesn't provide it
            if "detour" in ob and "detour" not in repl:
                repl["detour"] = ob["detour"]
            new_outbounds.append(repl)
        else:
            new_outbounds.append(ob)

    conf["outbounds"] = new_outbounds

    if not keep_private:
        strip_private_nodes_for_share(conf, sub_by_tag)

    # 1.14-ready patch set
    migrate_dns_servers(conf)
    ensure_default_domain_resolver(conf, "dns_direct")
    rebuild_bootstrap_dns_rule(conf)

    return conf


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--template-share", required=True)
    ap.add_argument("--template-air", required=True)
    ap.add_argument("--template-pro", required=True)
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--date", default=str(date.today()))
    ap.add_argument("--suffix", default="1.14-ready-v2.1")
    args = ap.parse_args()

    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    sub = fetch_subscription(args.url)
    sub_outbounds = [o for o in sub.get("outbounds", []) if isinstance(o, dict) and o.get("tag")]
    sub_by_tag: Dict[str, Dict[str, Any]] = {o["tag"]: o for o in sub_outbounds}

    t_share = load_json(Path(args.template_share))
    t_air = load_json(Path(args.template_air))
    t_pro = load_json(Path(args.template_pro))

    updated_share = update_from_subscription(t_share, sub_by_tag, keep_private=False)
    updated_air = update_from_subscription(t_air, sub_by_tag, keep_private=True)
    updated_pro = update_from_subscription(t_pro, sub_by_tag, keep_private=True)

    d = args.date
    suf = args.suffix

    p_share = outdir / f"sing-box_7.8-Air_share_{d}_{suf}.json"
    p_air = outdir / f"sing-box_5.9-Air_private_{d}_{suf}.json"
    p_pro = outdir / f"sing-box_5.9-Pro_private_{d}_{suf}.json"

    write_json(p_share, updated_share)
    write_json(p_air, updated_air)
    write_json(p_pro, updated_pro)

    # Print paths (for automation). Do NOT print node passwords.
    print(str(p_share))
    print(str(p_air))
    print(str(p_pro))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
