"""Run a quick local match batch against tools/simple_opponent.py."""
import collections, json, os, subprocess, time

N = int(os.environ.get("N", "50"))
me = subprocess.Popen(["python3", "main.py"], cwd="/workspace", env=dict(os.environ, PORT="8000"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
opp = subprocess.Popen(["python3", "tools/simple_opponent.py"], cwd="/workspace", env=dict(os.environ, PORT="8001"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ctr = collections.Counter(); turns = []
try:
    for seed in range(N):
        out = f"/tmp/bs_{seed}.jsonl"
        subprocess.run(["./game/battlesnake", "play", "-W", "11", "-H", "11", "-n", "gpt-5-5", "-u", "http://127.0.0.1:8000", "-n", "opp", "-u", "http://127.0.0.1:8001", "-r", str(seed), "-o", out], cwd="/workspace", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        states = [json.loads(line) for line in open(out) if '"turn"' in line]
        last = states[-1]
        alive = [s["name"] for s in last["board"]["snakes"]]
        if "gpt-5-5" in alive and "opp" not in alive: res = "win"
        elif "opp" in alive and "gpt-5-5" not in alive: res = "loss"
        elif "opp" not in alive and "gpt-5-5" not in alive: res = "tie"
        else: res = "both"
        ctr[res] += 1; turns.append(last["turn"])
    print(ctr, "avgturn", sum(turns) / len(turns))
finally:
    me.terminate(); opp.terminate(); me.wait(timeout=2); opp.wait(timeout=2)
