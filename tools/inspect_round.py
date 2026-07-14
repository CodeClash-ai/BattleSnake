#!/usr/bin/env python3
"""Print an easy-to-read sample game from a saved round directory.

Usage: python3 tools/inspect_round.py /logs/rounds/1 [max-turns]
"""
import glob
import json
import os
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "/logs/rounds/1"
max_turns = int(sys.argv[2]) if len(sys.argv) > 2 else 12

for path in sorted(glob.glob(os.path.join(root, "sim_*.jsonl"))):
    if os.path.getsize(path) == 0:
        continue
    states = []
    winner = None
    with open(path) as fh:
        for line in fh:
            obj = json.loads(line)
            if "turn" in obj:
                states.append(obj)
            elif "winnerName" in obj:
                winner = obj
    if not states:
        continue
    print(f"\n{os.path.basename(path)} turns={states[-1]['turn']} winner={winner}")
    for st in states[:max_turns]:
        print("turn", st["turn"], "food", st["board"].get("food"))
        for sn in st["board"].get("snakes", []):
            print(" ", sn.get("name"), "health", sn.get("health"), "len", sn.get("length"), "head", sn.get("head"), "body", sn.get("body", [])[:3])
    break
else:
    print(f"No non-empty sim_*.jsonl files found in {root}")
