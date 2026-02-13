#!/usr/bin/env node

/**
 * block.mjs — Block an ETH address on XMTP using consent state.
 *
 * Usage:
 *   node block.mjs <eth_address>
 *   node block.mjs --status <eth_address>
 */

import { createAgent } from "./lib/client.mjs";
import { IdentifierKind, ConsentState, ConsentEntityType } from "@xmtp/node-sdk";

const args = process.argv.slice(2);

function usage() {
  console.log(`
XMTP Block Tool

Usage:
  node block.mjs <eth_address>
  node block.mjs --status <eth_address>
`);
}

async function resolveInboxId(agent, address) {
  return agent.client.getInboxIdByIdentifier({
    identifier: address.toLowerCase(),
    identifierKind: IdentifierKind.Ethereum,
  });
}

async function main() {
  if (args.length === 0 || args[0] === "--help" || args[0] === "-h") {
    usage();
    process.exit(0);
  }

  const isStatus = args[0] === "--status";
  const target = isStatus ? args[1] : args[0];
  if (!target || !target.startsWith("0x")) {
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

  if (isStatus) {
    const state = await agent.client.preferences.getConsentState(
      ConsentEntityType.InboxId,
      inboxId,
    );
    console.log(JSON.stringify({
      address: target,
      inboxId,
      consentState: state,
      stateLabel: state === ConsentState.Denied ? "Denied" : state === ConsentState.Allowed ? "Allowed" : "Unknown",
    }));
    process.exit(0);
  }

  await agent.client.preferences.setConsentStates([
    {
      entityType: ConsentEntityType.InboxId,
      entity: inboxId,
      state: ConsentState.Denied,
    },
  ]);

  console.log(JSON.stringify({
    status: "blocked",
    address: target,
    inboxId,
    consentState: "Denied",
  }));
}

main().catch((err) => {
  console.error(`💥 Fatal error: ${err.message}`);
  process.exit(1);
});
