import json, glob, os
files = sorted(glob.glob("/logs/rounds/0/sim_*.jsonl"))
wall=0;self_c=0;h2h=0;body=0;other=0
for f in files:
    if os.path.getsize(f)==0: continue
    lines=[l for l in open(f).read().strip().split("\n") if l.strip()]
    boards=[json.loads(l) for l in lines if '"turn"' in l]
    if len(boards)<2: continue
    prev=boards[-1]  # last board with opp still shown as 'you'
    # opp is 'you' in these logs
    opp=prev['you']
    h=opp['head']; body_pts=opp['body']
    # determine their next intended move by continuity? we only have positions.
    # Check where head is - if out of bounds already
    W=prev['board']['width']; H=prev['board']['height']
    if h['x']<0 or h['x']>=W or h['y']<0 or h['y']>=H:
        wall+=1
    else:
        other+=1
print("wall(head OOB in last board):",wall,"other:",other)
