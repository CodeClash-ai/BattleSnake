"""Quick local batch against tools/vulture_snake_opponent.py.

Usage: N=50 python tools/eval_vulture.py
Large batches can exceed the 30s command timeout because Vulture games may run
long and the opponent has stateful/random fallback behavior.
"""
import collections
import json
import os
import subprocess
import time

N = int(os.environ.get("N", "50"))
ME = "gpt-5-5"
OPP = "Spenca__vulture-snake"

me = subprocess.Popen(["python3", "main.py"], cwd="/workspace", env=dict(os.environ, PORT="8000"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
opp = subprocess.Popen(["python3", "tools/vulture_snake_opponent.py"], cwd="/workspace", env=dict(os.environ, PORT="8001"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ctr = collections.Counter(); turns = []; bad = []
try:
    for seed in range(N):
        out = f"/tmp/vulture_{seed}.jsonl"
        try:
            subprocess.run(["./game/battlesnake", "play", "-W", "11", "-H", "11", "-n", ME, "-u", "http://127.0.0.1:8000", "-n", OPP, "-u", "http://127.0.0.1:8001", "-r", str(seed), "-o", out], cwd="/workspace", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            states = [json.loads(line) for line in open(out) if '"turn"' in line]
            last = states[-1]
            alive = {s["name"] for s in last["board"]["snakes"]}
            if ME in alive and OPP not in alive: res = "win"
            elif OPP in alive and ME not in alive: res = "loss"; bad.append((seed, last["turn"]))
            elif OPP not in alive and ME not in alive: res = "tie"; bad.append((seed, last["turn"]))
            else: res = "both"; bad.append((seed, last["turn"]))
            ctr[res] += 1; turns.append(last["turn"])
        except Exception as e:
            ctr["err"] += 1; bad.append((seed, str(e)))
    print(ctr, "avgturn", (sum(turns) / len(turns) if turns else None), "bad", bad[:20])
finally:
    for p in (me, opp):
        p.terminate()
    for p in (me, opp):
        try:
            p.wait(timeout=2)
        except Exception:
            p.kill()
