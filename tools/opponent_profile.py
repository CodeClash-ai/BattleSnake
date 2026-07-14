#!/usr/bin/env python3
"""Summarize observed opponent movement in saved Battlesnake jsonl logs.

Usage: python3 tools/opponent_profile.py /logs/rounds/1 [our-name]
"""
import collections
import glob
import json
import os
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "/logs/rounds/1"
our_name = sys.argv[2] if len(sys.argv) > 2 else "gpt-5-5"
turn_dirs = collections.Counter()
starts = collections.Counter()
lengths = []
winners = collections.Counter()

for path in glob.glob(os.path.join(root, "sim_*.jsonl")):
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
                winner = obj.get("winnerName")
    if not states:
        continue
    if winner:
        winners[winner] += 1
    prev = None
    for st in states:
        opps = [s for s in st["board"].get("snakes", []) if s.get("name") != our_name]
        if not opps:
            continue
        opp = opps[0]
        head = (opp["head"]["x"], opp["head"]["y"])
        if st["turn"] == 0:
            starts[head] += 1
        if prev is not None:
            turn_dirs[(head[0] - prev[0], head[1] - prev[1])] += 1
        prev = head
    lengths.append(states[-1]["turn"])

print(f"games={len(lengths)} root={root}")
if lengths:
    print(f"turn avg/min/max={sum(lengths)/len(lengths):.2f}/{min(lengths)}/{max(lengths)}")
print("winners", winners)
print("starts", starts)
print("opponent head deltas", turn_dirs)
