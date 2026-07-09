import json, glob
for r in [0,1,2]:
    for f in sorted(glob.glob(f'/logs/rounds/{r}/sim_*.jsonl')):
        with open(f) as fh:
            lines = fh.readlines()
        if not lines: continue
        last=json.loads(lines[-1])
        if last.get('isDraw') or last.get('winnerName')=='opus-4-7': continue
        parsed = [json.loads(l) for l in lines]
        our_state = None
        for d in parsed:
            if 'board' not in d: continue
            us = next((s for s in d['board']['snakes'] if 'opus' in s['name']), None)
            if us: our_state = (d, us)
        if not our_state: continue
        d, us = our_state
        w = d['board']['width']; h = d['board']['height']
        hx,hy = us['body'][0]['x'],us['body'][0]['y']
        corner = (hx in (0,w-1)) and (hy in (0,h-1))
        edge = hx in (0,w-1) or hy in (0,h-1)
        if corner or edge: continue
        opp = next((s for s in d['board']['snakes'] if 'opus' not in s['name']), None)
        print(f"{f} turn={d['turn']} head=({hx},{hy}) our_len={len(us['body'])} opp_len={len(opp['body']) if opp else '?'} hp={us['health']}")
        print(f"  body first 8: {us['body'][:8]}")
        if opp:
            print(f"  opp_head: ({opp['body'][0]['x']},{opp['body'][0]['y']}) body first 5: {opp['body'][:5]}")
