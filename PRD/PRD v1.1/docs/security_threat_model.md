# AgentComms MVP 威胁模型与安全清单（ACP/0.1）

> 目的：明确“我们在 MVP 解决什么安全问题、接受什么残余风险”，并给实现者（Claude Code）一份可执行的安全 checklist。

---

## 1. 资产（我们要保护什么）

### 1.1 机密性（Confidentiality）
- **消息内容（payload）**：必须端到端加密，Relay/DB 泄露不应泄露明文
- **Agent 私钥（sign_sk / enc_sk）**：仅保存在 Agent 侧，不可上传到服务端

### 1.2 完整性与真实性（Integrity / Authenticity）
- 每条消息必须可验证 **确由某个 Agent 发出**（消息签名）
- 每个 Agent 必须可验证 **确由某个 Owner 授权**（证书验签）

### 1.3 可用性（Availability）
- Relay 需要具备基本抗垃圾 / 抗 DoS 的能力（限流/配额/allowlist）
- 离线投递可用（store & forward）

### 1.4 元数据（Metadata）
- MVP 接受：Relay 可见 sender/recipient、时间、大小、频次等元数据
- 不接受：payload 明文泄露

---

## 2. 对手模型（我们假设的攻击者）

1) **外部攻击者**：没有合法证书/密钥，尝试伪造、重放、刷接口
2) **恶意 Agent**：拥有合法证书与 key，但滥用发送垃圾/探测/骚扰
3) **恶意或被攻陷的 Relay/DB 管理员**：可读写数据库、修改路由、丢包
4) **客户端被攻陷**：Agent 机器被入侵，私钥泄露

---

## 3. 威胁与缓解

### T1：伪造 Agent 身份发消息（Spoofing）
**风险**：攻击者伪造 sender，冒充某 Agent  
**缓解**：
- 消息必须 Ed25519 签名，服务端必须验证签名与 sender_agent_id 对应公钥一致
- 服务端只信 Directory 里已注册且 active 的 agent

### T2：伪造/篡改 Agent 证书（Forged Certificate）
**风险**：攻击者上传假证书，把别人的 owner 绑定到自己 key  
**缓解**：
- Register 必须验证 Owner 的 EIP-712 typed data 签名
- agent_id 若已存在，禁止绑定到不同 owner（或需要显式轮换流程）

### T3：消息篡改（Tampering）
**风险**：Relay 或中间人修改 header 或 ciphertext  
**缓解**：
- 签名覆盖 `header_bytes || ciphertext_bytes`，篡改即验签失败

### T4：重放攻击（Replay）
**风险**：攻击者重复投递历史消息，让 Agent 重复执行  
**缓解**：
- DB 约束：`(recipient_agent_id, message_id)` 唯一
- TTL：过期消息拒收 / 标记 expired 不投递
- poll 语义：at-least-once + idempotent ACK

### T5：目录投毒（Directory Poisoning）
**风险**：服务端返回错误的公钥导致发给错误对象  
**MVP 缓解**：
- 证书由 Owner 签名，可验证“这个 key 属于哪个 owner”
- **还需要 out-of-band** 确认 peer 的 owner address（如：你知道同事的 0x 地址）
- allowlist 建议绑定到 owner/agent 的确定身份

**残余风险**：如果用户不验证同事 owner 地址，可能被“同名 agent_id”诱导（工程上应避免 agent_id 冲突+做 allowlist）。

### T6：垃圾消息 / DoS（Abuse / DoS）
**风险**：恶意 Agent/外部攻击者刷 send、塞满 inbox  
**缓解（MVP 必做）**：
- allowlist：默认拒绝，只允许明确的 sender→recipient
- rate limit：按 sender、按 IP、按 recipient 做限流
- message 大小上限（header + ciphertext）
- inbox 保留期与最大积压条数

### T7：消息内容泄露（Confidentiality breach）
**风险**：DB 泄露或 Relay 内部人员读取消息  
**缓解**：
- sealed box E2EE：DB 只存 ciphertext
- 日志禁止打印 payload/ciphertext（只打 message_id、大小等）

### T8：私钥泄露（Key Compromise）
**风险**：Agent 机器被入侵，历史消息可被解密/伪造  
**缓解（MVP 能做的）**：
- key 不上云；本地加密存储（可选）
- 证书到期 + 快速吊销（revoked）
- 私钥轮换（下个版本）

**残余风险（MVP 接受）**：
- sealed box 不提供前向保密：recipient enc_sk 泄露会解密历史密文  
  后续应升级到 Double Ratchet / MLS。

---

## 4. 安全 Checklist（实现必须对照）

### 4.1 Directory
- [ ] 验证 EIP-712 签名 recovered address == owner
- [ ] agent_id 与 owner 绑定不可被第三方抢占/篡改
- [ ] expires_at_ms 必须大于当前时间（允许少量 clock skew）
- [ ] 支持 revoked 状态；revoked agent 不能发/收

### 4.2 Relay
- [ ] parse header_b64 → header JSON；字段完整性校验
- [ ] verify message signature：Ed25519 over sha256(header_bytes||ciphertext_bytes)
- [ ] enforce allowlist（默认拒绝）
- [ ] enforce TTL（过期拒收或不投递）
- [ ] enforce anti-replay（唯一索引）
- [ ] poll 返回 pending；ack 改状态并停止返回
- [ ] 日志不包含明文/密文

### 4.3 SDK/CLI
- [ ] keys 生成：sign(ed25519) 与 enc(curve25519) 分离
- [ ] sealed box encrypt/decrypt 可互通
- [ ] message signing/verification 与服务端一致
- [ ] demo 覆盖完整链路

---

## 5. 明确的 MVP 残余风险（接受并记录）
- 传输层中心化：Relay 可拒绝服务、可丢包
- 元数据暴露：sender/recipient/时间/大小可见
- 无前向保密：密钥泄露会解密历史消息
- 无经济型 anti-spam：主要靠 allowlist + rate limit

