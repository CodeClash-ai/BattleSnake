import json, glob

losses = []
wins = 0
ties = 0
for f in sorted(glob.glob('/logs/rounds/4/sim_*.jsonl')):
    with open(f) as fh:
        lines = fh.readlines()
    if not lines: continue
    last = json.loads(lines[-1])
    if last.get('isDraw'): ties += 1
    elif last.get('winnerName') == 'opus-4-7': wins += 1
    else:
        # loss
        # get penultimate turn to see state
        try:
            for i in range(len(lines)-1, -1, -1):
                d = json.loads(lines[i])
                if 'board' in d:
                    snakes = d['board']['snakes']
                    our = None
                    opp = None
                    for s in snakes:
                        if 'opus' in s['name']:
                            our = s
                        else:
                            opp = s
                    losses.append({'f': f, 'turn': d.get('turn'), 'our': our, 'opp': opp})
                    break
        except Exception as e:
            print('err', f, e)

print(f"W={wins} L={len(losses)} T={ties}")
print("\nLoss details:")
for l in losses:
    our = l['our']
    opp = l['opp']
    if our:
        head = our['body'][0] if our['body'] else None
        # Check if on edge
        edge = ''
        if head:
            x, y = head['x'], head['y']
            if x == 0 or x == 10: edge += 'W'
            if y == 0 or y == 10: edge += 'W'
        print(f"  turn={l['turn']} our_len={len(our['body']) if our else 0} our_hp={our['health'] if our else 0} head={head} edge={edge} opp_len={len(opp['body']) if opp else 0}")
