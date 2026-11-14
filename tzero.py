#!/usr/bin/env python3
"""Tzero testnet helper.

Read-only helper for the Tzero testnet (Base Sepolia):
  - points:     total points, Fuel, Crew, Liftoff, Signal, rank, eligibility
  - balance:    Base Sepolia ETH balance of any wallet
  - missions:   missions closest to liftoff (progress 40-65%, not graduated)
  - leaderboard: top wallets by points (API caps at 100 rows)

No secrets, no private keys, no API keys. The wallet address is always
passed as a command-line argument, never stored in this repo.

Usage:
  python3 tzero.py points <WALLET_ADDRESS>
  python3 tzero.py balance <WALLET_ADDRESS>
  python3 tzero.py missions [--limit N] [--min-bps N] [--max-bps N]
  python3 tzero.py leaderboard [--limit N]

Requires Python 3.8+. No third-party dependencies (stdlib only).
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

API_BASE = "https://testnet.tzer0.fun/api"
RPC_URL = "https://sepolia.base.org"
USER_AGENT = "tzero-testnet-helper/1.0"


def get_json(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        print(f"API error: HTTP {e.code} for {url}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason} for {url}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"API error: invalid JSON from {url}", file=sys.stderr)
        sys.exit(1)


def rpc_call(method, params, timeout=25):
    payload = json.dumps(
        {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    ).encode()
    req = urllib.request.Request(
        RPC_URL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        print(f"RPC error: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def cmd_points(wallet):
    data = get_json(f"{API_BASE}/points/{wallet}")
    if data.get("status") == "warming":
        print("Points API is warming up, retry in a minute.")
        return
    print(f"Wallet:     {data.get('address', wallet)}")
    print(f"Season:     {data.get('season')}")
    print(f"Total:      {data.get('total')}")
    print(f"  Fuel:     {data.get('fuel')}")
    print(f"  Crew:     {data.get('crew')}")
    print(f"  Liftoff:  {data.get('liftoff')}")
    print(f"  Signal:   {data.get('signal')}")
    print(f"Rank:       {data.get('rank')} / {data.get('rankedWallets')}")
    print(f"Eligible:   {data.get('eligible')} (threshold {data.get('threshold')})")


def cmd_balance(wallet):
    res = rpc_call("eth_getBalance", [wallet, "latest"])
    wei = int(res.get("result", "0x0"), 16)
    print(f"Wallet:          {wallet}")
    print(f"Base Sepolia:    {wei / 1e18:.6f} ETH")


def cmd_missions(limit, min_bps, max_bps):
    data = get_json(f"{API_BASE}/missions?limit=200")
    missions = data if isinstance(data, list) else data.get("missions", [])
    # Prefer missions not yet graduated, closest to liftoff.
    pool = [
        m
        for m in missions
        if not m.get("graduated")
        and min_bps <= (m.get("progressBps") or 0) <= max_bps
    ]
    pool.sort(key=lambda m: m.get("progressBps") or 0, reverse=True)
    print(f"Showing {min(len(pool), limit)} of {len(pool)} matching missions "
          f"(progress {min_bps / 100:.0f}%-{max_bps / 100:.0f}%, not graduated):")
    print(f"{'ID':>6}  {'SYMBOL':<10} {'PROGRESS':>9}  {'HOLDERS':>7}  TOKEN")
    for m in pool[:limit]:
        bps = m.get("progressBps") or 0
        print(f"{m.get('id', '?'):>6}  {str(m.get('symbol', '?')):<10} "
              f"{bps / 100:>8.2f}%  {m.get('holders', '?'):>7}  {m.get('token', '?')}")
    print("\nNote: the missions API can be stale. Always verify progress "
          "on-chain (progressBps) right before buying.")


def cmd_leaderboard(limit):
    data = get_json(f"{API_BASE}/points/leaderboard?limit=100")
    rows = data if isinstance(data, list) else data.get("leaderboard", [])
    if not rows:
        print("Leaderboard returned no rows (API may be warming up). "
              "Retry in a minute.")
        return
    print(f"Top {min(len(rows), limit)} wallets (API caps at 100 rows):")
    print(f"{'RANK':>5}  {'TOTAL':>10}  WALLET")
    for i, r in enumerate(rows[:limit], start=1):
        wallet = r.get("address") or r.get("wallet") or "?"
        total = r.get("total") or r.get("points") or "?"
        print(f"{i:>5}  {str(total):>10}  {wallet}")


def main():
    parser = argparse.ArgumentParser(
        description="Tzero testnet helper (read-only, Base Sepolia)."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("points", help="show points, rank and eligibility")
    p.add_argument("wallet", help="wallet address (0x...)")

    b = sub.add_parser("balance", help="show Base Sepolia ETH balance")
    b.add_argument("wallet", help="wallet address (0x...)")

    m = sub.add_parser("missions", help="list missions closest to liftoff")
    m.add_argument("--limit", type=int, default=10)
    m.add_argument("--min-bps", type=int, default=4000,
                   help="min progress in bps (4000 = 40%%)")
    m.add_argument("--max-bps", type=int, default=6500,
                   help="max progress in bps (6500 = 65%%)")

    l = sub.add_parser("leaderboard", help="show top wallets by points")
    l.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()
    if args.cmd == "points":
        cmd_points(args.wallet)
    elif args.cmd == "balance":
        cmd_balance(args.wallet)
    elif args.cmd == "missions":
        cmd_missions(args.limit, args.min_bps, args.max_bps)
    elif args.cmd == "leaderboard":
        cmd_leaderboard(args.limit)


if __name__ == "__main__":
    main()
