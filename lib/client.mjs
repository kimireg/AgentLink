/**
 * lib/client.mjs — Shared XMTP Agent initialization
 * 
 * Creates an XMTP Agent instance from environment variables.
 * Used by all skill scripts (send, listen, history, check).
 * 
 * Required env vars (in .env):
 *   XMTP_WALLET_KEY       - ETH private key (0x...)
 *   XMTP_DB_ENCRYPTION_KEY - DB encryption key (64 hex chars, no 0x prefix)
 *   XMTP_ENV              - Network: dev | production
 *   XMTP_DB_PATH          - Local DB path (default: ./data/xmtp-db)
 */

import { Agent } from "@xmtp/agent-sdk";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, "..");

/**
 * Load .env file manually
 */
function loadEnv() {
  const envPath = resolve(SKILL_DIR, ".env");
  if (!existsSync(envPath)) {
    console.error(`❌ Missing .env file at ${envPath}`);
    console.error(`   Copy .env.example to .env and fill in your values.`);
    process.exit(1);
  }

  // Manual parsing (more reliable than process.loadEnvFile)
  const content = readFileSync(envPath, "utf-8");
  for (const line of content.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eqIdx = trimmed.indexOf("=");
    if (eqIdx === -1) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    const val = trimmed.slice(eqIdx + 1).trim();
    if (key && !process.env[key]) {
      process.env[key] = val;
    }
  }
}

/**
 * Ensure the data directory exists for XMTP local database
 */
function ensureDataDir() {
  const dbPath = process.env.XMTP_DB_PATH || "./data/xmtp-db";
  const fullPath = resolve(SKILL_DIR, dbPath);
  const dir = dirname(fullPath);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
  return fullPath;
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

  if (!process.env.XMTP_ENV) {
    process.env.XMTP_ENV = "dev";
  }
}

/**
 * Create and return an XMTP Agent instance.
 * Does NOT call agent.start() — caller decides whether to listen or just send.
 * 
 * @returns {Promise<Agent>} Initialized XMTP Agent
 */
export async function createAgent() {
  loadEnv();
  validateEnv();
  const dbPath = ensureDataDir();

  // Set dbPath in env for Agent.createFromEnv()
  process.env.XMTP_DB_PATH = dbPath;

  const agent = await Agent.createFromEnv();
  return agent;
}

/**
 * Get the skill directory path
 */
export function getSkillDir() {
  return SKILL_DIR;
}
