#!/usr/bin/env node

/**
 * check-new.mjs — One-shot check for new XMTP messages (v2)
 *
 * Designed for cron jobs. Connects, syncs, checks for new messages,
 * outputs any unread messages, then exits.
 *
 * Usage:
 *   node check-new.mjs                    Check for new messages
 *   node check-new.mjs --since 15         Only messages from last 15 minutes (default)
 *   node check-new.mjs --since 60         Last 60 minutes
 *
 * Output:
 *   {"hasNew":true,"messages":[...],"count":3}
 *   {"hasNew":false,"messages":[],"count":0}
 */

import { createAgent } from "./lib/client.mjs";

const args = process.argv.slice(2);

async function main() {
  // Parse --since argument (minutes)
  const sinceIdx = args.indexOf("--since");
  const sinceMinutes =
    sinceIdx !== -1 ? parseInt(args[sinceIdx + 1], 10) || 15 : 15;
  const sinceTime = Date.now() - sinceMinutes * 60 * 1000;

  console.error("🔌 Connecting to XMTP network...");
  const agent = await createAgent();
  console.error(
    `✅ Connected as ${agent.address}, checking last ${sinceMinutes} min...`
  );

  try {
    // Sync conversations from network
    await agent.client.conversations.sync();
    const conversations = await agent.client.conversations.list();

    const newMessages = [];

    for (const conv of conversations) {
      try {
        await conv.sync();
        const messages = await conv.messages();

        for (const msg of messages) {
          // Skip our own messages
          if (msg.senderInboxId === agent.inboxId) continue;

          // Check timestamp
          const sentAt = msg.sentAtNs
            ? Number(msg.sentAtNs / 1000000n)
            : 0;
          if (sentAt < sinceTime) continue;

          // Resolve sender
          let senderAddress = msg.senderInboxId;
          try {
            const inboxState =
              await agent.client.preferences.inboxStateFromInboxIds([
                msg.senderInboxId,
              ]);
            if (inboxState?.[0]?.identifiers?.[0]?.identifier) {
              senderAddress = inboxState[0].identifiers[0].identifier;
            }
          } catch {
            // fallback to inboxId
          }

          newMessages.push({
            from: senderAddress,
            content:
              typeof msg.content === "string"
                ? msg.content
                : JSON.stringify(msg.content),
            conversationId: conv.id,
            timestamp: sentAt
              ? new Date(sentAt).toISOString()
              : null,
          });
        }
      } catch {
        // Skip conversations that fail to sync
        continue;
      }
    }

    // Sort by timestamp (newest first)
    newMessages.sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    console.log(
      JSON.stringify({
        hasNew: newMessages.length > 0,
        messages: newMessages,
        count: newMessages.length,
        checkedSinceMinutes: sinceMinutes,
        agentAddress: agent.address,
        timestamp: new Date().toISOString(),
      })
    );
  } catch (err) {
    console.error(`❌ Check failed: ${err.message}`);
    console.log(
      JSON.stringify({
        hasNew: false,
        messages: [],
        count: 0,
        error: err.message,
        timestamp: new Date().toISOString(),
      })
    );
    process.exit(1);
  }

  process.exit(0);
}

main().catch((err) => {
  console.error(`💥 Fatal error: ${err.message}`);
  process.exit(1);
});
