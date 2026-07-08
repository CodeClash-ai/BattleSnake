import json, glob, os
d="/logs/rounds/0"
death_turns=[]
for f in sorted(glob.glob(d+"/sim_*.jsonl")):
    if os.path.getsize(f)==0: continue
    lines=open(f).read().strip().split("\n")
    states=[]
    for ln in lines:
        try:
            o=json.loads(ln)
            if "board" in o and "turn" in o: states.append(o)
        except: pass
    if len(states)<2: continue
    # find when opp died: track opp presence
    prev=states[0]
    for s in states[1:]:
        names={sn["name"] for sn in s["board"]["snakes"]}
        if "Nettogrof__nessegrev-julia" not in names:
            # opp died this turn; look at prev opp head + surroundings
            opp_prev=[sn for sn in prev["board"]["snakes"] if sn["name"]=="Nettogrof__nessegrev-julia"]
            if opp_prev:
                oh=opp_prev[0]["head"]
                death_turns.append((os.path.basename(f), s["turn"], oh, opp_prev[0]["health"]))
            break
        prev=s
for x in death_turns[:15]:
    print(x)
print("total tracked deaths:", len(death_turns))
tcount={}
for _,t,_,_ in death_turns: tcount[t]=tcount.get(t,0)+1
print("death turn distribution:", dict(sorted(tcount.items())))
