"""Analyze losses in a round's game logs.

Usage: python analyze_losses.py [round_num]

Categorizes losses by:
- "trapped": no valid moves at last-alive turn (self-body, opp-body, walls)
- "h2h_lose": only-safe moves led into equal/longer opponent head
- "starve": health <= 2
- "unknown": other (likely flood-fill trap)
"""
import json, glob, sys, os

round_num = int(sys.argv[1]) if len(sys.argv) > 1 else 2
pattern = f'/logs/rounds/{round_num}/sim_*.jsonl'
files = glob.glob(pattern)
if not files:
    print(f'No files at {pattern}')
    sys.exit(1)

wins = losses = ties = 0
causes = {'wall':0, 'self':0, 'body':0, 'h2h_lose':0, 'trapped':0, 'unknown':0, 'starve':0}
loss_files = []
for f in files:
    with open(f) as fh:
        lines = fh.readlines()
    if not lines:
        continue
    d_last = json.loads(lines[-1])
    if d_last.get('isDraw'):
        ties += 1; continue
    if d_last.get('winnerName') == 'opus-4-7':
        wins += 1; continue
    losses += 1
    loss_files.append(f)
    if len(lines) < 3: continue
    # Find last alive turn for us
    for i in range(len(lines)-2, -1, -1):
        d = json.loads(lines[i])
        if 'board' not in d: continue
        our = None
        for s in d['board']['snakes']:
            if s['name'] == 'opus-4-7': our = s
        if not our: continue
        head = our['body'][0]
        W = d['board']['width']; H = d['board']['height']
        body = set((b['x'],b['y']) for b in our['body'][:-1])
        opp = [s for s in d['board']['snakes'] if s['name']!='opus-4-7']
        opp_bodies = set(); opp_heads = []
        for s in opp:
            for b in s['body'][:-1]: opp_bodies.add((b['x'],b['y']))
            opp_heads.append((s['body'][0], len(s['body'])))
        moves = [(head['x'],head['y']+1),(head['x'],head['y']-1),(head['x']-1,head['y']),(head['x']+1,head['y'])]
        valid = []
        wall_ct = self_ct = body_ct = 0
        for m in moves:
            if not (0<=m[0]<W and 0<=m[1]<H): wall_ct+=1; continue
            if m in body: self_ct+=1; continue
            if m in opp_bodies: body_ct+=1; continue
            valid.append(m)
        if our['health'] <= 2: causes['starve']+=1; break
        if not valid:
            if wall_ct==4: causes['wall']+=1
            elif self_ct>0: causes['self']+=1
            else: causes['body']+=1
            causes['trapped']+=1; break
        our_len = len(our['body'])
        all_lose = True
        for m in valid:
            for oh, ol in opp_heads:
                oh_m = [(oh['x'],oh['y']+1),(oh['x'],oh['y']-1),(oh['x']-1,oh['y']),(oh['x']+1,oh['y'])]
                if m in oh_m and ol >= our_len: break
            else:
                all_lose = False; continue
            # for-else: break -> lose for this move
        if all_lose: causes['h2h_lose']+=1
        else: causes['unknown']+=1
        break

print(f'Round {round_num}: W={wins} L={losses} T={ties}')
print('Loss causes:', causes)
