# AgentComms MVP Tech Spec（ACP/0.1）

> ACP = Agent Communication Protocol。  
> 设计目标：最小可用、安全边界清晰、可演进到 MLS/Waku/XMTP/Matrix 等更强方案。

---

## 1. 总体架构

### 1.1 组件
1. **Agent SDK**
   - 生成/管理 Agent 密钥（签名+加密）
   - 校验对端证书
   - 端到端加密/解密
   - 重试、去重、ACK
2. **Directory Service（目录）**
   - 存储 Agent 证书与公钥、端点
   - 提供查询接口
3. **Relay Service（中继）**
   - 接收密文消息
   - 校验签名/策略（allowlist、速率、TTL）
   - 存储并转发（store & forward）
4. **Admin/CLI（可选）**
   - 生成证书请求、上传注册、配置 allowlist
   - 健康检查/诊断

> MVP 可以把 Directory + Relay 合并成一个服务进程。

---

## 2. 身份模型

### 2.1 Owner（人类）身份
- `owner_address`: EVM 地址（20 bytes，0x...）
- 可选：`ens_name`（仅用于展示/发现，不参与安全决策）

### 2.2 Agent 身份
- `agent_id`: UUIDv4（字符串）
- `agent_sign_pk`: Ed25519 公钥（32 bytes）
- `agent_enc_pk`: X25519 公钥（32 bytes）
- `owner_signature`: Owner 钱包对“Agent 证书”的 EIP-712 签名

> 说明：不要求 Agent 持有 Owner 私钥。Owner 只在“签发证书”时签一次，后续消息由 Agent 自己签名。

---

## 3. 密钥与证书

### 3.1 Agent 证书（Owner 签发）
**目的**：把 `agent_id + agent_sign_pk + agent_enc_pk + 权限/有效期` 绑定到 `owner_address`。

#### EIP-712 Typed Data（示例）
Domain（建议）：
- name: `AgentComms`
- version: `1`
- chainId: 1（或你的主链/业务链）
- salt: `keccak256("agentcomms:"+relay_domain)`（可选，用于域隔离）

Types：
- `AgentCertificate`:
  - owner: address
  - agentId: string
  - signingPubKey: bytes32
  - encryptionPubKey: bytes32
  - permissionsHash: bytes32
  - issuedAt: uint64
  - expiresAt: uint64
  - nonce: uint64

Value：
- permissionsHash = keccak256(canonical_json(permissions))

证书结构（JSON）：
```json
{
  "owner": "0xabc...",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "signing_pubkey": "base64(ed25519_pk_32)",
  "encryption_pubkey": "base64(x25519_pk_32)",
  "permissions": {"scopes":["chat"],"max_qps":5},
  "issued_at": 1730000000,
  "expires_at": 1732592000,
  "nonce": 1,
  "owner_sig_eip712": "0x..."
}
```

### 3.2 吊销与轮换（MVP 简化）
- 证书短有效期（例如 7 天）
- Directory 支持 `status=active|revoked`
- 吊销由 Owner 再签一个 `Revoke` 消息（可选，MVP 也可用服务端管理员吊销）

---

## 4. 加密与签名（消息级）

### 4.1 目标
- Relay 看不到明文
- 接收方可验证：消息确实来自某个 Owner 绑定的 Agent
- 抗重放：消息 ID + 时间窗 + nonce/sequence

### 4.2 推荐算法（MVP）
- 密钥交换：X25519（静态-静态 DH，用于 MVP）
- 对称加密：XChaCha20-Poly1305（AEAD）
- 哈希：SHA-256 或 BLAKE3（实现任选一致即可）
- 消息签名：Ed25519（用 agent_sign_sk）

> 后续升级：引入 Double Ratchet 或 MLS（群组/更强前向保密）。

### 4.3 会话密钥派生
- shared_secret = X25519(sender_enc_sk, recipient_enc_pk)
- session_key = HKDF(shared_secret, salt=conversation_id, info="acp/0.1")

### 4.4 消息 Envelope
Envelope（明文头 + 密文体）：
```json
{
  "version": "acp/0.1",
  "header": {
    "message_id": "uuid",
    "conversation_id": "uuid",
    "sender_owner": "0x...",
    "sender_agent_id": "uuid",
    "recipient_owner": "0x...",
    "recipient_agent_id": "uuid",
    "timestamp": 1730000001,
    "ttl_sec": 86400,
    "sequence": 42
  },
  "nonce": "base64(24 bytes)",
  "ciphertext": "base64(...)",
  "sig": "base64(ed25519_sig)",
  "sender_certificate": { ... }
}
```

Payload（被加密的内容）：
```json
{
  "content_type": "application/json",
  "content": {
    "type": "chat",
    "text": "ping",
    "meta": {"trace_id":"..."}
  }
}
```

### 4.5 签名覆盖范围
- aad = canonical_json(header)   （作为 AEAD 的 associated data）
- plaintext = canonical_json(payload)
- ciphertext = AEAD_Encrypt(session_key, nonce, plaintext, aad)
- digest = SHA256( "acp/0.1" || SHA256(aad) || SHA256(ciphertext) || nonce )
- sig = Ed25519_Sign(agent_sign_sk, digest)

### 4.6 接收方验证流程
1. 拉取 envelope
2. 校验 `timestamp` 在允许时间窗内，`ttl_sec` 未过期
3. 解析并验证 `sender_certificate.owner_sig_eip712`
4. 用证书内的 `signing_pubkey` 验证 `sig`
5. 计算 shared_secret/session_key，解密 ciphertext
6. payload 解析，交给上层 Agent 处理
7. 发送 ACK（幂等）

---

## 5. Relay / Directory API（HTTP）

> 所有 API 必须走 TLS（HTTPS）。  
> 认证方式（MVP）：请求带 `X-Agent-Id` + `X-Req-Ts` + `X-Req-Nonce` + `X-Req-Sig`，由 agent_sign_sk 签名；服务端用目录中的 agent_sign_pk 验证。

### 5.1 注册 Agent
`POST /v1/agents/register`
Body：`sender_certificate`
- 服务端验证 owner_sig
- 存储 agent 记录

### 5.2 查询 Agent
`GET /v1/agents/{agent_id}`
Response：证书、公钥、状态

### 5.3 发送消息
`POST /v1/messages/send`
Body：`envelope`
- 服务端校验：sender_certificate、sig、allowlist、rate limit
- 存入收件人 inbox（按 recipient_agent_id 分区）

### 5.4 拉取消息
`GET /v1/messages/poll?agent_id=...&cursor=...&limit=...`
Response：
```json
{
  "cursor": "opaque",
  "messages": [ envelope, ... ]
}
```

### 5.5 ACK
`POST /v1/messages/ack`
Body：
```json
{
  "agent_id":"...",
  "message_id":"...",
  "status":"processed"
}
```

---

## 6. 数据模型（建议）

### agents
- agent_id (pk)
- owner_address
- signing_pubkey
- encryption_pubkey
- certificate_json
- status
- created_at, updated_at, expires_at

### allowlists
- owner_address
- allowed_owner_address (or allowed_agent_id)
- created_at

### messages
- message_id (pk)
- conversation_id
- sender_agent_id
- recipient_agent_id
- header_json
- nonce_b64
- ciphertext_b64
- sig_b64
- received_at
- expires_at
- state: queued|delivered|acked

### acks
- message_id
- agent_id
- acked_at

---

## 7. 安全策略（MVP）

- 只接受 allowlist 内的对端（最简单有效）
- Rate limit：按 owner_address / agent_id 维度限速
- Anti-replay：message_id 去重 + timestamp 窗口
- 证书短有效期 + 可吊销
- 日志只记录元数据，不落明文

---

## 8. 参考实现建议（给 Agent 开发者）

### 8.1 SDK 最小接口
- `register_agent(owner_sig_cert)`
- `send(to_agent_id, payload)`
- `poll() -> [payload]`
- `ack(message_id)`
- `verify_and_decrypt(envelope)`

### 8.2 本地开发
- docker-compose：relay+postgres
- CLI：生成 agent keys、请求 owner 签名、注册、发测试消息

### 8.3 端到端测试用例
1. A、B 注册
2. A → B 发 100 条消息，B 全部 ACK
3. 人为复制同一 envelope 再发一次：服务端/客户端应去重
4. 修改 ciphertext 或 header：应验签失败
5. 证书过期：应拒绝

---

## 9. 演进路线（从 ACP/0.1 到更强）

- ACP/0.2：引入 Double Ratchet（前向保密）
- ACP/0.3：支持群组（MLS / Sender Keys）
- ACP/1.0：支持联邦化/去中心化路由（例如接入 Waku 或 XMTP）
