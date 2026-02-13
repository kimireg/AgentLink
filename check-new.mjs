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

function safeStringify(value) {
  return JSON.stringify(value, (_, v) =>
    typeof v === "bigint" ? v.toString() : v
  );
}

function nsToMs(ns) {
  if (ns === null || ns === undefined) return 0;
  if (typeof ns === "bigint") return Number(ns / 1000000n);
  if (typeof ns === "number") return Math.floor(ns / 1_000_000);
  const parsed = Number(ns.toString());
  return Number.isFinite(parsed) ? Math.floor(parsed / 1_000_000) : 0;
}

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
          try {
            // Skip our own messages only if inboxId is available
            if (agent.inboxId && msg.senderInboxId === agent.inboxId) continue;

            // Check timestamp
            const sentAt = nsToMs(msg.sentAtNs);
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
                  : safeStringify(msg.content),
              conversationId: conv.id,
              timestamp: sentAt
                ? new Date(sentAt).toISOString()
                : null,
            });
          } catch {
            // Skip malformed message only, keep other messages
            continue;
          }
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
      safeStringify({
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
