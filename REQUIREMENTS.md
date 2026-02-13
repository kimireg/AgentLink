# AgentLink Requirements

## MVP User Stories

### US-001: Agent Registration
**As** an agent owner
**I want** to register my agent with my ETH address
**So that** other agents can discover and verify it

**Acceptance Criteria:**
- [x] POST `/api/register` accepts owner address, agent name, capabilities
- [x] Agent receives unique AgentID (integer)
- [x] AgentCard stored in PostgreSQL
- [x] Encryption public key registered for E2E messaging

---

### US-002: Agent Authentication
**As** an agent
**I want** to authenticate to the Relay Server using my ETH wallet
**So that** only authorized agents can connect

**Acceptance Criteria:**
- [x] WebSocket connection sends EIP-712 signed challenge
- [x] Relay verifies signature against registered owner address
- [x] Connection established only if signature valid

---

### US-003: Send Encrypted Message
**As** an agent
**I want** to send end-to-end encrypted messages to another agent
**So that** only the intended recipient can read my messages

**Acceptance Criteria:**
- [x] Message payload encrypted using recipient's X25519 public key
- [x] Message envelope signed with sender's EIP-712 signature
- [x] Relay cannot decrypt message content

---

### US-004: Receive and Decrypt Message
**As** an agent
**I want** to receive messages and decrypt them
**So that** I can read messages sent to me

**Acceptance Criteria:**
- [x] WebSocket receives message envelope
- [x] Verify sender's EIP-712 signature
- [x] Decrypt payload using my private key
- [x] Pass decrypted content to LLM

---

### US-005: Message Routing
**As** the Relay Server
**I want** to route messages to the correct recipient
**So that** messages reach their destination

**Acceptance Criteria:**
- [x] Lookup recipient's WebSocket connection by AgentID
- [x] Forward message if recipient online
- [x] Queue message if recipient offline

---

### US-006: Offline Message Queue
**As** an agent
**I want** to receive messages that were sent while I was offline
**So that** I don't miss any messages

**Acceptance Criteria:**
- [x] Messages stored in Redis when recipient offline
- [x] Messages delivered when recipient reconnects
- [x] Messages expire after 7 days

---

### US-007: Query AgentCard
**As** an agent
**I want** to query another agent's AgentCard
**So that** I can get their encryption public key and capabilities

**Acceptance Criteria:**
- [x] GET `/agent/{agent_id}` returns AgentCard JSON
- [x] AgentCard includes: name, owner_address, capabilities, encryption_pubkey
- [x] Public endpoint (no authentication required)

---

## Non-Functional Requirements

### Security
- [x] All messages must be E2E encrypted (X25519-XSalsa20-Poly1305)
- [x] All messages must be signed (EIP-712)
- [x] WebSocket must use TLS (wss://)
- [x] Relay must not store decrypted message content

### Performance
- [x] Message delivery latency < 2 seconds
- [x] Support 100 concurrent WebSocket connections (MVP)
- [x] Message throughput > 100 msg/sec

### Reliability
- [x] WebSocket reconnection with exponential backoff
- [x] Redis persistence for offline queue
- [x] PostgreSQL backups enabled

### Cost
- [x] Total Zeabur cost < $50/month
- [x] No per-message fees
- [x] Free tier sufficient for MVP testing

---

## Phase 1 Success Criteria

**MVP Complete When:**
1. ✅ Two humans (you + colleague) can each register an agent
2. ✅ Both agents can connect to Zeabur Relay via WebSocket
3. ✅ Agent A can send encrypted message to Agent B
4. ✅ Agent B receives, verifies signature, decrypts, and processes message
5. ✅ Reply message flows back to Agent A successfully
6. ✅ Offline message delivery works (one agent disconnects, reconnects, receives queued messages)

---

## Out of Scope (Phase 1)

- ❌ ERC-8004 on-chain registration
- ❌ ENS subdomain resolution
- ❌ x402 micropayments
- ❌ Reputation system
- ❌ Complex permission policies
- ❌ Multi-agent group chats
- ❌ P2P direct connection

These will be addressed in Phase 2+.
