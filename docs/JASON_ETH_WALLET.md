# Jason ETH Wallet (Mainnet)

## What was created
- Wallet type: Foundry keystore (encrypted JSON), managed via `cast`
- Chain: Ethereum mainnet
- RPC (current): https://ethereum.publicnode.com

## Address (public)
- `0x1181A37Bf11896Cc678f0B81412760133814238a`

## Where secrets live
- **Keystore file (encrypted):** `~/.openclaw/wallets/jason-eth/keystore/jason-eth`
- **Keystore password:** stored in **macOS Keychain**
  - service: `eth.jason.keystore.pass`
  - account: `jason`

### Recovery warning (important)
File backups include the keystore file, but **do not include macOS Keychain items**.
If the machine is wiped and the Keychain item is lost, the keystore cannot be decrypted and funds could be stuck.

Recommended: keep a sealed offline copy of the keystore password, or store an encrypted escrow copy (encrypted with a Kimi-controlled passphrase) alongside backups.

## Escrow (encrypted password) — implemented
- File: `~/.openclaw/wallets/jason-eth/escrow.enc`
- Create/update escrow:
  - `/Users/kimi/.openclaw/workspace/scripts/jason_eth_escrow_init.sh`
- Decrypt escrow during recovery (prints password to stdout):
  - `/Users/kimi/.openclaw/workspace/scripts/jason_eth_escrow_decrypt.sh`

Security model:
- Escrow contains ONLY the keystore password, encrypted with a passphrase Kimi controls.
- Passphrase is never stored by Jason; without it, the escrow is useless.

> Never paste the private key anywhere. The keystore password should also never be printed.

## Helper scripts
- Balance:
  - `/Users/kimi/.openclaw/workspace/scripts/jason_eth_balance.sh`
- Send (broadcasts to mainnet):
  - `/Users/kimi/.openclaw/workspace/scripts/jason_eth_send.sh <to> <value>`
  - Example: `/Users/kimi/.openclaw/workspace/scripts/jason_eth_send.sh 0xabc... 0.0001ether`

## Notes
- Cloudflare RPC (`https://cloudflare-eth.com`) currently returns `-32603 Internal error` for balance calls; switched to `https://ethereum.publicnode.com`.
- For safety, we should implement an approval gate before allowing any automatic sends.
