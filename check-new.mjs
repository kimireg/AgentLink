#!/usr/bin/env node

/**
 * check-new.mjs — One-shot XMTP new message checker
 * 
 * Designed for cron jobs or heartbeat integration.
 * Syncs conversations, checks for unread messages, outputs summary, exits.
 * 
 * Usage:
 *   node check-new.mjs              Check for new messages
 *   node check-new.mjs --since 60   Check messages from last 60 minutes (default: 30)
 * 
 * Output:
 *   {"unread":2,"messages":[...]}    If new messages found
 *   {"unread":0,"messages":[]}       If no new messages
 * 
 * Exit codes:
 *   0 - Success (regardless of message count)
 *   1 - Error
 */

import { createAgent } from "./lib/client.mjs";

const args = process.argv.slice(2);
const sinceIdx = args.indexOf("--since");
const sinceMinutes = sinceIdx !== -1 ? parseInt(args[sinceIdx + 1]) || 30 : 30;

async function main() {
  const agent = await createAgent();
  
  // Sync all conversations from network
  await agent.client.conversations.sync();
  
  const conversations = await agent.client.conversations.list();
  const cutoff = Date.now() - (sinceMinutes * 60 * 1000);
  const cutoffNs = BigInt(cutoff) * 1000000n;
  
  const newMessages = [];
  
  for (const conv of conversations) {
    try {
      await conv.sync();
      const messages = await conv.messages({ limit: 10 });
      
      for (const msg of messages) {
        // Skip messages from self
        if (msg.senderInboxId === agent.client.inboxId) continue;
        
        // Check if message is within time window
        if (msg.sentAtNs && msg.sentAtNs > cutoffNs) {
          let senderAddress = msg.senderInboxId;
          try {
            const state = await agent.client.preferences.inboxStateFromInboxIds([msg.senderInboxId]);
            if (state?.[0]?.identifiers?.[0]?.identifier) {
              senderAddress = state[0].identifiers[0].identifier;
            }
          } catch { /* use inboxId as fallback */ }
          
          newMessages.push({
            from: senderAddress,
            content: typeof msg.content === 'string' 
              ? (msg.content.length > 200 ? msg.content.slice(0, 200) + "..." : msg.content)
              : "[non-text content]",
            conversationId: conv.id,
            sentAt: new Date(Number(msg.sentAtNs / 1000000n)).toISOString(),
          });
        }
      }
    } catch {
      // Skip conversations that fail to sync
    }
  }
  
  // Sort by time, newest first
  newMessages.sort((a, b) => b.sentAt.localeCompare(a.sentAt));
  
  console.log(JSON.stringify({
    agent_address: agent.address,
    checked_at: new Date().toISOString(),
    since_minutes: sinceMinutes,
    unread: newMessages.length,
    messages: newMessages,
  }, null, 2));

  process.exit(0);
}

main().catch((err) => {
  console.error(`💥 Fatal error: ${err.message}`);
  process.exit(1);
});
