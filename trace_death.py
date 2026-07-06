import json

def load(f):
    return [json.loads(l) for l in open(f) if l.strip()]

def trace(f, me="opus-4-8", n=4):
    lines=load(f)
    turns=[l for l in lines if "turn" in l and "board" in l]
    # find death index
    idx=None
    for i,t in enumerate(turns):
        if me not in [s["name"] for s in t["board"]["snakes"]]:
            idx=i; break
    if idx is None:
        print("survived"); return
    for t in turns[max(0,idx-n):idx]:
        b=t["board"]
        ms=[s for s in b["snakes"] if s["name"]==me][0]
        opp=[s for s in b["snakes"] if s["name"]!=me]
        oh=opp[0]["head"] if opp else None
        print(f"turn {t['turn']}: head={ms['head']} len={ms['length']} hp={ms['health']} opp={oh}")
    print("--- died next turn ---")

import sys
trace(sys.argv[1])
