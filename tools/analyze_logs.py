#!/usr/bin/env python3
"""Summarize Battlesnake jsonl match logs.

Usage:
    python3 tools/analyze_logs.py /logs/rounds/0
"""
import collections
import glob
import json
import os
import sys

paths = []
for arg in (sys.argv[1:] or ["/logs/rounds/0"]):
    if os.path.isdir(arg):
        paths.extend(glob.glob(os.path.join(arg, "*.jsonl")))
    else:
        paths.extend(glob.glob(arg))

wins = collections.Counter()
turns = []
examples = {}
empty = 0
for path in sorted(paths):
    try:
        lines = open(path, encoding="utf-8").read().strip().splitlines()
        if not lines:
            empty += 1
            continue
        result = json.loads(lines[-1])
        name = result.get("winnerName") or ("DRAW" if result.get("isDraw") else "UNKNOWN")
        wins[name] += 1
        examples.setdefault(name, path)
        if len(lines) >= 2:
            turns.append(json.loads(lines[-2]).get("turn", 0))
    except Exception as exc:
        wins[f"ERROR:{type(exc).__name__}"] += 1
        examples.setdefault(f"ERROR:{type(exc).__name__}", path)

print(f"files: {len(paths)} (non-empty={sum(wins.values())}, empty={empty})")
print("wins:")
for name, count in wins.most_common():
    print(f"  {name!r}: {count}  example={examples.get(name)}")
if turns:
    print(f"last-state turn: avg={sum(turns)/len(turns):.2f} min={min(turns)} max={max(turns)}")
