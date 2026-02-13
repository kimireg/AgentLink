#!/usr/bin/env node

/**
 * listener.mjs — XMTP Message Listener (Long-Running)
 * 
 * Listens for incoming XMTP messages and outputs them as JSON to stdout.
 * Designed to run as a background process, piped to a log file or agent framework.
 * 
 * Usage:
 *   node listener.mjs                    Listen for all messages
 *   node listener.mjs --json             JSON output (default)
 *   node listener.mjs --human            Human-readable output
 *   node listener.mjs 2>>errors.log      Redirect errors to log
 * 
 * Output (JSON mode, one line per message):
 *   {"type":"message","from":"0x...","content":"Hello","conversationId":"...","timestamp":"..."}
 *   {"type":"started","address":"0x...","env":"dev","timestamp":"..."}
 * 
 * Integration with agent frameworks:
 *   - Run as background process or via cron/pm2
 *   - Pipe output to a file that heartbeat can check
 *   - Or integrate with sessions_send for real-time forwarding
 */

import { createAgent } from "./lib/client.mjs";

const args = process.argv.slice(2);
const humanMode = args.includes("--human");

function output(obj) {
  if (humanMode) {
    if (obj.type === "started") {
      console.log(`\n🤖 XMTP Listener Started`);
      console.log(`📍 Address: ${obj.address}`);
      console.log(`🌐 Network: ${obj.env}`);
      console.log(`⏰ Time: ${obj.timestamp}`);
      console.log(`\n👂 Waiting for messages...\n`);
    } else if (obj.type === "message") {
      console.log(`📩 [${obj.timestamp}] From ${obj.from}:`);
      console.log(`   ${obj.content}`);
      console.log();
    } else if (obj.type === "error") {
      console.log(`❌ [${obj.timestamp}] Error: ${obj.error}`);
    }
  } else {
    console.log(JSON.stringify(obj));
  }
}

async function main() {
  console.error("🔌 Connecting to XMTP network...");
  const agent = await createAgent();
  
  output({
    type: "started",
    address: agent.address,
    env: process.env.XMTP_ENV || "dev",
    timestamp: new Date().toISOString(),
  });

  // Listen for text messages
  agent.on("text", async (ctx) => {
    try {
      // Get sender address from inbox
      const senderInboxId = ctx.message.senderInboxId;
      let senderAddress = senderInboxId; // fallback
      
      try {
        const inboxState = await ctx.client.preferences.inboxStateFromInboxIds([senderInboxId]);
        if (inboxState?.[0]?.identifiers?.[0]?.identifier) {
          senderAddress = inboxState[0].identifiers[0].identifier;
        }
      } catch {
        // If we can't resolve, use inboxId as identifier
      }

      output({
        type: "message",
        from: senderAddress,
        fromInboxId: senderInboxId,
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

  // Listen for new DM conversations
  agent.on("dm", async (ctx) => {
    output({
      type: "new_dm",
      conversationId: ctx.conversation.id,
      timestamp: new Date().toISOString(),
    });
  });

  // Listen for new group conversations
  agent.on("group", async (ctx) => {
    output({
      type: "new_group",
      conversationId: ctx.conversation.id,
      timestamp: new Date().toISOString(),
    });
  });

  // Error handling
  agent.on("unhandledError", (error) => {
    output({
      type: "error",
      error: error?.message || String(error),
      timestamp: new Date().toISOString(),
    });
  });

  // Start listening
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
  process.exit(1);
});
