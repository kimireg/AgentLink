/**
 * lib/client.mjs — Shared XMTP Agent initialization (v2)
 *
 * Creates an XMTP Agent instance from environment variables.
 * Uses @xmtp/agent-sdk (official Agent SDK), NOT @xmtp/node-sdk.
 *
 * Required env vars (in .env):
 *   XMTP_WALLET_KEY          - ETH private key (0x...)
 *   XMTP_DB_ENCRYPTION_KEY   - DB encryption key (0x..., 64 hex chars)
 *   XMTP_ENV                 - Network: dev | production (default: dev)
 */

import { Agent } from "@xmtp/agent-sdk";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, "..");

/**
 * Load .env file from skill directory.
 * Node 22 LTS has native process.loadEnvFile().
 */
function loadEnv() {
  const envPath = resolve(SKILL_DIR, ".env");
  if (!existsSync(envPath)) {
    console.error(`❌ Missing .env file at ${envPath}`);
    console.error(`   Copy .env.example to .env and fill in your values.`);
    process.exit(1);
  }

  // Node 22+ has native .env loading
  if (typeof process.loadEnvFile === "function") {
    process.loadEnvFile(envPath);
  } else {
    // Fallback: manual parsing for older Node
    const content = readFileSync(envPath, "utf-8");
    for (const line of content.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eqIdx = trimmed.indexOf("=");
      if (eqIdx === -1) continue;
      const key = trimmed.slice(0, eqIdx).trim();
      const val = trimmed.slice(eqIdx + 1).trim();
      if (!process.env[key]) {
        process.env[key] = val;
      }
    }
  }
}

/**
 * Validate required environment variables
 */
function validateEnv() {
  const required = ["XMTP_WALLET_KEY", "XMTP_DB_ENCRYPTION_KEY"];
  const missing = required.filter((k) => !process.env[k]);
  if (missing.length > 0) {
    console.error(`❌ Missing required env vars: ${missing.join(", ")}`);
    console.error(`   Edit your .env file in ${SKILL_DIR}`);
    process.exit(1);
  }

  // Default to dev network
  if (!process.env.XMTP_ENV) {
    process.env.XMTP_ENV = "dev";
  }
}

/**
 * Ensure data directory exists for DB persistence
 */
function ensureDataDir() {
  const dataDir = resolve(SKILL_DIR, "data");
  if (!existsSync(dataDir)) {
    mkdirSync(dataDir, { recursive: true });
  }
}

/**
 * Check Node.js version meets requirements (22 LTS, not 25+)
 */
function checkNodeVersion() {
  const major = parseInt(process.versions.node.split(".")[0], 10);
  if (major >= 25) {
    console.error(`⚠️  Node.js v${process.versions.node} detected.`);
    console.error(`   XMTP requires Node 22 LTS. Node 25+ has TLS compatibility issues.`);
    console.error(`   Fix: nvm use 22`);
    // Don't exit — let the user try, but warn loudly
  } else if (major < 22) {
    console.error(`⚠️  Node.js v${process.versions.node} detected. XMTP Agent SDK requires Node >= 22.`);
    console.error(`   Fix: nvm install 22 && nvm use 22`);
  }
}

/**
 * Create and return an XMTP Agent instance.
 * Does NOT call agent.start() — caller decides whether to listen or just send.
 *
 * @returns {Promise<import("@xmtp/agent-sdk").Agent>} Initialized XMTP Agent
 */
export async function createAgent() {
  checkNodeVersion();
  loadEnv();
  validateEnv();
  ensureDataDir();

  // Agent.createFromEnv() reads XMTP_WALLET_KEY, XMTP_DB_ENCRYPTION_KEY, XMTP_ENV
  // Database defaults to current directory (./)
  const agent = await Agent.createFromEnv();

  return agent;
}

/**
 * Get the skill directory path
 */
export function getSkillDir() {
  return SKILL_DIR;
}
