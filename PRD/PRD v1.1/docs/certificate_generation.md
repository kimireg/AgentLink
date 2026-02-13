# AgentCertificate 生成与签名示例（EIP-712 / ethers）

> 目的：让实现者能快速跑通 register 流程。  
> MVP demo 允许使用测试私钥（`OWNER_PRIVATE_KEY`）在脚本里签名；真实环境可用钱包 UI 来签。

---

## 1) 固定 Domain 与 Types

### Domain
```json
{
  "name": "AgentComms",
  "version": "0.1",
  "chainId": 1,
  "verifyingContract": "0x0000000000000000000000000000000000000000"
}
```

### Types
```js
const types = {
  AgentCertificate: [
    { name: "owner", type: "address" },
    { name: "agentId", type: "string" },
    { name: "agentSignPubKey", type: "bytes32" },
    { name: "agentEncPubKey", type: "bytes32" },
    { name: "permissionsHash", type: "bytes32" },
    { name: "issuedAt", type: "uint256" },
    { name: "expiresAt", type: "uint256" },
    { name: "nonce", type: "uint256" }
  ]
};
```

---

## 2) message 字段说明

- `owner`：owner ETH address
- `agentId`：UUID 字符串
- `agentSignPubKey`：32 bytes（Ed25519 public key）→ hex `0x...`
- `agentEncPubKey`：32 bytes（Curve25519 public key）→ hex `0x...`
- `permissionsHash`：32 bytes → hex `0x...`
  - MVP 可先固定为 `keccak256("[]")` 或 `0x00..00`
- `issuedAt / expiresAt / nonce`：uint256（建议用毫秒或秒统一，**服务端与客户端必须一致**）
  - 推荐：都用 ms（epoch milliseconds）

---

## 3) ethers v6 签名示例（Node/TS）

```ts
import { Wallet, keccak256, toUtf8Bytes, verifyTypedData } from "ethers";

const domain = {
  name: "AgentComms",
  version: "0.1",
  chainId: 1,
  verifyingContract: "0x0000000000000000000000000000000000000000",
};

const types = {
  AgentCertificate: [
    { name: "owner", type: "address" },
    { name: "agentId", type: "string" },
    { name: "agentSignPubKey", type: "bytes32" },
    { name: "agentEncPubKey", type: "bytes32" },
    { name: "permissionsHash", type: "bytes32" },
    { name: "issuedAt", type: "uint256" },
    { name: "expiresAt", type: "uint256" },
    { name: "nonce", type: "uint256" },
  ],
};

// 32-byte hex helpers
function toBytes32Hex(b: Uint8Array): string {
  if (b.length !== 32) throw new Error("expected 32 bytes");
  return "0x" + Buffer.from(b).toString("hex");
}

const ownerWallet = new Wallet(process.env.OWNER_PRIVATE_KEY!);
const owner = await ownerWallet.getAddress();

const permissionsHash = keccak256(toUtf8Bytes("[]")); // MVP 固定值

const message = {
  owner,
  agentId: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  agentSignPubKey: toBytes32Hex(agentSignPkBytes),
  agentEncPubKey: toBytes32Hex(agentEncPkBytes),
  permissionsHash,
  issuedAt: BigInt(Date.now()),
  expiresAt: BigInt(Date.now() + 7 * 24 * 3600 * 1000),
  nonce: 1n,
};

const signature = await ownerWallet.signTypedData(domain, types, message);

// 本地验证（服务端也应如此验证）
const recovered = verifyTypedData(domain, types, message, signature);
console.log({ owner, recovered, signature });
```

---

## 4) 服务端如何验证
服务端收到 register 请求体里的 certificate 字段后：
1. 将 base64 公钥 decode 成 32 bytes
2. 转换成 bytes32 hex（`0x...`）
3. 组装 message（字段必须一致）
4. `verifyTypedData(domain, types, message, signature)` 得到 recovered
5. recovered == owner → 通过

---

## 5) 注意点（常见坑）
- bytes32：必须严格 32 bytes
- 时间单位：ms vs s 必须一致
- address：大小写不影响 recovered，但建议服务端统一存储为 lowercase
- signature：`0x` 前缀必须保留

