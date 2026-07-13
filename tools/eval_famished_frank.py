"""Local batch against copied coreyja Famished Frank opponent."""
import collections, json, os, subprocess, time, glob
N = int(os.environ.get("N", "50"))
me = subprocess.Popen(["python3", "main.py"], cwd="/workspace", env=dict(os.environ, PORT="8000"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
opp = subprocess.Popen(["python3", "tools/famished_frank_opponent.py"], cwd="/workspace", env=dict(os.environ, PORT="8001"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ctr=collections.Counter(); turns=[]
try:
    for seed in range(N):
        out=f"/tmp/famished_{seed}.jsonl"
        try:
            subprocess.run(["./game/battlesnake","play","-W","11","-H","11","-n","gpt-5-5","-u","http://127.0.0.1:8000","-n","coreyja__famished-frank","-u","http://127.0.0.1:8001","-r",str(seed),"-o",out], cwd="/workspace", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
            states=[json.loads(line) for line in open(out) if '"turn"' in line]
            last=states[-1]
            alive=[s["name"] for s in last["board"]["snakes"]]
            if "gpt-5-5" in alive and "coreyja__famished-frank" not in alive: res="win"
            elif "coreyja__famished-frank" in alive and "gpt-5-5" not in alive: res="loss"
            elif "coreyja__famished-frank" not in alive and "gpt-5-5" not in alive: res="tie"
            else: res="both"
            ctr[res]+=1; turns.append(last["turn"])
        except Exception as ex:
            ctr["err"] += 1
    print(ctr, "avgturn", (sum(turns)/len(turns) if turns else None))
finally:
    me.terminate(); opp.terminate()
    try: me.wait(timeout=2)
    except Exception: me.kill()
    try: opp.wait(timeout=2)
    except Exception: opp.kill()
