#!/usr/bin/env python3
"""Summarize Battlesnake JSONL logs.

Usage: python analyze_logs.py /logs/rounds/0 [our-snake-name]
Defaults to /logs/rounds/0 and gpt-5-5.  Opponents are inferred from each
simulation instead of being hard-coded, so this remains useful in later rounds.
"""
import collections
import glob
import json
import os
import sys

LOGDIR = sys.argv[1] if len(sys.argv) > 1 else "/logs/rounds/0"
NAME = sys.argv[2] if len(sys.argv) > 2 else "gpt-5-5"

def sim_key(path):
    base = os.path.basename(path)
    try:
        return int(base.split("_")[1].split(".")[0])
    except Exception:
        return base

ctr = collections.Counter()
turns = []
starts = collections.Counter()
deaths = []
opponents = collections.Counter()

for path in sorted(glob.glob(os.path.join(LOGDIR, "sim_*.jsonl")), key=sim_key):
    states = []
    for line in open(path):
        obj = json.loads(line)
        if "turn" in obj:
            states.append(obj)
    if not states:
        continue

    initial_names = {s["name"] for s in states[0]["board"].get("snakes", [])}
    for n in initial_names - {NAME}:
        opponents[n] += 1

    last = states[-1]
    alive = {s["name"] for s in last["board"].get("snakes", [])}
    enemy_alive = bool(alive - {NAME})
    if NAME in alive and not enemy_alive:
        res = "win"
    elif NAME not in alive and enemy_alive:
        res = "loss"
    elif NAME not in alive and not enemy_alive:
        res = "tie"
    else:
        res = "both_alive"
    ctr[res] += 1
    turns.append(last["turn"])

    s0 = states[0]["board"]
    starts[tuple((sn["name"], sn["head"]["x"], sn["head"]["y"]) for sn in s0.get("snakes", []))] += 1

    if len(states) >= 2:
        prev = states[-2]
        prev_alive = {sn["name"]: sn for sn in prev["board"].get("snakes", [])}
        last_alive = {sn["name"]: sn for sn in last["board"].get("snakes", [])}
        for n, sn in prev_alive.items():
            if n not in last_alive:
                deaths.append((res, os.path.basename(path), last["turn"], n, sn["head"], sn["length"], sn["health"]))

print("logdir", LOGDIR, "us", NAME, "opponents", dict(opponents))
if turns:
    print("results", ctr, "n", sum(ctr.values()), "avgturn", sum(turns) / len(turns), "max", max(turns), "min", min(turns))
else:
    print("no sim_*.jsonl states found")
print("starts top")
for k, v in starts.most_common(10):
    print(v, k)
print("sample deaths")
for d in deaths[:20]:
    print(d)
print("death res/name counter", collections.Counter((res, n) for res, _, _, n, _, _, _ in deaths))
