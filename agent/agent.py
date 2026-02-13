# AgentLink Local Agent - Core Module

"""
AgentNode: Main entry point for local Agent

Usage:
    agent = AgentNode(
        owner_address="0x7a3b...",
        wallet_rpc_url="http://localhost:8545",
        relay_url="wss://agentlink.zeabur.app/ws"
    )

    agent.register(agent_name="My Agent", capabilities=["chat"])
    agent.connect()

    agent.send(to="agent://2", content="Hello!")
"""

from .crypto.eip712 import EIP712Signer
from .crypto.encryption import EncryptionManager
from .relay.client import WebSocketClient
from .llm.claude import ClaudeClient
from .models import AgentCard, Message
from typing import Optional, Callable, Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


class AgentNode:
    """
    Main Agent class that handles connection, messaging, and LLM integration
    """

    def __init__(
        self,
        owner_address: str,
        wallet_rpc_url: str,
        relay_url: str,
        agent_id: Optional[str] = None,
        private_key: Optional[str] = None,  # For testing only, not recommended for production
        anthropic_api_key: Optional[str] = None,
    ):
        """
        Initialize AgentNode

        Args:
            owner_address: Ethereum address of the agent owner (0x...)
            wallet_rpc_url: URL to Ethereum wallet RPC (MetaMask, etc.)
            relay_url: WebSocket URL of the Relay Server
            agent_id: Registered agent ID (if already registered)
            private_key: Private key for signing (for testing only)
            anthropic_api_key: Claude API key (optional)
        """
        self.owner_address = owner_address
        self.wallet_rpc_url = wallet_rpc_url
        self.relay_url = relay_url
        self.agent_id = agent_id

        # Initialize components
        self.signer = EIP712Signer(owner_address, wallet_rpc_url, private_key)
        self.encryption = EncryptionManager()
        self.websocket = WebSocketClient(relay_url, self.signer)
        self.llm = ClaudeClient(anthropic_api_key) if anthropic_api_key else None

        # Message handlers
        self._message_handlers = {}
        self._is_connected = False

        logger.info(f"AgentNode initialized for owner {owner_address}")

    async def register(
        self,
        agent_name: str,
        capabilities: list,
        description: Optional[str] = None,
    ) -> str:
        """
        Register this agent with the Relay Server

        Args:
            agent_name: Human-readable name for the agent
            capabilities: List of capabilities (e.g., ["chat", "calendar"])
            description: Optional description

        Returns:
            Registered agent_id
        """
        # Generate encryption key pair
        self.encryption.generate_keys()
        encryption_pubkey = self.encryption.get_public_key()

        # Prepare registration data
        registration_data = {
            "owner_address": self.owner_address,
            "agent_name": agent_name,
            "capabilities": capabilities,
            "description": description,
            "encryption_pubkey": encryption_pubkey,
        }

        # Sign registration with EIP-712
        signature = await self.signer.sign_registration(registration_data)
        registration_data["signature"] = signature

        # Send to relay server
        import requests
        response = requests.post(
            self.relay_url.replace("wss://", "https://").replace("/ws", "/api/register"),
            json=registration_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            raise Exception(f"Registration failed: {response.text}")

        result = response.json()
        self.agent_id = result["agent_id"]

        logger.info(f"Agent registered with ID: {self.agent_id}")
        return self.agent_id

    async def connect(self) -> bool:
        """
        Connect to the Relay Server via WebSocket

        Returns:
            True if connection successful
        """
        if not self.agent_id:
            raise Exception("Agent not registered. Call register() first.")

        # Connect WebSocket
        success = await self.websocket.connect(self.agent_id)

        if success:
            self._is_connected = True
            logger.info(f"Connected to relay server as agent {self.agent_id}")

            # Start message receive loop
            asyncio.create_task(self._receive_loop())

            return True
        else:
            logger.error("Failed to connect to relay server")
            return False

    async def disconnect(self):
        """Disconnect from the Relay Server"""
        await self.websocket.disconnect()
        self._is_connected = False
        logger.info("Disconnected from relay server")

    async def send(
        self,
        to: str,
        content: str,
        intent: str = "inform",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a message to another agent

        Args:
            to: Recipient agent ID (e.g., "agent://2" or "2")
            content: Message content (will be encrypted)
            intent: Message intent (request|inform|negotiate|confirm|escalate)
            metadata: Optional metadata to include

        Returns:
            True if message sent successfully
        """
        if not self._is_connected:
            raise Exception("Not connected. Call connect() first.")

        if not self.agent_id:
            raise Exception("Agent not registered.")

        # Extract recipient agent ID
        recipient_agent_id = to.replace("agent://", "")

        # Get recipient's encryption public key
        recipient_pubkey = await self._get_recipient_pubkey(recipient_agent_id)

        # Encrypt message content
        encrypted_payload = self.encryption.encrypt(recipient_pubkey, content)

        # Create message envelope
        message = {
            "from": self.agent_id,
            "to": recipient_agent_id,
            "intent": intent,
            "payload": encrypted_payload,
            "metadata": metadata or {},
        }

        # Sign message with EIP-712
        signature = await self.signer.sign_message(message)
        message["signature"] = signature

        # Send via WebSocket
        return await self.websocket.send_message(message)

    async def on_message(self, intent: Optional[str] = None):
        """
        Decorator to register message handlers

        Usage:
            @agent.on_message(intent="request")
            async def handle_request(msg):
                ...
        """
        def decorator(handler: Callable):
            key = intent or "all"
            if key not in self._message_handlers:
                self._message_handlers[key] = []
            self._message_handlers[key].append(handler)
            return handler
        return decorator

    async def _receive_loop(self):
        """Background task to receive and process messages"""
        while self._is_connected:
            try:
                message = await self.websocket.receive_message()

                if message:
                    await self._process_message(message)

            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                await asyncio.sleep(1)

    async def _process_message(self, message: Dict[str, Any]):
        """Process incoming message"""
        try:
            # Verify signature
            if not await self.signer.verify_signature(message):
                logger.warning(f"Invalid signature from {message.get('from')}")
                return

            # Decrypt payload
            sender_agent_id = message.get("from")
            sender_pubkey = await self._get_recipient_pubkey(sender_agent_id)
            decrypted_content = self.encryption.decrypt(sender_pubkey, message["payload"])

            # Call registered handlers
            intent = message.get("intent", "inform")

            # Call intent-specific handlers
            if intent in self._message_handlers:
                for handler in self._message_handlers[intent]:
                    await handler(decrypted_content, message)

            # Call "all" handlers
            if "all" in self._message_handlers:
                for handler in self._message_handlers["all"]:
                    await handler(decrypted_content, message)

            # If LLM is available, process with LLM
            if self.llm:
                response = await self.llm.process(decrypted_content)
                if response:
                    await self.send(
                        to=f"agent://{sender_agent_id}",
                        content=response,
                        intent="inform"
                    )

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _get_recipient_pubkey(self, agent_id: str) -> str:
        """Get recipient's encryption public key from AgentCard"""
        import requests

        # Query AgentCard from relay server
        url = self.relay_url.replace("wss://", "https://").replace("/ws", f"/agent/{agent_id}")
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f"Failed to get AgentCard for {agent_id}: {response.text}")

        agent_card = response.json()
        return agent_card.get("encryption_pubkey")

    @property
    def is_connected(self) -> bool:
        """Check if connected to relay server"""
        return self._is_connected
