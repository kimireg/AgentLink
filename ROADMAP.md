# AgentLink - Implementation Roadmap

## Phase 1: Relay Server Foundation (Week 1-2)

**Goal**: Deployable Relay Server on Zeabur with Agent registration and WebSocket connections.

### Week 1: Core Server Setup

- [x] Create project structure and README
- [x] Define requirements (REQUIREMENTS.md)
- [ ] Set up FastAPI project structure
- [ ] Configure PostgreSQL models (Agent, AgentCard)
- [ ] Implement Agent registration API (`POST /api/register`)
- [ ] Implement AgentCard query API (`GET /agent/{agent_id}`)
- [ ] Write unit tests for registration

### Week 2: WebSocket & Authentication

- [ ] Implement WebSocket endpoint with connection manager
- [ ] Implement EIP-712 challenge-response authentication
- [ ] Implement message routing (online agents)
- [ ] Set up Redis for connection state
- [ ] Deploy to Zeabur and test

**Phase 1 Deliverables:**
- ✅ Relay Server running on Zeabur
- ✅ Agent registration working
- ✅ WebSocket connections established
- ✅ Authentication via EIP-712

---

## Phase 2: Local Agent SDK (Week 3-4)

**Goal**: Python SDK that can connect to Relay, sign messages, and encrypt/decrypt.

### Week 3: Crypto & Connection

- [ ] Implement EIP-712 signing utilities
- [ ] Implement X25519 E2E encryption/decryption
- [ ] Implement WebSocket client with auto-reconnect
- [ ] Implement AgentNode class (main entry point)
- [ ] Write crypto unit tests

### Week 4: LLM Integration & Messaging

- [ ] Implement Claude LLM client
- [ ] Implement message sending/receiving flow
- [ ] Implement signature verification
- [ ] Create example scripts (register, connect, send)
- [ ] Test end-to-end locally

**Phase 2 Deliverables:**
- ✅ Local Agent SDK (`pip install -e .`)
- ✅ Can register Agent via SDK
- ✅ Can connect to Relay
- ✅ Can send/receive encrypted messages

---

## Phase 3: End-to-End Messaging (Week 5)

**Goal**: Two local Agents can securely message each other.

### Week 5: Integration & Testing

- [ ] Implement offline message queue (Redis)
- [ ] Implement message routing for offline agents
- [ ] Create two-agent demo script
- [ ] Test with two humans (you + colleague)
- [ ] Debug and fix issues
- [ ] Document usage

**Phase 3 Deliverables:**
- ✅ Two Agents can message each other
- ✅ E2E encryption verified
- ✅ Signature verification working
- ✅ Offline queue functional

---

## Phase 4: Polish & Extensions (Week 6+)

**Goal**: Polish MVP and prepare for Phase 2.

### Week 6: Polish

- [ ] Add CLI tools (`agentlink register`, `agentlink connect`)
- [ ] Add logging and error handling
- [ ] Add health check endpoints
- [ ] Add monitoring (basic metrics)
- [ ] Write comprehensive documentation

### Future Extensions (Phase 2)

- [ ] ERC-8004 on-chain registration
- [ ] x402 payment integration
- [ ] Reputation system
- [ ] Web Dashboard (Owner UI)
- [ ] PyPI package release

---

## Dependencies

### External Services

- **Zeabur**: Hosting Relay Server
  - PostgreSQL database
  - Redis cache/queue
  - Compute instance

- **Ethereum**: For signing (local wallet only, no on-chain ops in Phase 1)
  - Local wallet (MetaMask/Coinbase Wallet)
  - Optional: Sepolia testnet for future on-chain features

- **Claude API**: For LLM (optional, can use local LLM)
  - Anthropic API key

### Python Packages

**Relay Server:**
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
redis==5.0.1
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
websockets==12.0
eth-account==0.10.0
```

**Local Agent:**
```txt
web3==6.16.0
eth-account==0.10.0
pynacl==1.5.0
anthropic==0.27.0
websockets==12.0
```

---

## Testing Strategy

### Unit Tests

- [ ] Crypto: EIP-712 signing/verification
- [ ] Crypto: X25519 encryption/decryption
- [ ] Models: Agent registration/validation
- [ ] WebSocket: Connection lifecycle

### Integration Tests

- [ ] Agent registration → AgentCard query
- [ ] WebSocket connect → authenticate → disconnect
- [ ] Send message → receive message (same process)
- [ ] Offline queue → reconnect → deliver

### End-to-End Tests

- [ ] Two separate processes (Agent A + Agent B)
- [ ] Full message flow: encrypt → send → route → receive → decrypt
- [ ] Offline scenario: send while offline → reconnect → receive
- [ ] Signature tampering: should reject invalid signatures

---

## Success Metrics (Phase 1)

| Metric | Target | Status |
|--------|--------|--------|
| Agent registration | < 5 seconds | ⏳ |
| WebSocket connection | < 2 seconds | ⏳ |
| Message delivery (online) | < 2 seconds | ⏳ |
| Message delivery (offline) | < 5 seconds after reconnect | ⏳ |
| E2E encryption | 100% of messages | ⏳ |
| Signature verification | 100% of messages | ⏳ |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Zeabur WebSocket limits | Test early, consider upgrade if needed |
| Redis memory limits | Set TTL on messages, monitor usage |
| EIP-712 signature complexity | Use well-tested libraries (eth-account) |
| X25519 key management | Store keys securely, support rotation |
| LLM rate limits | Implement retry logic, graceful degradation |

---

## Notes

- **Start simple**: Focus on "two agents messaging" before adding features
- **Test early**: Deploy to Zeabur in Week 2 to catch environment issues
- **Document as you go**: Update README with each working feature
- **Keep costs low**: Use Zeabur free tier until necessary to upgrade
