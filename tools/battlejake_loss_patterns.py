#!/usr/bin/env python3
import json, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main
root=sys.argv[1] if len(sys.argv)>1 else '/logs/rounds/0'
me='gpt-5-5'
for p in sorted(glob.glob(root+'/sim_*.jsonl'), key=lambda x:int(os.path.basename(x)[4:-6])):
    lines=[json.loads(l) for l in open(p)]
    res=lines[-1]
    if res.get('winnerName')==me: continue
    cnt=0
    print('\n',os.path.basename(p),res)
    for o in lines[-16:-1]:
        if 'board' not in o: continue
        snakes=o['board']['snakes']
        ys=[s for s in snakes if s.get('name')==me]
        if not ys: continue
        you=ys[0]; o['you']=you
        mv=main.move(o)['move']; head=main.pt(you['head']); n=main.add(head, main.MOVES[mv])
        opp=[s for s in snakes if s.get('name')!=me]
        maxe=max([s.get('length',len(s.get('body',[]))) for s in opp]+[0]); olen=maxe
        danger_short=False; danger_long=False; edists=[]
        # approximate legal next squares using main blocked logic
        food=[main.pt(f) for f in o['board'].get('food',[])]; w=o['board']['width']; h=o['board']['height']; my_len=you['length']
        blocked=set()
        for s in snakes:
            body=[main.pt(x) for x in s.get('body',[])]
            cg=(s['id']!=you['id']) and (main.adjacent_food(body[0],food,w,h) or s.get('health',100)<=1)
            for i,c in enumerate(body):
                if i==len(body)-1 and not cg: continue
                blocked.add(c)
        for s in opp:
            body=[main.pt(x) for x in s.get('body',[])]; eh=body[0]; el=s.get('length',len(body)); edists.append(main.dist(n,eh))
            neck=body[1] if len(body)>1 else None
            for d in main.MOVES.values():
                nn=main.add(eh,d)
                if not main.inside(nn,w,h): continue
                if nn==neck and len(set(body[:3]))>1: continue
                if nn in blocked and nn != head: continue
                if nn==n:
                    if el>=my_len: danger_long=True
                    else: danger_short=True
        # candidate metrics
        sim_blocked=set(blocked); sim_blocked.add(head); 
        if n in food: sim_blocked.add(main.pt(you['body'][-1]))
        area=main.flood(n,sim_blocked,w,h,limit=w*h)
        exits=sum(1 for d in main.MOVES.values() if main.inside(main.add(n,d),w,h) and main.add(n,d) not in sim_blocked)
        print(f"t{o['turn']} hp{you['health']} len{my_len} diff{my_len-olen} head{head} op{main.pt(opp[0]['head']) if opp else None} mv{mv}->{n} ds{danger_short} dl{danger_long} ed{min(edists) if edists else None} area{area} ex{exits} food{n in food}")
