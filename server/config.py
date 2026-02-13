# AgentLink Relay Server Configuration

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Server settings
    app_name: str = "AgentLink Relay Server"
    debug: bool = False
    port: int = 8000
    host: str = "0.0.0.0"

    # Database settings
    database_url: str = "postgresql://localhost/agentlink"

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    redis_db: int = 0

    # Ethereum settings
    eth_chain_id: int = 84532  # Base Sepolia testnet
    eth_rpc_url: str = "https://base-sepolia.infura.io/v3/YOUR_INFURA_KEY"

    # Security settings
    cors_origins: List[str] = ["*"]  # In production, restrict to specific origins

    # Message queue settings
    message_ttl_seconds: int = 604800  # 7 days

    # WebSocket settings
    websocket_ping_interval: int = 30  # seconds
    websocket_ping_timeout: int = 10  # seconds

    # API settings
    api_prefix: str = "/api"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
