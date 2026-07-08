import json, glob
d = "/logs/rounds/2"
turns=[]
for f in sorted(glob.glob(d+"/sim_*.jsonl")):
    lines=open(f).read().strip().split("\n")
    maxturn=0
    for ln in lines:
        o=json.loads(ln)
        t=o.get("turn")
        if t is not None: maxturn=max(maxturn,t)
    turns.append(maxturn)
turns.sort()
print("games:",len(turns))
print("min/median/max turns:", turns[0], turns[len(turns)//2], turns[-1])
print("avg:", sum(turns)/len(turns))
# distribution
short=[t for t in turns if t<20]
print("games ending <20 turns:", len(short))
