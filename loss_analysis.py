import json, glob, os
from collections import defaultdict
d="/logs/rounds/1"
games=defaultdict(list)
for f in glob.glob(os.path.join(d,"sim_*.jsonl")):
    lines=open(f).read().strip().split("\n")
    gid=None; frames=[]
    for ln in lines:
        try: o=json.loads(ln)
        except: continue
        if "board" in o:
            gid=o["game"]["id"]; frames.append(o)
    if gid and frames: games[gid]=frames

target=["cca5d25b","a00383a9","56ef62a5","ff1f024e"]
for gid,frames in games.items():
    if gid[:8] not in target: continue
    last=frames[-1]
    print(f"\n=== game {gid[:8]} turns={last['turn']} W={last['board'].get('width')}x{last['board'].get('height')} ===")
    # last 4 frames full board
    for fr in frames[-4:]:
        b=fr['board']
        print(f" turn {fr['turn']}:")
        for s in b['snakes']:
            tag="US" if s['name'].startswith('opus') else "OPP"
            body=[(c['x'],c['y']) for c in s['body']]
            print(f"   {tag} head={s['head']['x']},{s['head']['y']} len={s['length']} body={body}")
