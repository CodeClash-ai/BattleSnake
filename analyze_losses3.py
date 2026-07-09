import json, glob

def analyze_loss(f):
    with open(f) as fh:
        lines = fh.readlines()
    turns_data = []
    for line in lines:
        d = json.loads(line)
        if 'turn' in d and 'board' in d:
            snakes = d['board']['snakes']
            turns_data.append((d['turn'], [(s['name'][:6], len(s['body']), s['health']) for s in snakes]))
    if not turns_data:
        return None
    last = turns_data[-1]
    end_turn = last[0]
    # find our final state
    our_stats = None
    opp_stats = None
    for name, ln, hp in last[1]:
        if 'opus' in name:
            our_stats = (ln, hp)
        else:
            opp_stats = (ln, hp)
    # first state
    first = turns_data[0]
    return {'end_turn':end_turn, 'our_final':our_stats, 'opp_final':opp_stats}

losses_by_round={}
for r in [0,1,2]:
    losses = []
    for f in sorted(glob.glob(f'/logs/rounds/{r}/sim_*.jsonl')):
        with open(f) as fh:
            lines = fh.readlines()
        if not lines: continue
        last=json.loads(lines[-1])
        if not last.get('isDraw') and last.get('winnerName')!='opus-4-7':
            info = analyze_loss(f)
            info['file']=f
            losses.append(info)
    losses_by_round[r]=losses

for r,ls in losses_by_round.items():
    print(f"\n=== Round {r}: {len(ls)} losses ===")
    turns=[l['end_turn'] for l in ls]
    if turns:
        print(f"  End turns: min={min(turns)} max={max(turns)} avg={sum(turns)/len(turns):.1f}")
    # length diff at loss
    for l in ls[:10]:
        our = l['our_final']
        opp = l['opp_final']
        print(f"  turn={l['end_turn']} our={our} opp={opp}")
