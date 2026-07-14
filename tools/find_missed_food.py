#!/usr/bin/env python3
import json, glob, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main
root=sys.argv[1]
for p in sorted(glob.glob(root+'/sim_*.jsonl')):
    objs=[]
    for line in open(p):
        try: objs.append(json.loads(line))
        except: pass
    if not objs or objs[-1].get('winnerName')!='TheApX__hungry': continue
    for o in objs:
        if 'board' not in o: continue
        me=next((s for s in o['board']['snakes'] if s.get('name')=='gpt-5-5'),None)
        if not me: continue
        opps=[s for s in o['board']['snakes'] if s.get('name')!='gpt-5-5']
        if not opps: continue
        maxe=max(s['length'] for s in opps); deficit=maxe-me['length']
        if deficit<3: continue
        head=main.pt(me['head']); food=[main.pt(f) for f in o['board'].get('food',[])]
        adj=[(name,main.add(head,d)) for name,d in main.MOVES.items() if main.add(head,d) in food]
        if not adj: continue
        o['you']=me; mv=main.move(o)['move']
        if all(name!=mv for name,_ in adj):
            print(os.path.basename(p),'t',o['turn'],'len',me['length'],'maxe',maxe,'hp',me['health'],'head',head,'food',food,'adj',adj,'cur',mv)
            break
