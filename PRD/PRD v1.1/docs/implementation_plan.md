# AgentComms MVP 实现计划（给 Claude Code）

> 目标：让实现者不需要再“设计”，直接按步骤实现并通过验收。

---

## 0) 推荐技术栈（可替换，但需等价）
- Server：Node.js 20 + TypeScript + Fastify（或 NestJS）
- DB：Postgres 15+
- Crypto：
  - Ed25519 + sealed box（libsodium / PyNaCl）
  - EIP-712 验签：ethers.js
- Tests：vitest/jest（server）+ 一个 e2e 测试脚本
- 交付：Dockerfile + docker-compose

---

## 1) Repo 结构（建议）
```
agentcomms/
  docs/                         # 本启动包文档
  server/                       # Directory + Relay
  sdk/                          # 最小 SDK（node 或 python）
  cli/                          # demo/命令行（可选）
  docker-compose.yml
  README.md
```

---

## 2) 里程碑与任务拆分（按顺序做）

### M1：跑起来（骨架）
- [ ] 初始化 monorepo（或单 repo 多目录）
- [ ] server：健康检查 `/v1/healthz`
- [ ] docker-compose：server + postgres
- [ ] db：运行 `db_schema.sql`（migration 或启动时执行）
- [ ] README：本地启动步骤

验收：
- `docker compose up` 后 healthz 返回 200

---

### M2：Directory（注册 + 查询）
- [ ] 实现 `POST /v1/agents/register`
  - [ ] 校验请求 schema
  - [ ] EIP-712 验签 recovered == owner
  - [ ] upsert agents 记录（agent_id 为主键）
  - [ ] 冲突规则：若 agent_id 已存在但 owner 不同 → 409
- [ ] 实现 `GET /v1/agents/{agent_id}`
- [ ] 增加最小 rate limit（防止 register 被刷）

验收：
- 提交合法证书可注册；错误签名拒绝；可查询到 pk 与 expiry

---

### M3：Crypto 模块（可单独测试）
- [ ] SDK（或 server 内 util）实现：
  - [ ] generate_agent_keys(): sign(ed25519) + enc(curve25519)
  - [ ] sealed_box_encrypt(payload_json, recipient_enc_pk)
  - [ ] sealed_box_decrypt(ciphertext, recipient_enc_sk/pk)
  - [ ] sign_message(header_bytes, ciphertext_bytes, sign_sk)
  - [ ] verify_message_signature(...)
- [ ] 写 3~5 个单元测试：
  - [ ] encrypt->decrypt 一致
  - [ ] 篡改 header/ciphertext 触发验签失败
  - [ ] 不同 recipient key 无法解密

验收：
- crypto tests 通过

---

### M4：Relay（send/poll/ack）核心闭环
- [ ] `POST /v1/messages/send`
  - [ ] 解 header_b64 → header JSON
  - [ ] 基础字段校验：v/message_id/sender/recipient/timestamp/ttl
  - [ ] sender/recipient agent 是否存在且 active
  - [ ] verify message signature（查 sender sign_pk）
  - [ ] allowlist：recipient 是否允许 sender（默认 deny）
  - [ ] TTL：计算 expires_at；过期拒绝或标记 expired
  - [ ] 去重：依赖 DB unique index；冲突时返回 409
  - [ ] 入库 messages（pending）
- [ ] `GET /v1/messages/poll`
  - [ ] 鉴权：请求签名必须正确（见“请求签名”附录）
  - [ ] 仅允许 agent 拉取自己的 inbox
  - [ ] 按 cursor/limit 拉取 pending
  - [ ] 返回 next_cursor
- [ ] `POST /v1/messages/ack`
  - [ ] 鉴权：请求签名必须正确
  - [ ] 仅允许 recipient ack 自己的 message
  - [ ] 幂等：重复 ack 返回 ok
  - [ ] 更新 status=acked, acked_at

验收：
- A send -> B poll -> B ack 成功；ack 后不再返回

---

### M5：请求级签名（API auth）
- [ ] 定义 canonical_request_string：
  - `METHOD\nPATH\nTIMESTAMP_MS\nBODY_SHA256_HEX`
- [ ] 客户端用 agent_sign_sk 对 `SHA256(canonical_request_string)` 做 Ed25519 签名
- [ ] 服务器 verify：
  - X-Agent-Id 对应的 sign_pk
  - 时间窗口（例如 ±5 分钟）
  - 可选：nonce/重放缓存（MVP 可先不做，依赖时间窗口+限流）

验收：
- 未签名/签错无法 poll/ack

---

### M6：E2E Demo（必须）
- [ ] 提供一个脚本（node/python）演示：
  - 生成 A/B keys
  - 用测试 owner 私钥签发 A/B 证书（或输出 typed data 让人签）
  - register A/B
  - A→B 发消息（payload 加密），B poll 解密并回复
  - 双方 ack
- [ ] Demo 输出需包含 message_id、解密后的 payload 内容

验收：
- 一键跑 demo，看到明文在端侧输出，服务端只存密文

---

### M7：硬化（MVP 的安全底线）
- [ ] message 大小上限（例如 64KB）
- [ ] per-agent rate limit（例如 send/poll/ack）
- [ ] inbox 最大积压（例如每 recipient 1 万条，超出拒收）
- [ ] 日志脱敏：不打印 header_b64（可打印解析后的关键字段）

验收：
- 压测/恶意输入不会导致崩溃或数据库无限增长

---

## 3) 附录：allowlist 策略（MVP 建议）
- 默认：**deny all**
- 只允许预配置的 sender→recipient：
  - env：`ALLOWLIST_PAIRS="senderUUID1:recipientUUID1,senderUUID2:recipientUUID2"`
- 或用 DB allowlist 表（推荐）：注册后插入两条记录即放行

---

## 4) 附录：错误码规范（建议）
- 400：schema/字段错误
- 401：鉴权失败（请求签名）
- 403：allowlist 不允许
- 404：agent/message 不存在
- 409：去重冲突（message_id 重放、agent_id 冲突）
- 429：限流
- 500：内部错误（不泄露敏感细节）

