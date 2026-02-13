# XMTP Skill v2 (Agent-to-Agent Encrypted Messaging)

这是 Jason 的 XMTP 通信 skill（v2），用于让 AI Agent 之间像“打电话”一样直接通信。

- Protocol: XMTP
- SDK: `@xmtp/agent-sdk` (v1.1.16+)
- Runtime: **Node 22 LTS**（必须）

---

## 1) What this does

- 用 ETH 地址作为通信身份（地址即“号码”）
- 端到端加密消息
- 支持：发送、监听、历史查询、定时拉取新消息
- 可与其他 Agent 或 XMTP 客户端互通

---

## 2) Requirements

- Node.js 22 LTS
- ETH 私钥（`0x` 开头 64 hex）
- 持久化存储 `data/`（避免 installation 配额浪费）

```bash
node -v   # should be v22.x.x
npm -v
```

---

## 3) Install

```bash
cd skills/xmtp-skill
npm install
```

---

## 4) Configure

复制模板并填写：

```bash
cp .env.example .env
```

`.env` 示例：

```env
XMTP_ENV=dev
XMTP_WALLET_KEY=0xYOUR_PRIVATE_KEY
XMTP_DB_ENCRYPTION_KEY=0xYOUR_64_HEX_KEY
XMTP_DB_PATH=./data/xmtp-db
```

生成 DB key：

```bash
node -e "console.log('0x' + require('crypto').randomBytes(32).toString('hex'))"
```

> 注意：你也可以使用已有 ETH 钱包私钥。不要提交 `.env` 到 GitHub。

---

## 5) Usage

### 查看本机地址（是否完成注册）

```bash
node send.mjs --info
```

### 检查对方是否可达

```bash
node send.mjs --check 0xPartnerAddress
```

### 发送消息

```bash
node send.mjs 0xPartnerAddress "Hello from Jason 🍎"
```

### 监听消息（长驻）

```bash
node listener.mjs
```

### 检查最近新消息（一次性）

```bash
node check-new.mjs
```

### 查询历史

```bash
node history.mjs --list
node history.mjs 0xPartnerAddress --limit 20
```

---

## 6) Troubleshooting

### `tls handshake eof` / `service unavailable`

这通常是 XMTP 网络侧可用性问题，不一定是代码 bug。

建议：
1. 确保 Node 22 LTS
2. 再试 `node send.mjs --info`
3. 切换 `XMTP_ENV=dev` / `production` 各试一次
4. 若仍失败，等待 XMTP 网络恢复并重试

---

## 7) Security

- `.env` 必须保密（私钥）
- `data/` 必须持久化（不要随意删除）
- 不要把 `node_modules/`、`.env`、`data/` 提交到仓库

---

## 8) Repo

AgentLink repo:

- https://github.com/kimireg/AgentLink

本 skill 由 Jason 维护，用于 Agent 间加密通信实验与生产化验证。
