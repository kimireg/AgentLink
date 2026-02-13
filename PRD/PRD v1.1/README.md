# AgentComms MVP (ACP/0.1)

本仓库实现一个最小可用的 Agent 通讯系统：
- Directory：Owner(EVM) 签发 Agent 证书（EIP-712）注册/查询
- Relay：E2EE 密文消息 store & forward（send/poll/ack）
- SDK/CLI：生成密钥、构造 envelope、跑通 A/B demo

> 详细规格见 `docs/`：`00_CLAUDE_CODE_KICKOFF.md`

---

## 1. 快速开始（本地）

```bash
cp .env.example .env
docker compose up --build
curl http://localhost:8080/v1/healthz
```

---

## 2. 跑 Demo（示例）

> 约定：demo 会生成两组 keys（A/B），用测试 owner 私钥签证书并注册，然后完成互发消息。

```bash
# 示例（根据实际实现修改路径）
node ./cli/demo.js
# 或
python ./cli/demo.py
```

---

## 3. 文档

- `docs/00_CLAUDE_CODE_KICKOFF.md`：开工说明 + 验收标准
- `docs/openapi.agentcomms.v0.1.yaml`：API 契约
- `docs/db_schema.sql`：数据库结构
- `docs/security_threat_model.md`：威胁模型与 checklist
- `docs/implementation_plan.md`：实现计划

