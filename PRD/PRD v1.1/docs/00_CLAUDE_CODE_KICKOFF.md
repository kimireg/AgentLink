# AgentComms MVP（ACP/0.1）— Claude Code 开发启动包

> 目标：把本项目交给 **Claude Code** 进行实现。本文档用于“开工即能写代码”：明确范围、验收标准、接口契约、数据结构、安全边界、以及实现步骤。
>
> MVP 场景：**两端（你与同事）各 1 个 Agent，通过一个独立的 Relay/Directory 服务完成安全通讯**（1:1、离线投递、可验证身份、端到端加密、可控策略）。

---

## 0. 一句话定义产品

**AgentComms = 面向 Agent 的安全通信层（Protocol + Directory + Relay + SDK）**  
像 Telegram 的“消息网络”，但消息是机器可读、可验证、可治理的。

---

## 1. MVP 交付清单（必须）

### 1.1 服务端（必须）
- **Directory API**：注册/查询 Agent 证书与公钥
- **Relay API**：发送消息（store & forward）、拉取 inbox、ACK
- **安全策略**：allowlist + rate limit + anti-replay（message_id 去重 + TTL）

### 1.2 客户端（必须）
- **最小 SDK**（Node 或 Python 任选其一，但需提供可运行 Demo）：
  - 生成 Agent 密钥对（签名 + 加密）
  - 构造/解析 ACP Envelope
  - 端到端加密/解密
  - 请求签名（用于 poll/ack 等需要鉴权的接口）
- **CLI 或 Demo 脚本**：
  - A 注册
  - B 注册
  - A 发消息给 B
  - B 拉取并解密，回消息给 A
  - 双方 ACK

### 1.3 交付形态（必须）
- Docker 化（本地一条命令跑起来）
- Postgres 持久化
- 单元测试 + 集成测试（至少覆盖：证书验签、消息验签、加解密、去重、ACK 流程）

---

## 2. 范围与非目标（非常重要）

### 2.1 MVP **范围内**
- 1:1 消息
- 端到端加密（Relay 不可解密）
- Owner（ETH 地址）签发 Agent 证书（EIP-712 typed data）
- Agent 使用自身密钥签名消息与 API 请求
- 离线投递（store & forward）

### 2.2 MVP **不做**
- 群聊 / 多播 / 房间
- 前向保密（Double Ratchet / MLS）
- 去中心化传输网络（Waku/XMTP/Matrix 之类先不接）
- 链上发消息（成本与吞吐不合适）
- 复杂计费/结算（仅保留扩展位）

---

## 3. 术语与身份模型

### 3.1 身份
- **Owner**：人类拥有的 ETH 地址（`0x...`），作为身份根
- **Agent**：由 Owner 授权的“子身份”，由 `agent_id` +（签名公钥、加密公钥）表示

### 3.2 信任链（MVP 的核心）
1) Owner 用钱包签名一份 **AgentCertificate**（EIP-712）
2) Directory 保存该证书
3) 任何人都可验证：证书签名 → 证明该 Agent 属于该 Owner
4) 每条消息由 Agent 自己签名 → 可证明消息确由该 Agent 发出

> 关键原则：**Owner 不签每条消息**，避免私钥上服务器；Owner 只做一次“委托签名”。

---

## 4. 总体架构（MVP）

```
+-------------------+             +--------------------------+
|   Agent A (SDK)   |  HTTPS API  |  AgentComms Server       |
| - keys            +-----------> |  - Directory             |
| - E2EE encrypt    |             |  - Relay (store&forward) |
| - sign requests   |             |  - allowlist/rate limit  |
+-------------------+             +--------------------------+
           ^                                   |
           |                                   | Postgres
           |                                   v
+-------------------+             +--------------------------+
|   Agent B (SDK)   |  HTTPS API  |  DB: agents, messages    |
| - keys            +<----------- |                          |
| - E2EE decrypt    |             +--------------------------+
+-------------------+
```

- **Server 不可信（但可用）**：只做路由、存储、验签、策略控制；不持有解密能力
- **E2EE 在端侧**：ciphertext 存库；DB 泄露也不泄露内容

---

## 5. 加密与签名（ACP/0.1 实现型配置）

> 为了让 Claude Code 快速实现，MVP 推荐直接使用 libsodium / NaCl 体系（成熟、跨语言好实现）。

### 5.1 Agent 密钥
- **签名**：Ed25519
- **加密**：Curve25519（X25519）用于 sealed box

推荐库：
- Node：`libsodium-wrappers`（或 `tweetnacl` + 额外 sealed box 实现，但不如 libsodium 直接）
- Python：`PyNaCl`

### 5.2 Payload 加密（端到端）
- 使用 **Sealed Box**（libsodium `crypto_box_seal` / PyNaCl `SealedBox`）
- 发送方只需要接收方 `agent_enc_pk` 即可加密
- 接收方用（enc_pk, enc_sk）解密

**注意**：sealed box 不提供前向保密（recipient 私钥泄露会解密历史消息）。MVP 接受；后续可升级 Double Ratchet/MLS。

### 5.3 消息签名（不可抵赖 + 防篡改）
消息签名覆盖：`header_bytes` 与 `ciphertext_bytes`

- `header_bytes`：UTF-8 JSON bytes（原样传输）
- `ciphertext_bytes`：密文 bytes
- `hash = SHA256(header_bytes || ciphertext_bytes)`
- `signature = Ed25519.sign(hash, agent_sign_sk)`

**为什么 header 用 bytes 而不是对象 canonicalize？**  
为了避免多语言 JSON 序列化差异，直接把 header 作为 bytes 传输并签名，验证端使用同样 bytes 即可。

---

## 6. ACP Envelope（线协议结构）

> 线协议采用 JSON 外壳 + Base64 编码二进制字段；Relay 不解密。

### 6.1 Envelope JSON（服务端存储与转发）
```json
{
  "header_b64": "base64url(UTF8(JSON))",
  "ciphertext_b64": "base64(ciphertext)",
  "signature_b64": "base64(ed25519_signature)"
}
```

### 6.2 Header JSON（header_b64 解出来的内容）
```json
{
  "v": "acp/0.1",
  "message_id": "uuid",
  "sender_agent_id": "uuid",
  "recipient_agent_id": "uuid",
  "timestamp_ms": 1730000000000,
  "ttl_ms": 86400000,
  "type": "chat|task|result",
  "content_type": "application/json",
  "schema": "acp.payload.v1"
}
```

### 6.3 Payload JSON（加密前）
```json
{
  "schema": "acp.payload.v1",
  "body": {
    "text": "hello",
    "meta": {}
  }
}
```

---

## 7. Directory：Agent 证书（EIP-712）

### 7.1 证书字段（服务端存储）
```json
{
  "owner": "0xabc...",
  "agent_id": "uuid",
  "agent_sign_pk_b64": "base64(32 bytes)",
  "agent_enc_pk_b64": "base64(32 bytes)",
  "permissions_hash": "0x...",
  "issued_at_ms": 1730000000000,
  "expires_at_ms": 1732600000000,
  "nonce": 1,
  "chain_id": 1,
  "signature": "0x..." 
}
```

### 7.2 EIP-712 domain / types（固定）
- domain:
  - name: `AgentComms`
  - version: `0.1`
  - chainId: `chain_id`
  - verifyingContract: `0x0000000000000000000000000000000000000000`（固定）
- primaryType: `AgentCertificate`
- types:
  - `AgentCertificate(address owner,string agentId,bytes32 agentSignPubKey,bytes32 agentEncPubKey,bytes32 permissionsHash,uint256 issuedAt,uint256 expiresAt,uint256 nonce)`

服务端验签：用 ethers.js `verifyTypedData(domain, types, message, signature)`，得到 recovered address，与 `owner` 相等即通过。

---

## 8. API 契约

- OpenAPI 文件：`openapi.agentcomms.v0.1.yaml`（本启动包已提供）
- 重点端点：
  - `POST /v1/agents/register`
  - `GET /v1/agents/{agent_id}`
  - `POST /v1/messages/send`
  - `GET /v1/messages/poll`
  - `POST /v1/messages/ack`

鉴权策略：
- `register`：只做证书验签（可选增加 admin token / 限流）
- `poll/ack`：必须做 **Agent 请求签名**（防止别人拉取你的 inbox）
- `send`：至少校验“消息签名”；可选同时校验“请求签名”

---

## 9. 数据库（Postgres）

- Schema SQL：`db_schema.sql`（本启动包已提供）
- 最少 3 张表：
  1) `agents`：证书、owner、pk、状态
  2) `messages`：密文 envelope + 收件箱索引 + ACK 状态
  3) `allowlist`：收件人允许哪些发送者

---

## 10. 安全要求（MVP 级）

### 10.1 必须实现
- 证书验签（Owner → Agent）
- 消息验签（Agent → message）
- E2EE（sealed box）
- anti-replay：同一 `(recipient_agent_id, message_id)` 只能入库一次
- TTL：过期消息拒收或不投递
- allowlist 默认关闭（推荐），至少可配置 “只允许特定 sender → recipient”

### 10.2 可选但推荐
- 请求级签名（poll/ack 必须；send 可选）
- 服务端日志不打印密文、不打印 payload
- 速率限制（按 sender/recipient）

---

## 11. 验收标准（Definition of Done）

### 功能验收
- A/B 两个 Agent 完成：注册 → 发消息 → poll → 解密 → 回复 → ACK 的全链路
- Relay DB 中只保存密文与 header（header 不含敏感内容）
- 发送同一 message_id 两次：第二次返回 409（或 200 但不重复投递，需明确实现方式）
- allowlist 未放行：返回 403

### 安全验收
- 篡改 header_b64 或 ciphertext_b64：验签失败
- 伪造 owner 签名证书：注册失败
- 未授权 agent 调用 poll 拉取他人 inbox：鉴权失败

### 工程验收
- Docker compose 本地可跑
- 测试可跑（至少 10 个核心用例）
- README 清晰：如何生成证书、如何跑 demo

---

## 12. 实现步骤（建议顺序）

> 详细任务拆分见：`implementation_plan.md`

1) 建 repo 结构（server / sdk / cli / docs）
2) 实现 Postgres schema + migration
3) 实现 Directory：register + get
4) 实现 crypto：sealed box + message sign/verify
5) 实现 Relay：send + poll + ack
6) 加 allowlist + rate limit + TTL + 去重
7) 写 e2e demo + tests
8) Docker compose + 文档完善

---

## 13. 未来演进（不在 MVP，但要留接口）
- 传输层替换：XMTP/Waku/Matrix（协议保持 envelope/identity 兼容）
- 群组通信：MLS
- 经济防垃圾：PoW / stake / RLN / 付费消息
- 可审计：加密元数据/可验证日志（按需求）

---

## 14. 给 Claude Code 的“执行指令”（可直接复制粘贴）

> 你是 Claude Code。请按以下要求实现项目：
> 1) 严格实现本启动包里的 OpenAPI、DB schema、ACP Envelope、证书验签与消息加密签名流程
> 2) 输出可运行的 Docker compose（server + postgres）
> 3) 提供一个 demo（或 CLI）展示 A/B 互通
> 4) 保证测试覆盖核心安全逻辑（证书验签、消息验签、加解密、去重、ACK、allowlist）
> 5) 代码要可读、可维护：清晰模块划分、错误码规范、日志规范、配置集中化
> 6) 在 README 中写清楚：从零到跑通 demo 的步骤（含生成密钥、生成/签发证书、注册、发消息、收消息）

