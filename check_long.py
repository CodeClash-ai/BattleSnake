import json
for f in ["sim_228","sim_229","sim_230"]:
    lines=open(f"/logs/rounds/0/{f}.jsonl").read().strip().split("\n")
    states=[]
    for ln in lines:
        try:
            o=json.loads(ln)
            if "board" in o and "turn" in o: states.append(o)
        except: pass
    last=states[-1]
    print(f, "final turn", last["turn"])
    for sn in last["board"]["snakes"]:
        print("  ", sn["name"], "len", sn["length"], "health", sn["health"], "head", sn["head"])
    # who won
    names={sn["name"] for sn in last["board"]["snakes"]}
    print("   alive:", names)
