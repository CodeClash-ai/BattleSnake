import json, glob, os, sys
logdir = sys.argv[1] if len(sys.argv)>1 else "/logs/rounds/1"
files = sorted(glob.glob(os.path.join(logdir,"sim_*.jsonl")))
wall=0;other=0
for f in files:
    if os.path.getsize(f)==0: continue
    lines=[l for l in open(f).read().strip().split("\n") if l.strip()]
    boards=[json.loads(l) for l in lines if '"turn"' in l]
    if len(boards)<2: continue
    prev=boards[-1]
    opp=None
    for s in prev['board']['snakes']:
        if 'Nettogrof' in s['name'] or 'pambrose' in s['name']:
            opp=s
    if opp is None:
        # opp already eliminated
        continue
    h=opp['head']
    W=prev['board']['width']; H=prev['board']['height']
    if h['x']<0 or h['x']>=W or h['y']<0 or h['y']>=H:
        wall+=1
    else:
        other+=1
print("wall(head OOB):",wall,"other:",other)
