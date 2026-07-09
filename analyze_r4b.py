import json, glob

losses = []
for f in sorted(glob.glob('/logs/rounds/4/sim_*.jsonl')):
    with open(f) as fh:
        lines = fh.readlines()
    if not lines: continue
    last = json.loads(lines[-1])
    if not last.get('isDraw') and last.get('winnerName') != 'opus-4-7':
        # find last board state that contains our snake
        our_last = None
        opp_last = None
        turn = None
        for i in range(len(lines)-1, -1, -1):
            d = json.loads(lines[i])
            if 'board' in d:
                snakes = d['board']['snakes']
                our = next((s for s in snakes if 'opus' in s['name']), None)
                opp = next((s for s in snakes if 'opus' not in s['name']), None)
                if our and our_last is None:
                    our_last = our
                    opp_last = opp
                    turn = d.get('turn')
                    break
        losses.append({'f': f, 'turn': turn, 'our': our_last, 'opp': opp_last})

print(f"L={len(losses)}")
for l in losses:
    our = l['our']
    opp = l['opp']
    head = our['body'][0]
    x, y = head['x'], head['y']
    edge = []
    if x == 0: edge.append('L')
    if x == 10: edge.append('R')
    if y == 0: edge.append('B')
    if y == 10: edge.append('T')
    opp_head = opp['body'][0] if opp and opp['body'] else None
    dist = abs(x - opp_head['x']) + abs(y - opp_head['y']) if opp_head else -1
    print(f"  {l['f'].split('/')[-1]} turn={l['turn']} our_len={len(our['body'])} hp={our['health']} head=({x},{y}) edge={edge} opp_len={len(opp['body']) if opp else 0} opp_dist={dist}")
