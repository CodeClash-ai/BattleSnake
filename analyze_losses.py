import json, sys
def frames(f):
    out=[]
    for l in open(f):
        l=l.strip()
        if not l: continue
        d=json.loads(l)
        if 'board' in d and 'turn' in d: out.append(d)
    return out
for f in sys.argv[1:]:
    fr=frames(f)
    if len(fr)<2: continue
    # last frame with opus alive
    pre=fr[-2]
    opus=None;opp=None
    for s in pre['board']['snakes']:
        if 'opus' in s['name']: opus=s
        else: opp=s
    lo=len(opus['body']) if opus else 0
    lp=len(opp['body']) if opp else 0
    # was it edge death?
    h=opus['body'][0] if opus else None
    edge = h and (h['x'] in (0,10) or h['y'] in (0,10))
    print(f"{f} turn{pre['turn']} OPUS L{lo} @({h['x']},{h['y']}) OPP L{lp} edge={edge}")
