# AgentLink Relay Server Database Models

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Agent(Base):
    """
    Agent registration table
    Stores agent identity and metadata
    """
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_id = Column(String(64), unique=True, nullable=False, index=True)  # UUID string
    owner_address = Column(String(66), nullable=False, index=True)  # Ethereum address (0x...)
    agent_name = Column(String(255), nullable=False)
    capabilities = Column(JSON, nullable=False, default=[])  # List of capability strings
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # E2E encryption key (X25519 public key, base64 encoded)
    encryption_pubkey = Column(String(255), nullable=False)

    # Status
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index('ix_agents_owner_address', 'owner_address'),
        Index('ix_agents_agent_id', 'agent_id'),
    )

    def to_dict(self):
        return {
            'agent_id': self.agent_id,
            'owner_address': self.owner_address,
            'agent_name': self.agent_name,
            'capabilities': self.capabilities,
            'description': self.description,
            'encryption_pubkey': self.encryption_pubkey,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
        }

    def __repr__(self):
        return f"<Agent(id={self.id}, agent_id={self.agent_id}, name={self.agent_name})>"


class MessageQueue(Base):
    """
    Offline message queue
    Stores messages for agents that are currently offline
    """
    __tablename__ = 'message_queue'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # Sender and recipient
    sender_agent_id = Column(String(64), nullable=False, index=True)
    recipient_agent_id = Column(String(64), nullable=False, index=True)

    # Message envelope (JSON, signed but not decrypted)
    envelope = Column(JSON, nullable=False)

    # Encrypted payload (base64 encoded)
    payload = Column(Text, nullable=False)

    # Metadata
    intent = Column(String(50), nullable=False)  # request|inform|negotiate|confirm|escalate
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    is_delivered = Column(Boolean, default=False)

    __table_args__ = (
        Index('ix_message_queue_recipient', 'recipient_agent_id', 'is_delivered'),
        Index('ix_message_queue_created', 'created_at'),
    )

    def to_dict(self):
        return {
            'message_id': self.message_id,
            'sender_agent_id': self.sender_agent_id,
            'recipient_agent_id': self.recipient_agent_id,
            'intent': self.intent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_delivered': self.is_delivered,
        }

    def __repr__(self):
        return f"<MessageQueue(id={self.id}, to={self.recipient_agent_id}, delivered={self.is_delivered})>"


class Connection(Base):
    """
    Active WebSocket connections
    Tracks which agents are currently connected
    Note: This table is updated frequently, consider using Redis for production
    """
    __tablename__ = 'connections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(64), nullable=False, unique=True, index=True)
    connection_id = Column(String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    websocket_session_id = Column(String(64), nullable=True)  # For tracking WebSocket sessions
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index('ix_connections_agent_id', 'agent_id'),
        Index('ix_connections_active', 'is_active'),
    )

    def to_dict(self):
        return {
            'agent_id': self.agent_id,
            'connection_id': self.connection_id,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'is_active': self.is_active,
        }

    def __repr__(self):
        return f"<Connection(agent_id={self.agent_id}, active={self.is_active})>"


# Index for agent lookup by owner
Index('ix_agent_owner', Agent.owner_address, Agent.is_active)
