#!/usr/bin/env node

/**
 * send.mjs — Send an XMTP message to an ETH address (v2)
 *
 * Uses @xmtp/agent-sdk (Agent.createFromEnv pattern).
 *
 * Usage:
 *   node send.mjs <address> <message>     Send a message
 *   node send.mjs --check <address>       Check if address is reachable on XMTP
 *   node send.mjs --info                  Show this agent's XMTP address
 *
 * Examples:
 *   node send.mjs 0x1234...abcd "Hello from Jason 🍎"
 *   node send.mjs --check 0x1234...abcd
 *   node send.mjs 0x1234...abcd '{"protocol":"agent-msg","type":"query","body":"What is ETH price?"}'
 */

import { createAgent } from "./lib/client.mjs";
import { IdentifierKind } from "@xmtp/node-sdk";

const args = process.argv.slice(2);

async function main() {
  // Help
  if (args.length === 0 || args[0] === "--help" || args[0] === "-h") {
    console.log(`
XMTP Send v2 — Agent Messaging Tool

Usage:
  node send.mjs <address> <message>     Send a text message
  node send.mjs --check <address>       Check if address is on XMTP
  node send.mjs --info                  Show this agent's address

Examples:
  node send.mjs 0xABC...123 "Hello!"
  node send.mjs --check 0xABC...123
`);
    process.exit(0);
  }

  // Initialize agent (loads .env, connects to XMTP)
  console.error("🔌 Connecting to XMTP network...");
  const agent = await createAgent();
  console.error(`✅ Connected as ${agent.address}`);

  // --info: Show this agent's address
  if (args[0] === "--info") {
    const info = {
      address: agent.address,
      env: process.env.XMTP_ENV || "dev",
      sdk: "@xmtp/agent-sdk v2",
    };
    // Also try to get test URL for dev network
    try {
      const { getTestUrl } = await import("@xmtp/agent-sdk/debug");
      info.testUrl = getTestUrl(agent.client);
    } catch {
      // debug module may not be available
    }
    console.log(JSON.stringify(info));
    process.exit(0);
  }

  // --check: Check if address is reachable
  if (args[0] === "--check") {
    const targetAddress = args[1];
    if (!targetAddress) {
      console.error("❌ Usage: node send.mjs --check <address>");
      process.exit(1);
    }

    try {
      const identifier = {
        identifier: targetAddress.toLowerCase(),
        identifierKind: IdentifierKind.Ethereum,
      };
      const canMessage = await agent.client.canMessage([identifier]);
      const reachable =
        canMessage.get(targetAddress.toLowerCase()) ||
        canMessage.get(targetAddress) ||
        false;
      console.log(
        JSON.stringify({
          address: targetAddress,
          reachable,
          network: process.env.XMTP_ENV || "dev",
        })
      );
    } catch (err) {
      console.error(`❌ Check failed: ${err.message}`);
      process.exit(1);
    }
    process.exit(0);
  }

  // Send message
  const targetAddress = args[0];
  const message = args.slice(1).join(" ");

  if (!targetAddress || !message) {
    console.error("❌ Usage: node send.mjs <address> <message>");
    process.exit(1);
  }

  if (!targetAddress.startsWith("0x")) {
    console.error("❌ Address must start with 0x");
    process.exit(1);
  }

  try {
    // Create or get existing DM conversation
    const conversation = await agent.createDmWithAddress(targetAddress);

    // Send the message (DM API)
    await conversation.send(message);

    console.log(
      JSON.stringify({
        status: "sent",
        to: targetAddress,
        from: agent.address,
        message_preview:
          message.length > 100 ? message.slice(0, 100) + "..." : message,
        timestamp: new Date().toISOString(),
      })
    );
  } catch (err) {
    console.error(`❌ Send failed: ${err.message}`);

    // Common error hints
    if (
      err.message.includes("not on the network") ||
      err.message.includes("canMessage")
    ) {
      console.error(
        `   Hint: The address may not have registered on XMTP yet.`
      );
      console.error(
        `   Check with: node send.mjs --check ${targetAddress}`
      );
    }
    if (err.message.includes("TLS") || err.message.includes("handshake")) {
      console.error(
        `   Hint: TLS error. Ensure you're using Node 22 LTS (not Node 25+).`
      );
      console.error(`   Fix: nvm use 22`);
    }
    process.exit(1);
  }

  process.exit(0);
}

main().catch((err) => {
  console.error(`💥 Fatal error: ${err.message}`);
  process.exit(1);
});
