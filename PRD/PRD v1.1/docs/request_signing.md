# AgentComms 请求签名（HTTP API Auth）规范（MVP）

> 目的：防止他人调用 poll/ack 拉取或确认你的 inbox。  
> 注意：`send` 端点可以只依赖“消息签名”；但 `poll/ack` 必须开启“请求签名”。

---

## 1. 参与字段（Headers）

客户端发送：
- `X-Agent-Id`: 发送请求的 agent_id（UUID）
- `X-Timestamp`: unix epoch ms（int64）
- `X-Body-Sha256`: hex(SHA256(raw_body_bytes))
  - GET 请求 body 为空 → hash 空字符串即可
- `X-Req-Signature`: base64(Ed25519 signature)

---

## 2. canonical_request_string（必须严格一致）

```
METHOD\n
PATH\n
TIMESTAMP_MS\n
BODY_SHA256_HEX
```

示例：
```
GET
/v1/messages/poll
1730000000123
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

---

## 3. 签名计算

```
req_hash = SHA256(utf8(canonical_request_string))
X-Req-Signature = base64(Ed25519.sign(req_hash, agent_sign_sk))
```

---

## 4. 服务端验证

1) 读取 `X-Agent-Id` 查 agent_sign_pk（必须 active）
2) 校验 `abs(now_ms - X-Timestamp) <= CLOCK_SKEW_MS`（建议 5 分钟）
3) 计算 `X-Body-Sha256` 是否匹配真实 body bytes
4) 重建 canonical_request_string → req_hash
5) Ed25519.verify(signature, req_hash, agent_sign_pk)

通过才允许访问。

---

## 5. 重放风险与 MVP 处理

MVP 默认不引入 nonce 缓存（减少状态），依赖：
- 时间窗口（CLOCK_SKEW_MS）
- rate limit
- poll/ack 的幂等语义（ack 重复是安全的）

后续可升级：
- `X-Nonce` + Redis 去重缓存
- 更强的 session token / short-lived bearer

