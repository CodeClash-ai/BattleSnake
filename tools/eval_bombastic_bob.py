"""Quick local batch runner against tools/bombastic_bob_opponent.py.

Usage: N=100 python tools/eval_bombastic_bob.py
"""
import collections
import json
import os
import subprocess
import time

N = int(os.environ.get("N", "50"))
me = subprocess.Popen(["python3", "main.py"], cwd="/workspace", env=dict(os.environ, PORT="8000"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
opp = subprocess.Popen(["python3", "tools/bombastic_bob_opponent.py"], cwd="/workspace", env=dict(os.environ, PORT="8001"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ctr = collections.Counter()
turns = []
bad = []
try:
    for seed in range(N):
        out = f"/tmp/bob_{seed}.jsonl"
        try:
            subprocess.run([
                "./game/battlesnake", "play", "-W", "11", "-H", "11",
                "-n", "gpt-5-5", "-u", "http://127.0.0.1:8000",
                "-n", "coreyja__bombastic-bob", "-u", "http://127.0.0.1:8001",
                "-r", str(seed), "-o", out,
            ], cwd="/workspace", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            states = [json.loads(line) for line in open(out) if '"turn"' in line]
            last = states[-1]
            alive = [s["name"] for s in last["board"]["snakes"]]
            if "gpt-5-5" in alive and "coreyja__bombastic-bob" not in alive:
                res = "win"
            elif "coreyja__bombastic-bob" in alive and "gpt-5-5" not in alive:
                res = "loss"
            elif "coreyja__bombastic-bob" not in alive and "gpt-5-5" not in alive:
                res = "tie"
            else:
                res = "both"
            ctr[res] += 1
            turns.append(last["turn"])
            if res != "win":
                bad.append((seed, res, last["turn"]))
        except Exception as exc:
            ctr["err"] += 1
            bad.append((seed, "err", repr(exc)))
    print(ctr, "avgturn", (sum(turns) / len(turns) if turns else None), "bad", bad[:20])
finally:
    for proc in (me, opp):
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
