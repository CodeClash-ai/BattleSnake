#!/usr/bin/env python3
"""
Analysis helper for /logs/rounds/<round>/*.jsonl match logs.

Usage:
    python3 analyze_logs.py /logs/rounds/0

Each round directory contains:
  - results.json      : summary (winner, scores) for the round
  - sim_<N>.jsonl      : per-simulation turn-by-turn game state log.
    First line of each sim_*.jsonl is the "game" object; subsequent lines
    are full move-request payloads (game/turn/board/you) for each turn
    that was played.

This script prints:
  - the round's declared winner + score summary (from results.json)
  - per-simulation: which snake died first / survived longest, final turn count
  - aggregate win counts by snake name across all sim_*.jsonl in the folder
"""
import json
import sys
import glob
import os


def analyze_round(round_dir):
    results_path = os.path.join(round_dir, "results.json")
    if os.path.exists(results_path):
        with open(results_path) as f:
            results = json.load(f)
        print("=== results.json ===")
        print(json.dumps(results, indent=2))

    sim_files = sorted(glob.glob(os.path.join(round_dir, "sim_*.jsonl")))
    print(f"\n=== {len(sim_files)} simulation files ===")

    win_counts = {}
    turn_counts = []
    for sim_path in sim_files:
        with open(sim_path) as f:
            lines = [l for l in f if l.strip()]
        # Each sim_*.jsonl ends with a final summary line of the form
        # {"winnerId":..., "winnerName":..., "isDraw":...} -- this is the
        # authoritative result for the sim (added in round-2 analysis: the
        # previous version of this script inferred the winner from the
        # last turn's board.snakes list instead, which under-reports
        # heavily on rounds where most sim files only contain a single
        # "pre-game" line with no turns logged -- see README_agent.md).
        final_obj = None
        turns = []
        for l in lines:
            obj = json.loads(l)
            if "winnerId" in obj or "isDraw" in obj:
                final_obj = obj
            elif "board" in obj and "turn" in obj:
                turns.append(obj)
        if turns:
            turn_counts.append(turns[-1]["turn"])

        if final_obj is not None:
            if final_obj.get("isDraw"):
                win_counts["__draw__"] = win_counts.get("__draw__", 0) + 1
            else:
                winner = final_obj.get("winnerName") or "__unknown__"
                win_counts[winner] = win_counts.get(winner, 0) + 1
        elif turns:
            # No final summary line (older/incomplete log) -- fall back to
            # inferring from the last turn's alive snakes, as before.
            last = turns[-1]
            alive_names = [s["name"] for s in last["board"]["snakes"]]
            if len(alive_names) == 1:
                win_counts[alive_names[0]] = win_counts.get(alive_names[0], 0) + 1
            elif len(alive_names) == 0:
                win_counts["__draw__"] = win_counts.get("__draw__", 0) + 1
            else:
                win_counts["__unfinished_or_tie__"] = win_counts.get("__unfinished_or_tie__", 0) + 1

    print("\nWin counts by snake name (based on last surviving snake per sim):")
    for name, cnt in sorted(win_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {name}: {cnt}")
    if turn_counts:
        print(f"\nAvg turns per sim: {sum(turn_counts)/len(turn_counts):.1f}  "
              f"(min={min(turn_counts)}, max={max(turn_counts)})")


if __name__ == "__main__":
    round_dir = sys.argv[1] if len(sys.argv) > 1 else "/logs/rounds/0"
    analyze_round(round_dir)
