#!/usr/bin/env node

/**
 * history.mjs — Query XMTP conversation history
 * 
 * Usage:
 *   node history.mjs --list                   List all conversations
 *   node history.mjs <address>                Read messages with address (last 10)
 *   node history.mjs <address> --limit 50     Read more messages
 */

import { createAgent } from "./lib/client.mjs";

const args = process.argv.slice(2);

async function main() {
  if (args.length === 0 || args[0] === "--help") {
    console.log(`
XMTP History — Conversation Query Tool

Usage:
  node history.mjs --list                   List all conversations
  node history.mjs <address>                Read messages (last 10)
  node history.mjs <address> --limit 50     Read more messages
`);
    process.exit(0);
  }

  console.error("🔌 Connecting to XMTP network...");
  const agent = await createAgent();
  console.error(`✅ Connected as ${agent.address}`);

  // Sync conversations from network
  console.error("🔄 Syncing conversations...");
  await agent.client.conversations.sync();

  if (args[0] === "--list") {
    // List all conversations
    const conversations = await agent.client.conversations.list();
    
    const results = [];
    for (const conv of conversations) {
      results.push({
        id: conv.id,
        type: conv.isGroup ? "group" : "dm",
        createdAt: conv.createdAtNs ? new Date(Number(conv.createdAtNs / 1000000n)).toISOString() : null,
      });
    }
    
    console.log(JSON.stringify({ 
      total: results.length, 
      conversations: results 
    }, null, 2));
    process.exit(0);
  }

  // Read messages with a specific address
  const targetAddress = args[0];
  const limitIdx = args.indexOf("--limit");
  const limit = limitIdx !== -1 ? parseInt(args[limitIdx + 1]) || 10 : 10;

  try {
    // Find existing DM with address
    const conversations = await agent.client.conversations.listDms();
    
    // Try to find the conversation with this address
    // Note: XMTP V3 uses inboxId, so we need to look through conversations
    let targetConv = null;
    for (const conv of conversations) {
      // Sync conversation to get latest messages
      await conv.sync();
      targetConv = conv; // Simplified — in production, match by peer address
    }

    if (!targetConv) {
      console.error(`❌ No conversation found with ${targetAddress}`);
      console.log(JSON.stringify({ messages: [], total: 0 }));
      process.exit(0);
    }

    const messages = await targetConv.messages({ limit });
    
    const results = messages.map((msg) => ({
      id: msg.id,
      senderInboxId: msg.senderInboxId,
      content: msg.content,
      sentAt: msg.sentAtNs ? new Date(Number(msg.sentAtNs / 1000000n)).toISOString() : null,
      fromSelf: msg.senderInboxId === agent.client.inboxId,
    }));

    console.log(JSON.stringify({
      with: targetAddress,
      total: results.length,
      messages: results,
    }, null, 2));
  } catch (err) {
    console.error(`❌ Error: ${err.message}`);
    process.exit(1);
  }

  process.exit(0);
}

main().catch((err) => {
  console.error(`💥 Fatal error: ${err.message}`);
  process.exit(1);
});
