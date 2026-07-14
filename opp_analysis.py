import json, glob, os
files = sorted(glob.glob("/logs/rounds/0/sim_*.jsonl"))
death_causes={}
for f in files:
    if os.path.getsize(f)==0: continue
    lines=[l for l in open(f).read().strip().split("\n") if l.strip()]
    boards=[json.loads(l) for l in lines if '"turn"' in l]
    if len(boards)<2: continue
    # last board before end
    lastb=boards[-1]
    snakes=lastb['board']['snakes']
    opp=[s for s in snakes if s['name'].startswith('Netto')]
    me=[s for s in snakes if s['name'].startswith('opus')]
    # find opp move from second-last to last
    if len(boards)>=2:
        prev=boards[-2]['board']['snakes']
        oprev=[s for s in prev if s['name'].startswith('Netto')]
        if oprev:
            h=oprev[0]['head']
            # where did they go next? board after
            onow=opp[0]['head'] if opp else None
            # actually opp may already be dead in last board
    print(os.path.basename(f), "turns=",lastb['turn'], "opp_alive=",bool(opp))
