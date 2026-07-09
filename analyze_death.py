import json, glob, sys

# Look at last few turns of each loss to figure out what killed us
def analyze(f):
    with open(f) as fh:
        lines = fh.readlines()
    parsed = []
    for line in lines:
        try:
            d = json.loads(line)
            parsed.append(d)
        except: pass
    # Find last board state before we vanished
    our_last = None
    for d in parsed:
        if 'board' in d:
            snakes = d['board'].get('snakes', [])
            for s in snakes:
                if 'opus' in s['name']:
                    our_last = (d.get('turn', -1), s, d['board'])
    return our_last, parsed[-1]

for r in [2]:
    for f in sorted(glob.glob(f'/logs/rounds/{r}/sim_*.jsonl')):
        with open(f) as fh:
            lines = fh.readlines()
        if not lines: continue
        last=json.loads(lines[-1])
        if not last.get('isDraw') and last.get('winnerName')!='opus-4-7':
            our_last, final = analyze(f)
            if our_last:
                turn, us, board = our_last
                head = us['body'][0]
                length = len(us['body'])
                health = us['health']
                # Opponent info
                opps = [s for s in board['snakes'] if 'opus' not in s['name']]
                opp = opps[0] if opps else None
                opp_info = ""
                if opp:
                    ohead = opp['body'][0]
                    opp_info = f"opp_head={ohead} opp_len={len(opp['body'])}"
                print(f"{f}: last_turn={turn} head={head} len={length} hp={health} {opp_info}")
