# tzero-testnet-helper

Read-only helper for the [Tzero](https://testnet.tzer0.fun) testnet (Base Sepolia).
Check your points, wallet balance, missions near liftoff, and the leaderboard —
without opening the website.

## Install

Python 3.8+ only. No third-party dependencies.

```bash
git clone https://github.com/jesshqi/tzero-testnet-helper.git
cd tzero-testnet-helper
```

## Usage

Replace `<WALLET_ADDRESS>` with your own wallet address (0x...).

```bash
# Points, Fuel, Crew, Liftoff, Signal, rank, eligibility
python3 tzero.py points <WALLET_ADDRESS>

# Base Sepolia ETH balance
python3 tzero.py balance <WALLET_ADDRESS>

# Missions closest to liftoff (default: 40-65% progress, not graduated)
python3 tzero.py missions
python3 tzero.py missions --limit 5 --min-bps 5000 --max-bps 7000

# Top wallets by points (the API caps at 100 rows)
python3 tzero.py leaderboard
python3 tzero.py leaderboard --limit 20
```

## How points work (Season 0)

- **Fuel:** 1,000 pts per 1 ETH bought, counted after a 60-minute hold.
  Buys below 0.0005 ETH are not counted.
- **Crew:** +150 pts per mission that liftoffs, if you bought at least
  0.01 ETH before liftoff and still hold at liftoff (max 5/day).
- **Liftoff:** +500 pts per self-launched mission that liftoffs with
  at least 5 other wallets backing 0.01 ETH each.
- **Signal:** +200 for an X reply/quote, +100 for following @T0dotfun.
- Eligible from 500 points. No end date announced for Season 0.

## Safety

- This tool is **read-only**: it only calls public APIs and a public RPC.
  It never signs, sends, or spends anything.
- It contains **no private keys, seed phrases, or API keys**.
- Your wallet address is a command-line argument — it is never stored
  in this repo.

## Caveats

- The missions API can be **stale** (wrong addresses, already-liftoffed
  missions still showing ~50-60%). Always verify a mission's progress
  on-chain (`progressBps`) right before buying.
- The points API sometimes returns HTTP 502 or an empty response —
  just retry.
- The leaderboard API is hard-capped at 100 rows.
