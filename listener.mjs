#!/usr/bin/env node

/**
 * listener.mjs — XMTP Message Listener v2 (Long-Running)
 *
 * Uses @xmtp/agent-sdk event-driven pattern (like Express.js).
 * Listens for incoming messages and outputs them as JSON to stdout.
 *
 * Usage:
 *   node listener.mjs                    Listen for all messages (JSON output)
 *   node listener.mjs --human            Human-readable output
 *   node listener.mjs 2>>errors.log      Redirect errors to log
 *
 * Output (JSON mode, one line per message):
 *   {"type":"message","from":"0x...","content":"Hello","conversationId":"...","timestamp":"..."}
 *   {"type":"started","address":"0x...","env":"dev","timestamp":"..."}
 *
 * Integration with OpenClaw:
 *   - Run as background process or via cron/pm2
 *   - Pipe output to a file that heartbeat can check
 *   - Or integrate with sessions_send for real-time forwarding
 */

import { createAgent } from "./lib/client.mjs";

const args = process.argv.slice(2);
const humanMode = args.includes("--human");

function output(obj) {
  if (humanMode) {
    switch (obj.type) {
      case "started":
        console.log(`\n🤖 XMTP Listener v2 Started`);
        console.log(`📍 Address: ${obj.address}`);
        console.log(`🌐 Network: ${obj.env}`);
        if (obj.testUrl) console.log(`🔗 Test: ${obj.testUrl}`);
        console.log(`⏰ Time: ${obj.timestamp}`);
        console.log(`\n👂 Waiting for messages...\n`);
        break;
      case "message":
        console.log(`📩 [${obj.timestamp}] From ${obj.from}:`);
        console.log(`   ${obj.content}`);
        console.log();
        break;
      case "new_dm":
        console.log(`🆕 New DM conversation: ${obj.conversationId}`);
        break;
      case "new_group":
        console.log(`👥 New group conversation: ${obj.conversationId}`);
        break;
      case "error":
        console.log(`❌ [${obj.timestamp}] Error: ${obj.error}`);
        break;
    }
  } else {
    console.log(JSON.stringify(obj));
  }
}

async function main() {
  console.error("🔌 Connecting to XMTP network...");
  const agent = await createAgent();

  // Build startup info
  const startInfo = {
    type: "started",
    address: agent.address,
    env: process.env.XMTP_ENV || "dev",
    timestamp: new Date().toISOString(),
  };

  // Try to get test URL (dev network)
  try {
    const { getTestUrl } = await import("@xmtp/agent-sdk/debug");
    startInfo.testUrl = getTestUrl(agent.client);
  } catch {
    // debug module may not be available
  }

  output(startInfo);

  // === Event Handlers (Agent SDK v1.1 pattern) ===

  // Handle text messages
  agent.on("text", async (ctx) => {
    try {
      // Skip messages sent by ourselves
      if (ctx.message.senderInboxId === agent.inboxId) return;

      // Resolve sender address from inbox ID
      let senderAddress = ctx.message.senderInboxId; // fallback
      try {
        const inboxState =
          await ctx.client.preferences.inboxStateFromInboxIds([
            ctx.message.senderInboxId,
          ]);
        if (inboxState?.[0]?.identifiers?.[0]?.identifier) {
          senderAddress = inboxState[0].identifiers[0].identifier;
        }
      } catch {
        // If we can't resolve, use inboxId as identifier
      }

      output({
        type: "message",
        from: senderAddress,
        fromInboxId: ctx.message.senderInboxId,
        content: ctx.message.content,
        conversationId: ctx.conversation.id,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      output({
        type: "error",
        error: err.message,
        timestamp: new Date().toISOString(),
      });
    }
  });

  // Handle new DM conversations
  agent.on("dm", async (ctx) => {
    output({
      type: "new_dm",
      conversationId: ctx.conversation.id,
      timestamp: new Date().toISOString(),
    });
  });

  // Handle new group conversations
  agent.on("group", async (ctx) => {
    output({
      type: "new_group",
      conversationId: ctx.conversation.id,
      timestamp: new Date().toISOString(),
    });
  });

  // Agent ready
  agent.on("start", () => {
    console.error("✅ Agent event loop started, listening for messages...");
  });

  // Start the agent event loop (blocks until stopped)
  await agent.start();
}

// Graceful shutdown
process.on("SIGINT", () => {
  console.error("\n🛑 Listener stopped (SIGINT)");
  process.exit(0);
});

process.on("SIGTERM", () => {
  console.error("🛑 Listener stopped (SIGTERM)");
  process.exit(0);
});

main().catch((err) => {
  console.error(`💥 Fatal error: ${err.message}`);
  if (err.message.includes("TLS") || err.message.includes("handshake")) {
    console.error(
      `   Hint: TLS error. Ensure you're using Node 22 LTS (not Node 25+).`
    );
    console.error(`   Fix: nvm use 22`);
  }
  process.exit(1);
});
