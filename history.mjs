#!/usr/bin/env node

/**
 * history.mjs — Read XMTP conversation history (v2)
 *
 * Usage:
 *   node history.mjs --list                   List all conversations
 *   node history.mjs <address> [--limit N]    Read messages with an address
 *
 * Examples:
 *   node history.mjs --list
 *   node history.mjs 0x1234...abcd
 *   node history.mjs 0x1234...abcd --limit 50
 */

import { createAgent } from "./lib/client.mjs";

const args = process.argv.slice(2);

async function main() {
  if (args.length === 0 || args[0] === "--help" || args[0] === "-h") {
    console.log(`
XMTP History v2 — Conversation Reader

Usage:
  node history.mjs --list                   List all conversations
  node history.mjs <address> [--limit N]    Read messages (default limit: 20)
`);
    process.exit(0);
  }

  console.error("🔌 Connecting to XMTP network...");
  const agent = await createAgent();
  console.error(`✅ Connected as ${agent.address}`);

  // --list: List all conversations
  if (args[0] === "--list") {
    try {
      // Sync conversations from network
      await agent.client.conversations.sync();
      const conversations = await agent.client.conversations.list();

      if (conversations.length === 0) {
        console.log(JSON.stringify({ conversations: [], count: 0 }));
        process.exit(0);
      }

      const convList = [];
      for (const conv of conversations) {
        const info = {
          id: conv.id,
          createdAt: conv.createdAtNs
            ? new Date(Number(conv.createdAtNs / 1000000n)).toISOString()
            : null,
        };

        // Try to get members
        try {
          const members = await conv.members();
          info.memberCount = members.length;
          // Extract addresses from members
          const addresses = [];
          for (const m of members) {
            if (m.addresses) {
              addresses.push(...m.addresses);
            }
          }
          info.members = addresses;
        } catch {
          // Some conversation types may not support members
        }

        convList.push(info);
      }

      console.log(
        JSON.stringify({ conversations: convList, count: convList.length })
      );
    } catch (err) {
      console.error(`❌ List failed: ${err.message}`);
      process.exit(1);
    }
    process.exit(0);
  }

  // Read messages for a specific address
  const targetAddress = args[0];
  const limitIdx = args.indexOf("--limit");
  const limit = limitIdx !== -1 ? parseInt(args[limitIdx + 1], 10) || 20 : 20;

  if (!targetAddress.startsWith("0x")) {
    console.error("❌ Address must start with 0x");
    process.exit(1);
  }

  try {
    // Sync and find conversation with address
    await agent.client.conversations.sync();
    const conversations = await agent.client.conversations.list();

    // Find conversation matching the address
    let targetConv = null;
    for (const conv of conversations) {
      try {
        const members = await conv.members();
        for (const m of members) {
          if (m.addresses?.some((a) => a.toLowerCase() === targetAddress.toLowerCase())) {
            targetConv = conv;
            break;
          }
        }
      } catch {
        continue;
      }
      if (targetConv) break;
    }

    if (!targetConv) {
      console.log(
        JSON.stringify({
          address: targetAddress,
          messages: [],
          count: 0,
          note: "No conversation found with this address",
        })
      );
      process.exit(0);
    }

    // Sync and read messages
    await targetConv.sync();
    const messages = await targetConv.messages();

    // Take last N messages
    const recentMessages = messages.slice(-limit).map((msg) => ({
      id: msg.id,
      senderInboxId: msg.senderInboxId,
      content: msg.content,
      sentAt: msg.sentAtNs
        ? new Date(Number(msg.sentAtNs / 1000000n)).toISOString()
        : null,
    }));

    console.log(
      JSON.stringify({
        address: targetAddress,
        conversationId: targetConv.id,
        messages: recentMessages,
        count: recentMessages.length,
        total: messages.length,
      })
    );
  } catch (err) {
    console.error(`❌ History read failed: ${err.message}`);
    process.exit(1);
  }

  process.exit(0);
}

main().catch((err) => {
  console.error(`💥 Fatal error: ${err.message}`);
  process.exit(1);
});
