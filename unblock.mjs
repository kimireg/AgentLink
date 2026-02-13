#!/usr/bin/env node

/**
 * unblock.mjs — Unblock an ETH address on XMTP using consent state.
 *
 * Usage:
 *   node unblock.mjs <eth_address>
 */

import { createAgent } from "./lib/client.mjs";
import { IdentifierKind, ConsentState, ConsentEntityType } from "@xmtp/node-sdk";

const args = process.argv.slice(2);

async function resolveInboxId(agent, address) {
  return agent.client.getInboxIdByIdentifier({
    identifier: address.toLowerCase(),
    identifierKind: IdentifierKind.Ethereum,
  });
}

async function main() {
  const target = args[0];
  if (!target || target === "--help" || target === "-h") {
    console.log(`\nUsage: node unblock.mjs <eth_address>\n`);
    process.exit(target ? 0 : 1);
  }

  if (!target.startsWith("0x")) {
    console.error("❌ Address must start with 0x");
    process.exit(1);
  }

  const agent = await createAgent();
  const inboxId = await resolveInboxId(agent, target);

  if (!inboxId) {
    console.log(JSON.stringify({
      address: target,
      status: "not_found",
      note: "Address not found on XMTP",
    }));
    process.exit(0);
  }

  await agent.client.preferences.setConsentStates([
    {
      entityType: ConsentEntityType.InboxId,
      entity: inboxId,
      state: ConsentState.Allowed,
    },
  ]);

  console.log(JSON.stringify({
    status: "unblocked",
    address: target,
    inboxId,
    consentState: "Allowed",
  }));
}

main().catch((err) => {
  console.error(`💥 Fatal error: ${err.message}`);
  process.exit(1);
});
