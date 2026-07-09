import json, glob
# Check board and full body at the last valid state before death for all round-2 losses
files = []
for r in [0,1,2]:
    for f in sorted(glob.glob(f'/logs/rounds/{r}/sim_*.jsonl')):
        with open(f) as fh:
            lines = fh.readlines()
        if not lines: continue
        last=json.loads(lines[-1])
        if not last.get('isDraw') and last.get('winnerName')!='opus-4-7':
            files.append(f)
print(f"Total losses: {len(files)}")

# For each, check: was our tail reachable at time of death? Corner? Edge?
corner_deaths=0
edge_deaths=0
open_deaths=0
long_lead_deaths=0  # dying with length advantage
for f in files:
    with open(f) as fh:
        lines = fh.readlines()
    parsed = [json.loads(l) for l in lines]
    # find last state where we exist
    our_state = None
    for d in parsed:
        if 'board' not in d: continue
        snakes = d['board']['snakes']
        us = next((s for s in snakes if 'opus' in s['name']), None)
        if us: our_state = (d, us)
    if not our_state: continue
    d, us = our_state
    w = d['board']['width']; h = d['board']['height']
    head = us['body'][0]
    opp = next((s for s in d['board']['snakes'] if 'opus' not in s['name']), None)
    hx,hy = head['x'],head['y']
    corner = (hx in (0,w-1)) and (hy in (0,h-1))
    edge = hx in (0,w-1) or hy in (0,h-1)
    if corner: corner_deaths+=1
    elif edge: edge_deaths+=1
    else: open_deaths+=1
    if opp and len(us['body']) > len(opp['body']):
        long_lead_deaths+=1
print(f"Corner: {corner_deaths}, Edge (non-corner): {edge_deaths}, Open: {open_deaths}")
print(f"Deaths while being longer: {long_lead_deaths}")
