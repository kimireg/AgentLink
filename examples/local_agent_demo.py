"""
AgentLink Local Agent Demo
Demonstrates how to use the AgentNode to connect and message
"""

import asyncio
import os
from agentlink import AgentNode

# Configuration
OWNER_ADDRESS = "0x7a3b..."  # Replace with your ETH address
WALLET_RPC_URL = "http://localhost:8545"  # MetaMask RPC
RELAY_URL = "wss://agentlink.zeabur.app/ws"  # Replace with your Zeabur URL


async def demo():
    """Demo script for AgentLink"""
    
    # Initialize Agent
    agent = AgentNode(
        owner_address=OWNER_ADDRESS,
        wallet_rpc_url=WALLET_RPC_URL,
        relay_url=RELAY_URL,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    
    # Register Agent (one-time)
    print("Registering agent...")
    agent_id = await agent.register(
        agent_name="Kimi's Assistant",
        capabilities=["chat", "research"],
        description="Personal AI assistant for Kimi"
    )
    print(f"Registered with agent_id: {agent_id}")
    
    # Connect to Relay Server
    print("Connecting to relay server...")
    connected = await agent.connect()
    
    if not connected:
        print("Failed to connect")
        return
    
    print("Connected!")
    
    # Register message handler
    @agent.on_message(intent="request")
    async def handle_request(content, message):
        print(f"\n📥 Received request: {content}")
        print(f"   From: {message.get('from')}")
        # Process with LLM or custom logic
        print("   Processing with LLM...")
    
    @agent.on_message(intent="inform")
    async def handle_inform(content, message):
        print(f"\n📥 Received message: {content}")
        print(f"   From: {message.get('from')}")
    
    # Send a test message
    print("\n📤 Sending test message...")
    recipient_agent_id = "agent://2"  # Replace with actual recipient agent ID
    success = await agent.send(
        to=recipient_agent_id,
        content="Hello! This is a test message from AgentLink.",
        intent="inform"
    )
    
    if success:
        print("Message sent successfully!")
    else:
        print("Failed to send message")
    
    # Keep running to receive messages
    print("\n📡 Waiting for messages... (Press Ctrl+C to exit)")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        await agent.disconnect()
        print("Disconnected")


if __name__ == "__main__":
    asyncio.run(demo())
