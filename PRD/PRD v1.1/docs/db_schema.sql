-- AgentComms MVP (ACP/0.1) - Postgres schema
-- Notes:
-- - This schema stores ONLY ciphertext for message payload (E2EE).
-- - Agent certificate is Owner-signed (EIP-712), verified on register.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) Agents (Directory)
CREATE TABLE IF NOT EXISTS agents (
  agent_id           UUID PRIMARY KEY,
  owner_address      VARCHAR(42) NOT NULL,                 -- "0x..." (lowercase recommended)
  agent_sign_pk      BYTEA NOT NULL,                       -- 32 bytes Ed25519 public key
  agent_enc_pk       BYTEA NOT NULL,                       -- 32 bytes Curve25519 public key

  permissions_hash   BYTEA NOT NULL,                       -- 32 bytes (keccak256)
  issued_at_ms       BIGINT NOT NULL,
  expires_at_ms      BIGINT NOT NULL,
  nonce              BIGINT NOT NULL,
  chain_id           BIGINT NOT NULL,
  owner_signature    BYTEA NOT NULL,                       -- EIP-712 signature bytes

  status             TEXT NOT NULL DEFAULT 'active',       -- 'active' | 'revoked'
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at         TIMESTAMPTZ NULL,

  CONSTRAINT agents_status_check CHECK (status IN ('active','revoked'))
);

CREATE INDEX IF NOT EXISTS idx_agents_owner ON agents(owner_address);
CREATE UNIQUE INDEX IF NOT EXISTS uq_agents_sign_pk ON agents(agent_sign_pk);

-- 2) Allowlist (policy)
-- Recipient decides who can send to them.
CREATE TABLE IF NOT EXISTS allowlist (
  recipient_agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  sender_agent_id    UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  allow              BOOLEAN NOT NULL DEFAULT TRUE,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (recipient_agent_id, sender_agent_id)
);

-- 3) Messages (Relay store & forward)
CREATE TABLE IF NOT EXISTS messages (
  id                 BIGSERIAL PRIMARY KEY,               -- acts as cursor
  message_id         UUID NOT NULL,
  sender_agent_id    UUID NOT NULL REFERENCES agents(agent_id) ON DELETE RESTRICT,
  recipient_agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE RESTRICT,

  header_b64         TEXT NOT NULL,                       -- base64url(header_bytes)
  ciphertext         BYTEA NOT NULL,                      -- ciphertext bytes (sealed box)
  signature          BYTEA NOT NULL,                      -- Ed25519 signature bytes

  received_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at         TIMESTAMPTZ NOT NULL,                -- derived from header timestamp + ttl
  acked_at           TIMESTAMPTZ NULL,
  status             TEXT NOT NULL DEFAULT 'pending',      -- 'pending' | 'acked' | 'expired'

  CONSTRAINT messages_status_check CHECK (status IN ('pending','acked','expired'))
);

-- Anti-replay / dedup: message_id unique per recipient
CREATE UNIQUE INDEX IF NOT EXISTS uq_messages_recipient_msgid
  ON messages(recipient_agent_id, message_id);

-- Fast poll: pending messages per recipient ordered by cursor
CREATE INDEX IF NOT EXISTS idx_messages_inbox
  ON messages(recipient_agent_id, id)
  WHERE status = 'pending';

-- Optional: quickly query sender->recipient traffic
CREATE INDEX IF NOT EXISTS idx_messages_sender_recipient
  ON messages(sender_agent_id, recipient_agent_id, received_at);

