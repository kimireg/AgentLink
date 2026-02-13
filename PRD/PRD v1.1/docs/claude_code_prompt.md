# Claude Code Prompt（直接粘贴用）

你是 Claude Code，请实现一个最小可用的 Agent 通讯系统（AgentComms，ACP/0.1）。

## 必须交付
1. Server（Directory + Relay）：
   - POST /v1/agents/register（验证 Owner 的 EIP-712 证书签名并入库）
   - GET  /v1/agents/{agent_id}
   - POST /v1/messages/send（验证消息签名、allowlist、TTL、去重并入库）
   - GET  /v1/messages/poll（必须请求签名鉴权，拉取 inbox pending）
   - POST /v1/messages/ack（必须请求签名鉴权，幂等 ACK）
   - GET  /v1/healthz

2. Postgres schema：严格按 docs/db_schema.sql
3. OpenAPI：严格按 docs/openapi.agentcomms.v0.1.yaml
4. Crypto：
   - E2EE：Sealed Box（libsodium）
   - 消息签名：Ed25519 over SHA256(header_bytes || ciphertext_bytes)
   - 证书验签：ethers verifyTypedData（EIP-712，domain/types 固定）
5. Docker compose：server + postgres，一条命令可跑
6. Demo/CLI：生成 A/B keys → 签证书 → register → 发消息 → poll 解密 → 回复 → ack
7. Tests：覆盖证书验签、消息验签、加解密、去重、ACK、allowlist

## 关键文档（你必须遵守）
- docs/00_CLAUDE_CODE_KICKOFF.md
- docs/crypto_profile_sealedbox.md
- docs/request_signing.md
- docs/security_threat_model.md
- docs/openapi.agentcomms.v0.1.yaml

## 工程要求
- TypeScript（推荐）或 Python（可接受），结构清晰、可维护
- 错误码规范：400/401/403/404/409/429/500
- 日志不要打印 payload/ciphertext
- 配置集中化（.env），提供 .env.example
