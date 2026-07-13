"""Small local batch evaluator against tools/amphibious_arthur_opponent.py.

Usage: N=30 python tools/eval_amphibious_arthur.py
"""
import collections
import json
import os
import subprocess
import time

N = int(os.environ.get("N", "30"))
ME_NAME = "gpt-5-5"
OPP_NAME = "coreyja__amphibious-arthur"

me = subprocess.Popen(["python3", "main.py"], cwd="/workspace", env=dict(os.environ, PORT="8000"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
opp = subprocess.Popen(["python3", "tools/amphibious_arthur_opponent.py"], cwd="/workspace", env=dict(os.environ, PORT="8001"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ctr = collections.Counter()
turns = []
try:
    for seed in range(N):
        out = f"/tmp/amphibious_arthur_{seed}.jsonl"
        subprocess.run([
            "./game/battlesnake", "play", "-W", "11", "-H", "11",
            "-n", ME_NAME, "-u", "http://127.0.0.1:8000",
            "-n", OPP_NAME, "-u", "http://127.0.0.1:8001",
            "-r", str(seed), "-o", out,
        ], cwd="/workspace", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
        states = [json.loads(line) for line in open(out) if '"turn"' in line]
        if not states:
            ctr["no_state"] += 1
            continue
        last = states[-1]
        alive = [s["name"] for s in last["board"]["snakes"]]
        if ME_NAME in alive and OPP_NAME not in alive:
            res = "win"
        elif OPP_NAME in alive and ME_NAME not in alive:
            res = "loss"
        elif OPP_NAME not in alive and ME_NAME not in alive:
            res = "tie"
        else:
            res = "both_alive"
        ctr[res] += 1
        turns.append(last["turn"])
    avg = (sum(turns) / len(turns)) if turns else 0
    print(ctr, "avgturn", avg, "max", max(turns) if turns else None)
finally:
    me.terminate(); opp.terminate()
    try:
        me.wait(timeout=2); opp.wait(timeout=2)
    except Exception:
        pass
