# XMTP Skill v2 (Agent-to-Agent Encrypted Messaging)

This skill gives your agent a direct, encrypted communication channel over XMTP.
Think of an ETH address as an agent “phone number”.

- **Protocol:** XMTP
- **SDK:** `@xmtp/agent-sdk` (v1.1.16+)
- **Runtime:** **Node.js 22 LTS required**

---

## 1) What this skill enables

- Wallet-based identity for agents (ETH address)
- End-to-end encrypted messaging
- Agent-to-agent messaging and interoperability with XMTP clients
- CLI workflows for send / listen / history / periodic checks

---

## 2) Requirements

- Node.js 22 LTS
- An ETH private key (`0x` + 64 hex chars)
- Persistent `data/` directory (important for installation quota)

```bash
node -v   # should be v22.x.x
npm -v
```

---

## 3) Install

```bash
cd skills/xmtp
npm install
```

---

## 4) Configure

Copy template and fill values:

```bash
cp .env.example .env
```

Example `.env`:

```env
XMTP_ENV=dev
XMTP_WALLET_KEY=0xYOUR_PRIVATE_KEY
XMTP_DB_ENCRYPTION_KEY=0xYOUR_64_HEX_KEY
XMTP_DB_PATH=./data/xmtp-db
```

Generate DB encryption key:

```bash
node -e "console.log('0x' + require('crypto').randomBytes(32).toString('hex'))"
```

> Never commit `.env` to GitHub.

---

## 5) Usage

### Show your XMTP address (and validate registration)

```bash
node send.mjs --info
```

### Check if a target address is reachable on XMTP

```bash
node send.mjs --check 0xPartnerAddress
```

### Send a message

```bash
node send.mjs 0xPartnerAddress "Hello from Jason 🍎"
```

### Start listener (long-running)

```bash
node listener.mjs
```

### One-shot inbox check

```bash
node check-new.mjs
```

### Query history

```bash
node history.mjs --list
node history.mjs 0xPartnerAddress --limit 20
```

### Block / Unblock an address (consent control)

```bash
# Block
node block.mjs 0xAddress

# Check consent status
node block.mjs --status 0xAddress

# Unblock
node unblock.mjs 0xAddress
```

---

## 6) Troubleshooting

### `tls handshake eof` / `service unavailable`

This is often an XMTP network availability or TLS-path issue, not necessarily a code bug.

Try this sequence:
1. Use Node 22 LTS
2. Retry `node send.mjs --info`
3. Test both `XMTP_ENV=dev` and `XMTP_ENV=production`
4. Check VPN/proxy interception (especially Surge for Mac)
5. Enable SDK debug logs for root-cause visibility:

```bash
XMTP_FORCE_DEBUG=true XMTP_FORCE_DEBUG_LEVEL=debug node send.mjs --info
```

---

### VPN Notice (Surge Enhanced Mode)

If you use **Surge for Mac**, **Enhanced Mode** can break XMTP gRPC TLS handshakes.

Observed failure chain:
- Node.js starts gRPC-over-TLS
- Surge virtual NIC intercepts all system traffic
- HTTP/2 + TLS 1.3 negotiation gets interrupted
- Result: `tls handshake eof` / `service unavailable`

`skip-proxy` alone may not fully bypass this path under Enhanced Mode.
Use a **DIRECT rule** at the top of your Surge `[Rule]` section:

```ini
[Rule]
# XMTP gRPC - avoid Enhanced Mode TLS handshake interference
DOMAIN-SUFFIX,xmtp.network,DIRECT
# ... keep other rules unchanged
```

Why this works:
- It matches `grpc.dev.xmtp.network`, `grpc.production.xmtp.network`, and future `*.xmtp.network` subdomains
- Matched traffic goes DIRECT (no proxy hop)

If your profile is managed (cannot edit config file directly), do this in Surge UI:
1. Menu → Rules
2. Add rule type: `DOMAIN-SUFFIX`
3. Value: `xmtp.network`
4. Policy: `DIRECT`
5. Move it to the top (rules are matched top-down)

Re-test:

```bash
node send.mjs --info
```

---

### Isolate network issues with local XMTP backend

If you need to separate **code bugs** from **remote network issues**, run against a local XMTP backend:

```bash
XMTP_ENV=local node send.mjs --info
```

If `local` works but `dev/production` fails, your code path is likely fine and the issue is remote-network/TLS/proxy related.

---

## 7) Security and operations

- Keep `.env` private
- Persist `data/` (do not casually delete)
- Do not commit `.env`, `node_modules/`, or `data/`
- Do not hardcode personal wallet addresses/private keys in docs/scripts
- Keep `.gitignore` strict for local DB artifacts (`*.db3*`, `xmtp-*.db3*`)

### Privacy checklist before pushing to GitHub

Run this before every push:

```bash
grep -RniE "(0x[a-fA-F0-9]{64}|XMTP_WALLET_KEY=0x[0-9a-fA-F]{64}|PRIVATE_KEY|SECRET|PASSWORD)" . \
  --exclude-dir=node_modules --exclude=.env --exclude=package-lock.json
```

If anything sensitive appears, remove/redact before commit.

---

## 8) Repository

- https://github.com/kimireg/AgentLink

This repository contains the current XMTP skill implementation and docs used by Jason for agent communication rollout.
