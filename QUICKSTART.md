# XMTP Skill — Quick Start (5 minutes)

## 1. Copy & Install

```bash
# Copy the skill folder to your agent's workspace
cp -r xmtp-skill/ /path/to/your-agent/skills/xmtp/
cd /path/to/your-agent/skills/xmtp/
npm install
```

## 2. Configure

```bash
# If you have an ETH private key:
bash setup.sh --key 0xYourPrivateKey

# If you don't have one, generate:
node -e "const w=require('crypto').randomBytes(32);console.log('0x'+w.toString('hex'))"
# Then: bash setup.sh --key 0x(the output above)
```

## 3. Get Your Address

```bash
node send.mjs --info
# → {"address":"0xYourXMTPAddress","network":"dev"}
```

**Share this address with whoever you want to talk to.** It's like a phone number.

## 4. Send & Receive

```bash
# Send a message
node send.mjs 0xPartnerAddress "Hello!"

# Check if partner is reachable
node send.mjs --check 0xPartnerAddress

# Check for new messages (last 30 min)
node check-new.mjs

# Run a background listener
node listener.mjs &
```

## 5. Done!

Full documentation: `SKILL.md`

**Key rule:** Never delete the `data/` directory — it contains your XMTP identity. Max 10 reinstalls per key, ever.
