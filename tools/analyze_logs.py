#!/usr/bin/env python3
"""Analyze /logs/rounds/N/ match logs: win/loss/draw counts and turn stats.

Usage:
    python3 tools/analyze_logs.py [round_num ...]

If no round numbers given, analyzes all rounds found under /logs/rounds/.

For each round, reads results.json (if present) and all sim_*.jsonl files.
Each sim_*.jsonl file is a sequence of JSON lines representing game state
snapshots per turn, with the final line (if the game actually completed)
being a summary object like:
    {"winnerId": "...", "winnerName": "...", "isDraw": false}
Empty files are skipped (seen in round 0 -- looks like harness artifacts
for unused sim slots, not real games).
"""
import json
import os
import sys

LOGS_DIR = "/logs/rounds"


def analyze_round(round_dir, my_name_hint="sonnet-5"):
    results_path = os.path.join(round_dir, "results.json")
    results = None
    if os.path.exists(results_path):
        with open(results_path) as f:
            results = json.load(f)

    sim_files = sorted(
        f for f in os.listdir(round_dir) if f.startswith("sim_") and f.endswith(".jsonl")
    )

    empty = 0
    win = 0
    loss = 0
    draw = 0
    unknown = 0
    turn_counts = []
    winners = {}

    for fname in sim_files:
        path = os.path.join(round_dir, fname)
        if os.path.getsize(path) == 0:
            empty += 1
            continue
        with open(path) as f:
            lines = [l for l in f if l.strip()]
        if not lines:
            empty += 1
            continue
        # Turn count: count lines that have a "turn" field (state snapshots).
        n_turns = sum(1 for l in lines if '"turn"' in l)
        turn_counts.append(n_turns)

        last = lines[-1]
        try:
            summary = json.loads(last)
        except Exception:
            unknown += 1
            continue

        if "isDraw" in summary or "winnerName" in summary:
            if summary.get("isDraw"):
                draw += 1
            else:
                wname = summary.get("winnerName", "")
                winners[wname] = winners.get(wname, 0) + 1
                if my_name_hint in wname:
                    win += 1
                else:
                    loss += 1
        else:
            unknown += 1

    print(f"=== Round dir: {round_dir} ===")
    if results:
        print(f"  results.json winner: {results.get('winner')}")
        print(f"  results.json scores: {results.get('scores')}")
    print(f"  sim files: {len(sim_files)} total, {empty} empty, "
          f"{len(sim_files) - empty} real games")
    print(f"  win={win} loss={loss} draw={draw} unknown={unknown}")
    print(f"  winners breakdown: {winners}")
    if turn_counts:
        print(f"  turn counts: min={min(turn_counts)} max={max(turn_counts)} "
              f"avg={sum(turn_counts) / len(turn_counts):.1f}")
    print()


def main():
    args = sys.argv[1:]
    if not os.path.isdir(LOGS_DIR):
        print(f"No logs dir found at {LOGS_DIR}")
        return
    if args:
        round_dirs = [os.path.join(LOGS_DIR, r) for r in args]
    else:
        round_dirs = sorted(
            os.path.join(LOGS_DIR, d) for d in os.listdir(LOGS_DIR)
            if os.path.isdir(os.path.join(LOGS_DIR, d))
        )
    for rd in round_dirs:
        if os.path.isdir(rd):
            analyze_round(rd)
        else:
            print(f"Skipping missing round dir: {rd}")


if __name__ == "__main__":
    main()
