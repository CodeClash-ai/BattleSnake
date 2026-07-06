import json, glob, os

def last_two_turns(f, me="opus-4-8"):
    lines = [json.loads(l) for l in open(f) if l.strip()]
    turns = [l for l in lines if "turn" in l and "board" in l]
    # find turn where I disappear
    prev = None
    for t in turns:
        names = [s["name"] for s in t["board"]["snakes"]]
        if me not in names:
            return prev, t
        prev = t
    return prev, None

for f in sorted(glob.glob("/logs/rounds/0/sim_*.jsonl")):
    prev, gone = last_two_turns(f)
    n=os.path.basename(f)
    if gone is None:
        continue  # we won
    # show my last state and opponent
    b = prev["board"]
    me="opus-4-8"
    ms=[s for s in b["snakes"] if s["name"]==me][0]
    opp=[s for s in b["snakes"] if s["name"]!=me]
    print(f"\n=== {n} died at turn {prev['turn']}->{gone['turn']} ===")
    print("my head:", ms["head"], "len", ms["length"], "health", ms["health"])
    for o in opp:
        print("opp head:", o["head"], "len", o["length"])
    print("food:", b["food"])
    print("my body:", [(c['x'],c['y']) for c in ms["body"]])
