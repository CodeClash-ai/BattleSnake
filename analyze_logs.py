import json, sys, glob, os
logdir = sys.argv[1] if len(sys.argv)>1 else "/logs/rounds/0"
files = sorted(glob.glob(os.path.join(logdir,"sim_*.jsonl")))
wins={}; turns=[]
for f in files:
    if os.path.getsize(f)==0: continue
    lines=[l for l in open(f).read().strip().split("\n") if l.strip()]
    if not lines: continue
    last=json.loads(lines[-1])
    if 'winnerName' in last:
        w=last['winnerName'] if not last.get('isDraw') else 'DRAW'
    else:
        w='?'
    t=0
    for ln in lines:
        d=json.loads(ln)
        if 'turn' in d: t=max(t,d['turn'])
    turns.append(t)
    wins[w]=wins.get(w,0)+1
print("games played:",len(turns))
print("wins:",wins)
print("avg turns:", round(sum(turns)/len(turns),1), "min",min(turns),"max",max(turns))
