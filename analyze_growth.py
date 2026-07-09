import json, glob

def analyze(f):
    with open(f) as fh:
        lines = fh.readlines()
    trajectory = []  # (turn, our_len, our_hp, opp_len, opp_hp)
    for line in lines:
        d = json.loads(line)
        if 'turn' in d and 'board' in d:
            snakes = d['board']['snakes']
            our_len=our_hp=opp_len=opp_hp=None
            for s in snakes:
                if 'opus' in s['name']:
                    our_len=len(s['body']); our_hp=s['health']
                else:
                    opp_len=len(s['body']); opp_hp=s['health']
            trajectory.append((d['turn'], our_len, our_hp, opp_len, opp_hp))
    return trajectory

# Analyze one loss in detail
f='/logs/rounds/2/sim_100.jsonl'
t = analyze(f)
for row in t[::5]:
    print(row)
print('---')
for row in t[-6:]:
    print(row)
