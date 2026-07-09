import json, glob
# Count our length growth in losses vs wins in round 2
def growth(f):
    with open(f) as fh:
        lines = fh.readlines()
    us_lens = []
    opp_lens = []
    for line in lines:
        try: d = json.loads(line)
        except: continue
        if 'board' not in d: continue
        us = next((s for s in d['board']['snakes'] if 'opus' in s['name']), None)
        opp = next((s for s in d['board']['snakes'] if 'opus' not in s['name']), None)
        if us and opp:
            us_lens.append(len(us['body']))
            opp_lens.append(len(opp['body']))
    return us_lens, opp_lens

# For losses, plot max length reached
maxlens_loss = []
maxlens_win = []
for r in [2]:
    for f in sorted(glob.glob(f'/logs/rounds/{r}/sim_*.jsonl')):
        with open(f) as fh:
            lines = fh.readlines()
        if not lines: continue
        last=json.loads(lines[-1])
        us_lens, opp_lens = growth(f)
        if not us_lens: continue
        won = last.get('winnerName')=='opus-4-7'
        (maxlens_win if won else maxlens_loss).append((max(us_lens), max(opp_lens) if opp_lens else 0))
print(f"Losses: max_us={max(x[0] for x in maxlens_loss)} avg_us={sum(x[0] for x in maxlens_loss)/len(maxlens_loss):.1f}")
print(f"Wins: max_us={max(x[0] for x in maxlens_win)} avg_us={sum(x[0] for x in maxlens_win)/len(maxlens_win):.1f}")
print(f"Loss samples: {maxlens_loss[:10]}")
