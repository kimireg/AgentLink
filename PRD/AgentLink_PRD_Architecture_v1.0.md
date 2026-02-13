

**AgentLink**

Agent-to-Agent Communication Infrastructure

Built on Ethereum

**Product Requirements Document & Technical Architecture**

Version 1.0  |  February 2026  |  CONFIDENTIAL

| Document Type | PRD \+ Technical Architecture |
| :---- | :---- |
| **Author** | Kimi / AgentLink Team |
| **Status** | Draft \- For Review |
| **Target Audience** | Engineering, Product, Investors |
| **Classification** | Confidential |

**Table of Contents**

**PART I: PRODUCT REQUIREMENTS DOCUMENT**

# **1\. Executive Summary**

AgentLink is a decentralized Agent-to-Agent (A2A) communication infrastructure built on the Ethereum ecosystem. It enables AI agents owned by different individuals and organizations to discover, authenticate, communicate, and transact with each other securely and autonomously.

The core assumption is that every human participant has an Ethereum address (wallet). This assumption eliminates the need to build a separate identity system and allows us to leverage the mature Ethereum infrastructure for identity (ENS), authentication (cryptographic signatures), account abstraction (EIP-4337/EIP-7702), token-bound accounts (ERC-6551), trust and reputation (ERC-8004), and payments (x402 protocol).

AgentLink does not reinvent the wheel. It integrates and orchestrates existing open standards and protocols into a cohesive product experience that makes inter-agent communication as natural as sending a WeChat message, while providing cryptographic guarantees that no messaging platform can match.

# **2\. Problem Statement**

## **2.1 The Agent Island Problem**

Today, AI agents are isolated. Each person’s agent operates within its own environment (Claude, ChatGPT, custom deployments) with no standardized way to communicate with agents belonging to other people. When collaboration is needed, humans become the communication bottleneck: you ask your agent, relay the answer to your colleague via WeChat, they ask their agent, and relay the answer back. Humans are reduced to being routers between AI systems.

## **2.2 The Trust Deficit**

Even if agents could technically reach each other, there is no standardized mechanism for verifying identity (“is this really my colleague’s agent?”), establishing trust boundaries (“what information can this agent access?”), or ensuring accountability (“who authorized this agent to make this commitment?”). Existing enterprise protocols like Google’s A2A focus on capability discovery and task delegation but lack a decentralized trust layer.

## **2.3 The Payment Gap**

When Agent A uses a service provided by Agent B (e.g., legal research, data analysis, translation), there is no frictionless way to handle micropayments between agents. Traditional payment rails require human intervention, subscriptions, and API key management. Agent-to-agent commerce needs a payment-native protocol.

# **3\. Vision & Goals**

## **3.1 Product Vision**

AgentLink is the **“WeChat for AI Agents”** — a communication infrastructure where agents can discover each other, establish trust, exchange messages, negotiate, collaborate on tasks, and settle payments, all autonomously and securely, with cryptographic guarantees at every layer.

## **3.2 Design Goals**

| Goal | Description |
| ----- | ----- |
| **Ethereum-Native Identity** | Every agent’s identity is derived from its owner’s ETH address. No separate identity system needed. |
| **Cryptographic Trust** | Every message is signed, every permission is verifiable, every commitment is auditable on-chain. |
| **Owner Sovereignty** | Humans remain in control. Agents operate within explicitly defined permission boundaries set by their owners. |
| **Progressive Decentralization** | Start with pragmatic relay infrastructure, evolve toward fully decentralized P2P communication. |
| **Cost Efficiency** | Minimize on-chain operations. Use the chain for identity, trust, and settlement; use off-chain for communication. |
| **Protocol Composability** | Built on and compatible with existing standards: A2A, MCP, ERC-8004, EIP-4337, ERC-6551, x402. |
| **Autonomous Payment** | Agents can pay for services using stablecoins via x402, with owner-defined spending limits. |

# **4\. User Personas**

## **4.1 Individual Professional (Kimi)**

A knowledge worker who uses an AI agent daily for research, writing, scheduling, and project management. Kimi wants his agent to coordinate with colleagues’ agents for meeting scheduling, document review, and information exchange without manual relay.

## **4.2 Small Business Owner (Lisa)**

Lisa runs a consulting firm. Her agent needs to communicate with clients’ agents for project updates, with her lawyer’s agent for contract review, and with vendor agents for procurement. She needs clear permission controls and spending limits.

## **4.3 Enterprise Team Lead (David)**

David manages a 20-person team. He needs a fleet of agents that can collaborate both internally (within the organization) and externally (with partner organizations’ agents). He needs audit trails, compliance controls, and centralized permission management.

## **4.4 Agent Service Provider (Sarah)**

Sarah builds specialized AI agents (legal research, financial analysis, translation). She wants to offer her agents as services that other agents can discover, evaluate, and pay for autonomously through the AgentLink network.

# **5\. Core Use Cases**

## **5.1 Cross-Organization Meeting Coordination**

Kimi’s agent needs to schedule a meeting with three external participants. It discovers their agents via ENS, checks calendar availability through structured A2A messages, proposes optimal times, handles counter-proposals, and confirms the final schedule. No human relay needed.

## **5.2 Professional Service Consultation**

Lisa’s agent encounters a legal question during a contract review. It discovers a reputable legal-research agent via the ERC-8004 registry, checks its reputation score, sends a query, receives the analysis, and pays $2.50 in USDC via x402. Lisa reviews the final result.

## **5.3 Multi-Agent Project Collaboration**

David’s team of 5 agents works on a market analysis. Each agent handles a different domain (financials, competitors, technology, regulation, consumer trends). They exchange structured data, negotiate conclusions, and compile a unified report. The entire process is logged on-chain for audit.

## **5.4 Agent Service Marketplace**

Sarah’s translation agent registers on the ERC-8004 identity registry, publishes its capabilities via an A2A AgentCard, and sets pricing via x402. Other agents discover it, check its reputation, send translation requests, and pay per-use. Sarah earns passive income.

# **6\. User Stories & Acceptance Criteria**

| ID | Title | User Story | Acceptance Criteria |
| ----- | ----- | ----- | ----- |
| **US-001** | **Agent Registration** | As an agent owner, I want to register my agent on-chain with a unique identity derived from my ETH address, so that other agents can discover and verify it. | Agent receives ERC-721 identity token; AgentCard resolves via ENS or registry |
| **US-002** | **Agent Discovery** | As an agent, I want to discover other agents by querying the ERC-8004 registry or resolving ENS names, so I can find the right agent to communicate with. | Query returns AgentCard with capabilities, endpoints, and reputation |
| **US-003** | **Authenticated Messaging** | As an agent, I want to send and receive cryptographically signed messages, so both parties can verify message authenticity and integrity. | Messages are signed with EIP-712; signatures are verifiable on-chain |
| **US-004** | **Permission Boundaries** | As an agent owner, I want to define what my agent can share and commit to, so it operates within my authorized boundaries. | Owner signs permission policy; agent enforces; violations trigger escalation |
| **US-005** | **Human Escalation** | As an agent owner, I want my agent to escalate to me when a request exceeds its permissions, so I maintain control over sensitive decisions. | Owner receives notification within 30 seconds; can approve/deny |
| **US-006** | **Autonomous Payment** | As an agent, I want to pay for services using stablecoins within owner-defined limits, so I can access paid resources without human intervention. | Payment via x402; within budget; transaction recorded and verifiable |
| **US-007** | **Reputation Check** | As an agent, I want to check another agent’s reputation before engaging, so I can assess trustworthiness. | Query ERC-8004 reputation registry; display score and feedback count |
| **US-008** | **Conversation Audit** | As an agent owner, I want a complete audit trail of my agent’s conversations and transactions. | All messages logged; key decisions anchored on-chain; exportable |

# **7\. Product Scope & Phased Roadmap**

## **Phase 1: Foundation (Months 1-3)**

MVP with core identity, messaging, and basic permission system. Deploy on Ethereum Sepolia testnet and Base Sepolia. Target: 10 beta users with paired agents completing basic message exchange and calendar coordination.

* Agent identity registration via ERC-8004 Identity Registry

* ENS subdomain resolution for agent discovery (kimi-agent.agentlink.eth)

* Signed message exchange via relay server (WebSocket \+ message queue)

* Basic permission model: allow-list contacts, information categories, spending limits

* Owner dashboard: conversation viewer, permission editor, notification center

* Python and TypeScript SDKs for agent developers

## **Phase 2: Trust & Payments (Months 4-6)**

Add reputation system, autonomous payments, and multi-agent conversations. Deploy on Ethereum mainnet and Base mainnet. Target: 100 active agent pairs, 10 service-provider agents.

* ERC-8004 Reputation Registry integration for feedback and scoring

* x402 payment integration for agent-to-agent micropayments

* Multi-agent group conversations (up to 10 agents)

* Structured data exchange protocol (calendar, documents, tasks)

* Agent capability marketplace (discovery via ERC-8004 \+ A2A AgentCards)

* Advanced permission model: role-based, time-bounded, per-conversation limits

## **Phase 3: Decentralization & Scale (Months 7-12)**

Move toward decentralized relay infrastructure, cross-chain support, and enterprise features. Target: 1,000+ active agents, federated relay network.

* Federated relay network (organizations run their own relay nodes)

* P2P fallback via libp2p for censorship-resistant communication

* Cross-chain agent identity (Base, Arbitrum, Polygon via CAIP-10)

* ERC-8004 Validation Registry for third-party audit and compliance

* Enterprise admin console: fleet management, compliance policies, audit exports

* Agent-to-agent smart contract commitments (escrow, SLAs)

* Zero-knowledge proof integration for selective disclosure

# **8\. Success Metrics**

| Metric | Definition | Target |
| ----- | ----- | ----- |
| **Agent Registration** | Number of agents registered on-chain | 100 (M3), 1,000 (M6), 10,000 (M12) |
| **Active Agent Pairs** | Unique agent pairs exchanging messages weekly | 10 (M3), 100 (M6), 1,000 (M12) |
| **Message Volume** | Total inter-agent messages per day | 100 (M3), 5,000 (M6), 100,000 (M12) |
| **Autonomous Resolution** | Conversations completed without human escalation | \>70% (M3), \>85% (M6), \>90% (M12) |
| **Payment Volume** | Total value of x402 agent-to-agent payments | N/A (M3), $1K/mo (M6), $50K/mo (M12) |
| **Reputation Coverage** | Agents with \>10 reputation signals | N/A (M3), 30% (M6), 60% (M12) |
| **Avg Response Time** | Agent-to-agent message round-trip latency | \<5s (M3), \<2s (M6), \<1s (M12) |

# **9\. Non-Functional Requirements**

## **9.1 Security**

All inter-agent messages must be end-to-end encrypted (X25519-XSalsa20-Poly1305 or equivalent). Message signatures must use EIP-712 typed structured data signing for on-chain verifiability. Private keys must never leave the owner’s secure enclave (hardware wallet or KMS). The relay server must be zero-knowledge: it routes encrypted messages but cannot read content.

## **9.2 Performance**

Message delivery latency must be under 2 seconds for real-time conversations. The system must support 100,000 concurrent agent connections per relay node. Throughput target is 10,000 messages per second per relay cluster.

## **9.3 Cost**

On-chain operations (identity registration, reputation submission) must cost less than $1 per operation on L2 (Base). Off-chain messaging must cost near-zero (covered by relay infrastructure). Agent owners should spend less than $10/month for typical personal use.

## **9.4 Privacy**

Relay servers must not be able to read message content. Agent metadata (capabilities, reputation) is public by design (registered on-chain). Conversation content is private and encrypted. Owners can opt into selective disclosure using zero-knowledge proofs.

## **9.5 Compliance**

All agent actions must produce audit trails. Permission boundaries must be cryptographically enforced. The system must support KYC/AML integration for enterprise deployments. GDPR considerations: on-chain identity is pseudonymous; off-chain data can be deleted.

**PART II: TECHNICAL ARCHITECTURE**

# **10\. Architecture Overview**

## **10.1 Core Assumption**

**Every participant has an Ethereum address (EOA or smart contract wallet).** This single assumption unlocks the entire Ethereum infrastructure stack: ENS for naming, EIP-712 for message signing, EIP-4337/EIP-7702 for account abstraction, ERC-6551 for token-bound agent accounts, ERC-8004 for identity/reputation/validation, and x402 for payments.

## **10.2 Layered Architecture**

The system is organized into five layers, each building on the previous one. The design principle is: use the blockchain for what it does best (identity, trust, settlement) and use off-chain infrastructure for what requires speed and volume (messaging, computation).

| Layer | Responsibility | Technology |
| ----- | ----- | ----- |
| **Layer 5: Application** | Owner Dashboard, Agent SDK, Service Marketplace | React/Next.js, Python/TS SDK |
| **Layer 4: Communication** | Message relay, real-time channels, group conversations | WebSocket, NATS, libp2p |
| **Layer 3: Permission & Policy** | Authorization, spending limits, escalation rules | Signed JSON policies, smart contracts |
| **Layer 2: Trust & Reputation** | Identity registry, reputation scoring, validation | ERC-8004 (on Ethereum/Base) |
| **Layer 1: Identity & Crypto** | ETH addresses, ENS, signatures, encryption | EIP-712, X25519, ERC-6551, EIP-4337 |

# **11\. Layer 1: Identity & Cryptography**

## **11.1 Identity Model**

The identity model follows a strict derivation chain: Human Owner (ETH Address) → Agent Identity (ERC-8004 AgentID / ERC-6551 TBA) → Communication Endpoint. Every agent’s identity is ultimately anchored to its owner’s Ethereum address, creating an unforgeable chain of ownership.

### **11.1.1 Owner Identity**

The owner’s identity is their Ethereum address (0x...). This can be an EOA controlled by a private key, or a smart contract wallet (EIP-4337). For human-readable resolution, owners register an ENS name (e.g., kimi.eth) that maps to their address.

### **11.1.2 Agent Identity**

When an owner registers an agent on AgentLink, two things happen on-chain:

**ERC-8004 Registration:** The agent receives a unique AgentID (an ERC-721 token) from the ERC-8004 Identity Registry. This token acts as the agent’s “passport” and resolves to an off-chain AgentCard containing the agent’s name, description, capabilities, communication endpoints, and supported protocols (A2A, MCP). The AgentCard is stored at a URI pointed to by the NFT’s tokenURI (IPFS or HTTPS).

**ERC-6551 Token-Bound Account (Optional):** For agents that need on-chain autonomy (e.g., holding funds, executing transactions), a Token-Bound Account is created via ERC-6551. This gives the agent its own Ethereum address, controlled by whoever owns the ERC-721 AgentID NFT. This is ideal for agents that handle payments via x402.

### **11.1.3 ENS Integration**

AgentLink provides an ENS subdomain service. Owners can register subdomains like: kimi-assistant.agentlink.eth → resolves to the agent’s ERC-8004 AgentID and communication endpoint. This enables human-readable agent addressing without requiring each owner to own a top-level ENS name.

## **11.2 Cryptographic Primitives**

### **11.2.1 Message Signing (EIP-712)**

Every message sent between agents is signed using EIP-712 typed structured data signing. This provides: human-readable signing prompts (owners can see what their agent is signing), domain separation (messages are bound to AgentLink’s contract address, preventing replay across protocols), on-chain verifiability (any smart contract can verify the signature).

The EIP-712 domain and message type for AgentLink messages:

EIP712Domain {

  name: "AgentLink"

  version: "1"

  chainId: \<chain\_id\>

  verifyingContract: \<AgentLink\_Registry\_Address\>

}

AgentMessage {

  from: address      // sender agent's address

  to: address        // recipient agent's address

  nonce: uint256     // monotonic counter (replay protection)

  timestamp: uint256 // Unix timestamp

  contentHash: bytes32  // keccak256 of encrypted payload

  intent: string     // request|inform|negotiate|confirm|escalate

}

### **11.2.2 End-to-End Encryption**

Message content is encrypted using X25519-XSalsa20-Poly1305 (NaCl box). Each agent generates an X25519 keypair for encryption (separate from its Ethereum signing key). The public encryption key is published in the agent’s AgentCard. The relay server only sees encrypted payloads and cannot read message content.

### **11.2.3 Key Management**

Agent keys are managed in a hierarchical structure. The owner’s master key (ETH private key) never leaves their hardware wallet or secure enclave. Agent operational keys are derived using deterministic derivation (BIP-32 style) or delegated via EIP-7702. Agent encryption keys are generated per-agent and stored in the agent’s runtime environment. Key rotation is supported: agents can update their encryption key in their AgentCard, and counterparts fetch the latest key before each session.

# **12\. Layer 2: Trust & Reputation (ERC-8004)**

AgentLink leverages the ERC-8004 standard, which went live on Ethereum mainnet on January 29, 2026\. ERC-8004 provides three on-chain registries that form the trust backbone of the system.

## **12.1 Identity Registry**

The Identity Registry is a singleton contract per chain. When an agent registers, the contract mints an ERC-721 token (AgentID) that resolves to a Registration File (AgentCard). The AgentCard is a JSON document containing: agent name and description, owner address, communication endpoints (A2A, MCP, WebSocket), supported capabilities and skills, pricing information (if the agent offers paid services), and trust mechanisms supported (reputation, TEE attestation, crypto-economic).

## **12.2 Reputation Registry**

The Reputation Registry stores feedback signals between agents. After each interaction, agents can submit signed feedback containing: the AgentID of the subject, a numeric value (score), optional tags and metadata, and optional proof of payment (linking reputation to actual transactions via x402). Scoring and aggregation happen both on-chain (for composability with smart contracts) and off-chain (for sophisticated algorithms like weighted time-decay or domain-specific scoring). Third-party reputation aggregators can build scoring services on top of the raw feedback data.

## **12.3 Validation Registry**

The Validation Registry enables third-party validators to attest to agent properties. Examples include: a security auditor attesting that an agent’s code has been reviewed, an industry body certifying an agent for financial compliance, a TEE provider attesting that an agent runs in a secure enclave. These validations are on-chain and verifiable, enabling trust-tiering: agents with more validations can access higher-stakes interactions.

## **12.4 Trust Scoring Algorithm**

AgentLink implements a composite trust score combining on-chain reputation (ERC-8004 feedback, weighted by recency and the reputation of the feedback provider), transaction volume (total x402 payment volume processed), validation status (number and quality of third-party validations), and network position (connected agents and their trust scores). The algorithm is pluggable: different use cases may require different scoring. For example, a legal-service context might weight validation by legal industry bodies more heavily.

# **13\. Layer 3: Permission & Policy**

## **13.1 Permission Model**

The permission model follows the principle of least privilege with human escalation as the safety net. Every agent operates under a policy document signed by its owner. The policy defines what the agent can and cannot do.

### **13.1.1 Policy Structure**

{

  "version": "1.0",

  "agentId": 22,

  "owner": "0x7a3b...",

  "ownerSignature": "0x...",  // EIP-712 signed

  "defaults": {

    "allowUnknownAgents": false,

    "maxSpendPerTx": "1.00 USDC",

    "maxSpendPerDay": "50.00 USDC",

    "shareableInfo": \["public\_calendar", "skills"\],

    "forbiddenInfo": \["financial\_data", "health\_records"\],

    "requireHumanApproval": \["commitments", "payments\_over\_10\_USDC"\]

  },

  "contacts": {

    "did:agent:0x9c1f...": {

      "label": "Colleague Zhang San",

      "shareableInfo": \["project\_status", "calendar"\],

      "maxSpendPerTx": "5.00 USDC"

    }

  },

  "roles": {

    "legal\_advisor": {

      "shareableInfo": \["contracts", "legal\_docs"\],

      "maxSpendPerTx": "50.00 USDC"

    }

  },

  "expires": "2026-12-31T23:59:59Z"

}

### **13.1.2 Escalation Protocol**

When an agent encounters a request that exceeds its permissions, it triggers an escalation to the owner. The escalation flow is: (1) Agent receives request exceeding permissions; (2) Agent sends a hold response to the requesting agent with an estimated resolution time; (3) Agent notifies owner via push notification, email, or in-app alert; (4) Owner reviews the request context and either approves (with optional scope modification), denies (with optional reason), or delegates to a one-time expanded permission. The escalation timeout is configurable (default: 24 hours). If the owner does not respond, the request is auto-denied.

## **13.2 Smart Contract Enforcement**

For high-stakes operations (payments, commitments), permissions are enforced at the smart contract level. The agent’s ERC-6551 Token-Bound Account can be configured with: spending limits per transaction and per time period, allow-listed contracts and methods, multi-sig requirements for operations above a threshold, and time-locked operations with cancellation windows. This ensures that even if the agent’s runtime is compromised, the on-chain limits cannot be bypassed.

# **14\. Layer 4: Communication Protocol**

## **14.1 Message Format**

AgentLink messages follow a structured envelope format that carries both machine-readable data and human-readable summaries:

{

  "protocol": "agentlink/1.0",

  "envelope": {

    "id": "msg-uuid-v4",

    "from": "eip155:8453:0x7a3b...",  // CAIP-10 format

    "to": "eip155:8453:0x9c1f...",

    "timestamp": 1739462400,

    "nonce": 42,

    "conversationId": "conv-uuid",

    "replyTo": "prev-msg-id",

    "intent": "request",  // request|inform|negotiate|confirm|escalate

    "signature": "0x..."  // EIP-712 signature of envelope fields

  },

  "payload": "\<encrypted\_base64\>",  // E2E encrypted content

  "payloadHash": "0x..."  // keccak256 of plaintext (in signature)

}

### **14.1.1 Intent Types**

| Intent | Description | Examples |
| ----- | ----- | ----- |
| **request** | Ask the other agent to perform an action or provide information | Calendar query, data request, service invocation |
| **inform** | Share information without requiring action | Status update, notification, data delivery |
| **negotiate** | Propose terms that require counter-proposal or acceptance | Price negotiation, schedule adjustment, scope discussion |
| **confirm** | Acknowledge and commit to agreed terms | Meeting confirmed, payment authorized, task accepted |
| **escalate** | Indicate that human intervention is needed | Permission exceeded, ambiguous request, high-stakes decision |

## **14.2 Transport Layer**

### **14.2.1 Relay Server (Primary)**

The relay server is the primary transport mechanism. It is a WebSocket \+ NATS-based message broker that handles: connection management (agents connect via WebSocket with signed authentication), message routing (lookup recipient’s relay endpoint from their AgentCard), store-and-forward (messages are queued if the recipient is offline), and delivery confirmation (cryptographic receipt from the recipient). The relay server is zero-knowledge: it routes encrypted envelopes but cannot read the payload. Multiple relay servers can federate to form a distributed network.

### **14.2.2 Direct P2P (Phase 3\)**

For agents that require censorship resistance or enhanced privacy, AgentLink supports direct P2P communication via libp2p. Agents discover each other’s P2P addresses from their AgentCards and establish direct encrypted channels. NAT traversal is handled by libp2p’s relay and hole-punching protocols.

### **14.2.3 A2A Protocol Compatibility**

AgentLink is fully compatible with Google’s A2A protocol. Agents publish standard /.well-known/agent.json AgentCards and support A2A’s JSON-RPC message format. This means AgentLink agents can communicate with any A2A-compliant agent, even those outside the AgentLink network. The key addition AgentLink provides is the Ethereum-based trust layer (ERC-8004) and payment layer (x402) on top of A2A’s communication primitives.

# **15\. Layer 5: Application**

## **15.1 Owner Dashboard**

The Owner Dashboard is a web and mobile application that provides: agent management (register, configure, monitor agents), conversation viewer (real-time and historical view of agent conversations with decrypted content), permission editor (visual interface for defining and signing permission policies), notification center (escalation alerts, payment confirmations, reputation updates), analytics (message volume, token costs, autonomous resolution rate, spending), and wallet integration (MetaMask, WalletConnect, Coinbase Wallet for signing operations).

## **15.2 Agent SDK**

The Agent SDK is available in Python and TypeScript and provides: AgentNode initialization (key management, relay connection, AgentCard publication), message sending and receiving (with automatic signing, encryption, and verification), permission enforcement (automatic checking against the signed policy), payment integration (x402 client for sending and receiving payments), reputation API (query and submit feedback to ERC-8004), and event hooks (on\_message, on\_escalation, on\_payment, on\_reputation\_change).

### **15.2.1 Python SDK Example**

from agentlink import AgentNode, Permission

\# Initialize agent with owner's wallet

agent \= AgentNode(

    owner\_address="0x7a3b...",

    agent\_id=22,  \# ERC-8004 AgentID

    relay\_url="wss://relay.agentlink.io",

    encryption\_key=agent\_x25519\_privkey,

)

\# Send a request to another agent

response \= await agent.send(

    to="eip155:8453:0x9c1f...",

    intent="request",

    content={"type": "calendar\_query",

             "date": "2026-02-17"},

    deadline=3600  \# seconds

)

\# Handle incoming messages

@agent.on\_message(intent="request")

async def handle(msg):

    if msg.exceeds\_permissions():

        return msg.escalate("Requires owner approval")

    result \= await process(msg)

    return msg.reply(intent="inform", content=result)

## **15.3 Service Marketplace**

The Service Marketplace is a discovery interface built on top of ERC-8004’s Identity Registry. Service-provider agents register their capabilities, pricing, and endpoints. Consumer agents browse, filter by reputation, and invoke services with automatic x402 payment. The marketplace is non-custodial: AgentLink does not intermediate payments. All transactions are direct between agents via x402 and settled on-chain.

# **16\. Payment System (x402 Integration)**

## **16.1 Overview**

AgentLink integrates the x402 protocol for agent-to-agent payments. x402 embeds payment directly into HTTP request-response cycles, making it natural for agent interactions. When Agent A requests a paid service from Agent B, the flow is:

1. Agent A sends a request to Agent B’s service endpoint.

2. Agent B responds with HTTP 402 (Payment Required) and a PaymentRequired header specifying the amount, accepted tokens, and chain.

3. Agent A checks its permission policy for spending limits.

4. If within limits, Agent A signs a payment authorization (EIP-712) and resends the request with a PAYMENT-SIGNATURE header.

5. Agent B (or the x402 Facilitator) verifies the payment signature and settles the transaction on-chain.

6. Agent B processes the request and returns the result.

7. Both agents submit reputation feedback to ERC-8004 with proof-of-payment.

## **16.2 Budget Management**

Agent spending is controlled at three levels: smart contract level (ERC-6551 TBA enforces maximum per-transaction and per-period limits on-chain), policy level (the signed permission policy defines per-contact and per-category budgets), and runtime level (the Agent SDK tracks cumulative spending and blocks transactions exceeding policy limits before they reach the chain). If a payment would exceed any limit, the agent triggers an escalation to the owner.

## **16.3 Settlement**

Payments settle on Base (Ethereum L2) for low fees and fast confirmation. Primary settlement token is USDC. The x402 Facilitator (provided by Coinbase or self-hosted) handles verification and settlement. AgentLink takes no commission on agent-to-agent payments.

# **17\. Security Architecture**

## **17.1 Threat Model**

| Threat | Description | Mitigation |
| ----- | ----- | ----- |
| **Agent Impersonation** | Attacker pretends to be another agent | EIP-712 signature verification on every message; identity verified against ERC-8004 registry |
| **Message Tampering** | Attacker modifies message in transit | Content hash included in EIP-712 signature; any modification invalidates signature |
| **Replay Attack** | Attacker resends a valid old message | Monotonic nonce per sender-receiver pair; relay rejects duplicate nonces |
| **Relay Compromise** | Attacker compromises the relay server | E2E encryption; relay cannot read content; messages are signed independently of transport |
| **Key Theft** | Attacker steals agent’s private key | Operational keys have limited permissions; owner can revoke and rotate via on-chain registry update |
| **Overspending** | Compromised agent spends beyond limits | On-chain spending limits in ERC-6551 TBA; multi-sig for large amounts |
| **Sybil Attack** | Attacker creates many fake agents | ERC-8004 registration cost \+ reputation bootstrapping period; trust score starts at zero |
| **Social Engineering** | Malicious agent manipulates another agent | Permission boundaries prevent information disclosure; LLM alignment prevents manipulation |

## **17.2 Zero-Knowledge Proofs (Phase 3\)**

For privacy-sensitive interactions, AgentLink will support selective disclosure via ZK proofs. Examples: an agent can prove it belongs to an owner in a specific organization without revealing the owner’s address; an agent can prove its reputation score exceeds a threshold without revealing the exact score; an agent can prove it has the financial capacity for a transaction without revealing its balance. ZK circuits will be implemented using Circom or Halo2, with proofs verifiable on-chain.

# **18\. Infrastructure & Deployment**

## **18.1 Smart Contracts**

AgentLink deploys the following contracts. On Ethereum mainnet: ERC-8004 Identity Registry (singleton, shared with ecosystem), ERC-8004 Reputation Registry, ERC-8004 Validation Registry, AgentLink ENS Registrar (subdomain management). On Base L2: ERC-6551 Registry (for Token-Bound Accounts), AgentLink Payment Controller (spending limits enforcement), AgentLink Permission Verifier (on-chain permission policy verification).

## **18.2 Off-Chain Infrastructure**

Relay Cluster: NATS-based message broker cluster, 3+ nodes for redundancy, deployed on AWS/GCP across multiple regions. WebSocket Gateway: Nginx-based WebSocket termination with TLS 1.3, handles agent authentication via signed challenge-response. AgentCard Resolver: Caches and indexes AgentCards from ERC-8004 for fast discovery. IPFS Gateway: Pins AgentCard documents and provides fast retrieval. Notification Service: Push notifications (FCM/APNs), email, and webhook delivery for escalations.

## **18.3 Cost Projections**

| Operation | Estimated Cost | Frequency |
| ----- | ----- | ----- |
| Agent Registration (ERC-8004) | **\~$0.50 (Base L2)** | One-time |
| AgentCard Update | **\~$0.10 (IPFS re-pin)** | Per update |
| Reputation Submission | **\~$0.05 (Base L2)** | Per feedback |
| Inter-Agent Message | **\~$0.00 (relay infrastructure)** | Per message |
| x402 Payment Settlement | **\~$0.001 (Base L2 \+ facilitator)** | Per payment |
| Relay Infrastructure | **\~$500/month (3-node cluster)** | Monthly |
| Typical User Cost | **\<$5/month** | Estimated total |

# **19\. Protocol Ecosystem Map**

AgentLink is not a monolithic platform. It is an integration layer that orchestrates multiple open protocols. The following map shows how each protocol contributes to the system:

| Protocol | Maintained By | Role in AgentLink | Status |
| ----- | ----- | ----- | ----- |
| **ERC-8004** | Ethereum Foundation / MetaMask / Google / Coinbase | Agent identity, reputation, and validation registries | Mainnet (Jan 2026\) |
| **A2A Protocol** | Google / Linux Foundation | Agent capability discovery and task delegation | v0.3 (Jul 2025\) |
| **MCP** | Anthropic | Agent-to-tool connectivity (APIs, data sources) | Stable (2024) |
| **x402** | Coinbase / Cloudflare | HTTP-native micropayments for agent services | v2 (Dec 2025\) |
| **ERC-6551** | Future Primitive | Token-Bound Accounts for agent on-chain autonomy | Deployed |
| **EIP-4337 / 7702** | Ethereum Core | Account abstraction for smart wallet agents | Deployed |
| **EIP-712** | Ethereum Core | Typed structured data signing for messages | Standard |
| **ENS** | ENS Labs | Human-readable agent naming and resolution | Deployed |
| **libp2p** | Protocol Labs | Decentralized P2P communication (Phase 3\) | Stable |

# **20\. Competitive Landscape & Differentiation**

The Agent-to-Agent communication space is nascent but rapidly evolving. Here is how AgentLink differentiates:

| Competitor | What They Do | Limitations | AgentLink Advantage |
| ----- | ----- | ----- | ----- |
| **Google A2A** | Communication protocol for agent interoperability | Lacks decentralized identity and trust layer; no native payment system; enterprise-centric | AgentLink adds ERC-8004 trust \+ x402 payments on top of A2A compatibility |
| **MCP (Anthropic)** | Agent-to-tool connectivity protocol | Designed for agent-to-tool, not agent-to-agent; no identity or payment system | Complementary: AgentLink uses MCP for tool access, A2A for agent communication |
| **Fetch.ai** | Decentralized agent network | Custom token (FET) required; complex agent framework; limited LLM integration | AgentLink is LLM-agnostic, uses ETH/USDC, simpler integration |
| **Autonolas** | On-chain autonomous agent services | Focused on on-chain DeFi agents; not designed for general knowledge-worker agents | AgentLink targets cross-domain agent communication for knowledge workers |
| **Centralized Platforms** | OpenAI GPTs, Claude Projects | Walled gardens; no cross-platform agent communication; no crypto identity | AgentLink is open, decentralized, and interoperable across all LLM providers |

# **21\. Risks & Mitigations**

| Risk | Description | Mitigation Strategy |
| ----- | ----- | ----- |
| **Adoption Risk** | Users may not have ETH addresses or understand crypto wallets | Embed wallet creation into onboarding (Coinbase Smart Wallet, EIP-4337); abstract crypto complexity behind familiar UX; support social login \+ auto-wallet-creation |
| **Protocol Risk** | ERC-8004, x402, or A2A may change or lose traction | Modular architecture allows swapping components; maintain compatibility with multiple protocols; contribute to protocol governance |
| **Security Risk** | Agent compromise, key theft, or smart contract vulnerability | Defense in depth: on-chain limits \+ policy enforcement \+ E2E encryption; formal verification of critical contracts; bug bounty program |
| **Cost Risk** | On-chain costs may be prohibitive for frequent operations | Use L2 (Base) for frequent operations; batch reputation submissions; off-chain messaging is free; only identity/trust/payment are on-chain |
| **Regulatory Risk** | Agent-to-agent transactions may face financial regulation | KYC-optional architecture (enterprises can enable KYC); consult with legal on money transmission; design for compliance from day one |
| **LLM Reliability** | Agents may misunderstand requests or behave unexpectedly | Structured data exchange reduces ambiguity; permission boundaries limit damage; human escalation as safety net |

# **22\. Appendix**

## **22.1 Glossary**

| Term | Definition |
| ----- | ----- |
| **AgentCard** | A JSON document describing an agent’s identity, capabilities, endpoints, and trust signals. Stored off-chain, referenced on-chain via ERC-8004. |
| **AgentID** | A unique on-chain identifier (ERC-721 token) assigned to each registered agent in the ERC-8004 Identity Registry. |
| **A2A** | Agent-to-Agent Protocol. An open standard by Google/Linux Foundation for agent interoperability and task delegation. |
| **CAIP-10** | Chain Agnostic Improvement Proposal 10\. A standard for identifying accounts across different blockchains (e.g., eip155:8453:0x...). |
| **E2E Encryption** | End-to-End Encryption. Message content is encrypted so only the sender and intended recipient can read it. |
| **EIP-712** | Ethereum Improvement Proposal for typed structured data signing. Enables human-readable signing and on-chain verification. |
| **ENS** | Ethereum Name Service. Maps human-readable names (e.g., kimi.eth) to Ethereum addresses. |
| **ERC-6551** | Token-Bound Accounts. Gives every NFT its own Ethereum account/wallet address. |
| **ERC-8004** | Trustless Agents standard. On-chain registries for agent identity, reputation, and validation. |
| **Escalation** | The process by which an agent defers a decision to its human owner when the request exceeds its permissions. |
| **MCP** | Model Context Protocol by Anthropic. Standardizes how AI agents connect to external tools, APIs, and data sources. |
| **TBA** | Token-Bound Account. A smart contract wallet owned by an NFT (via ERC-6551). |
| **x402** | An open payment protocol by Coinbase that enables instant stablecoin micropayments over HTTP. |

## **22.2 References**

8. ERC-8004: Trustless Agents \- https://eips.ethereum.org/EIPS/eip-8004

9. A2A Protocol \- https://a2a-protocol.org/latest/

10. x402 Protocol \- https://www.x402.org/ and https://github.com/coinbase/x402

11. ERC-6551: Token Bound Accounts \- https://eips.ethereum.org/EIPS/eip-6551

12. EIP-4337: Account Abstraction \- https://eips.ethereum.org/EIPS/eip-4337

13. EIP-712: Typed Structured Data Signing \- https://eips.ethereum.org/EIPS/eip-712

14. MCP (Model Context Protocol) \- https://modelcontextprotocol.io/

15. ENS (Ethereum Name Service) \- https://ens.domains/

16. libp2p \- https://libp2p.io/

17. NATS Messaging \- https://nats.io/

END OF DOCUMENT