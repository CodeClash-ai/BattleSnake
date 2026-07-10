import json, glob

# Categorize losses: were we longer, shorter, or tied when we died?
longer_losses = 0
shorter_losses = 0
equal_losses = 0
total = 0
edge_deaths = 0
corner_deaths = 0
trapped_deaths = 0
h2h_lost = 0
h2h_deaths_when_longer = 0

for f in sorted(glob.glob('/logs/rounds/3/sim_*.jsonl')):
    with open(f) as fh:
        lines = fh.readlines()
    if len(lines) < 3: continue
    result = json.loads(lines[-1])
    if 'opus' in result.get('winnerName', '') or result.get('isDraw'): continue
    total += 1
    frames = []
    for line in lines[1:-1]:
        try: d = json.loads(line)
        except: continue
        if 'board' not in d: continue
        frames.append(d)
    if len(frames) < 2: continue
    # find last frame where we still exist
    last_alive = None
    death_frame = None
    for fr in frames:
        our = None
        for s in fr['board']['snakes']:
            if 'opus' in s['name']:
                our = s; break
        if our:
            last_alive = fr
        else:
            death_frame = fr
            break
    if last_alive is None: continue
    our = [s for s in last_alive['board']['snakes'] if 'opus' in s['name']][0]
    opp = None
    for s in last_alive['board']['snakes']:
        if 'opus' not in s['name']:
            opp = s; break
    if opp is None: continue
    ol = len(our['body']); pl = len(opp['body'])
    if ol > pl: longer_losses += 1
    elif ol < pl: shorter_losses += 1
    else: equal_losses += 1
    hx, hy = our['body'][0]['x'], our['body'][0]['y']
    w = last_alive['board']['width']
    h = last_alive['board']['height']
    if hx in (0, w-1) or hy in (0, h-1): edge_deaths += 1
    if (hx in (0,w-1)) and (hy in (0,h-1)): corner_deaths += 1
    # check h2h
    ox, oy = opp['body'][0]['x'], opp['body'][0]['y']
    if abs(ox-hx)+abs(oy-hy) <= 2:
        # potential h2h scenario
        # look at death frame if any
        if death_frame:
            # our snake gone, opp survived: probably h2h
            opp_new = None
            for s in death_frame['board']['snakes']:
                if 'opus' not in s['name']:
                    opp_new = s; break
            if opp_new:
                onx, ony = opp_new['body'][0]['x'], opp_new['body'][0]['y']
                # if opp moved adjacent to our old head, could be h2h loss
                if abs(onx-hx)+abs(ony-hy) == 1:
                    h2h_lost += 1
                    if ol > pl:
                        h2h_deaths_when_longer += 1

print(f"Total losses: {total}")
print(f"Died while LONGER: {longer_losses}")
print(f"Died while SHORTER: {shorter_losses}")
print(f"Died while EQUAL: {equal_losses}")
print(f"Edge deaths: {edge_deaths}")
print(f"Corner deaths: {corner_deaths}")
print(f"Likely h2h losses: {h2h_lost}")
print(f"  h2h deaths when longer(!): {h2h_deaths_when_longer}")
