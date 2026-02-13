# ACP/0.1 加密实现配置：Sealed Box（MVP 规范）

> 这是 **MVP 的“落地实现型规范”**（实现者以本文件为准），用于确保 Node/Python/Go 等多语言互通。
>
> 设计目标：实现最少、依赖成熟库、避免自研复杂 KDF/nonce 管理。

---

## 1. 密钥类型与长度

### 1.1 签名密钥（Ed25519）
- public key：32 bytes
- secret key：
  - libsodium 常见为 64 bytes（包含 seed + public）
  - 存储时建议保存 **seed(32 bytes)** 或完整 secret key（实现自行决定，但需可恢复 sign）

### 1.2 加密密钥（Curve25519 / X25519，用于 sealed box）
- public key：32 bytes
- secret key：32 bytes

---

## 2. 编码约定

- `header_b64`：**base64url**（URL-safe，建议不带 padding）
- `ciphertext_b64`：标准 base64（允许 padding）
- `signature_b64`：标准 base64（允许 padding）

注意：服务端与 SDK 必须严格一致。

---

## 3. Payload 加密：Sealed Box

### 3.1 算法
- libsodium: `crypto_box_seal` / `crypto_box_seal_open`
- PyNaCl: `nacl.public.SealedBox`

### 3.2 加密（发送方）
输入：
- `payload_bytes`（UTF-8 JSON bytes）
- `recipient_enc_pk`（32 bytes）

输出：
- `ciphertext_bytes`

伪代码：
```
ciphertext_bytes = crypto_box_seal(payload_bytes, recipient_enc_pk)
```

### 3.3 解密（接收方）
输入：
- `ciphertext_bytes`
- `recipient_enc_pk`（32 bytes）
- `recipient_enc_sk`（32 bytes）

输出：
- `payload_bytes`

伪代码：
```
payload_bytes = crypto_box_seal_open(ciphertext_bytes, recipient_enc_pk, recipient_enc_sk)
```

### 3.4 安全属性与限制
- ✅ Relay 不可解密
- ✅ 每条消息使用临时 ephemeral key（sealed box 内部处理）
- ❌ 不提供前向保密：recipient 私钥泄露会解密历史密文（MVP 接受）

---

## 4. 消息签名：Ed25519（覆盖 header + ciphertext）

### 4.1 签名输入
- `header_bytes`：从 `header_b64` 解码得到（发送方生成并原样传输）
- `ciphertext_bytes`：从 `ciphertext_b64` 解码得到

计算：
```
hash = SHA256(header_bytes || ciphertext_bytes)
signature = Ed25519.sign(hash, sender_sign_sk)
```

### 4.2 验签
```
hash = SHA256(header_bytes || ciphertext_bytes)
ok = Ed25519.verify(signature, hash, sender_sign_pk)
```

---

## 5. Header 生成建议（非强制，但推荐）
为便于调试与一致性，建议 header 生成时：
- JSON key 排序
- compact 序列化（无空格、无换行）

例如：
- Python: `json.dumps(obj, separators=(',', ':'), sort_keys=True)`
- Node: 使用稳定 stringify（例如自己递归排序或用 stable stringify 库）

**但注意**：验签必须使用“收到的 header_bytes”，服务端不要重新 stringify。

