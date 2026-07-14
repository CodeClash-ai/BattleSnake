#!/usr/bin/env python3
"""Print current main.move scores for a logged state (kept for teammate analysis)."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main
p=sys.argv[1]; turn=int(sys.argv[2]); me_name=sys.argv[3] if len(sys.argv)>3 else 'gpt-5-5'

def score_moves(game_state):
    board = game_state["board"]; you=game_state["you"]; w,h=board["width"],board["height"]
    my_id=you["id"]; my_body=[main.pt(x) for x in you["body"]]; head=my_body[0]
    my_len=len(my_body); my_health=you.get('health',100); food=[main.pt(f) for f in board.get('food',[])]
    hazards={main.pt(x) for x in board.get('hazards',[])}
    hazard_damage=game_state.get('game',{}).get('ruleset',{}).get('settings',{}).get('hazardDamagePerTurn',14)
    snakes=board.get('snakes',[]); enemies=[s for s in snakes if s.get('id')!=my_id]
    blocked=set()
    for s in snakes:
        body=[main.pt(x) for x in s.get('body',[])]
        if not body: continue
        is_me=s.get('id')==my_id
        could_grow=(not is_me) and (main.adjacent_food(body[0], food, w, h) or s.get('health',100)<=1)
        for i,cell in enumerate(body):
            if i==len(body)-1 and not could_grow: continue
            blocked.add(cell)
    enemy_heads=[main.pt(s['head']) for s in enemies]
    enemy_lengths={main.pt(s['head']):s.get('length',len(s.get('body',[]))) for s in enemies}
    danger_equal_longer=set(); danger_shorter=set(); enemy_nexts=[]
    for s in enemies:
        body=[main.pt(x) for x in s.get('body',[])]
        if not body: continue
        eh=body[0]; elen=s.get('length',len(body)); opts=[]; neck2=body[1] if len(body)>1 else None
        for d in main.MOVES.values():
            n=main.add(eh,d)
            if not main.inside(n,w,h): continue
            if n==neck2 and len(set(body[:3]))>1: continue
            if n in blocked and n != head: continue
            opts.append(n)
            (danger_equal_longer if elen>=my_len else danger_shorter).add(n)
        enemy_nexts.append((s,opts))
    max_enemy_len=max([s.get('length',len(s.get('body',[]))) for s in enemies]+[0])
    neck=my_body[1] if len(my_body)>1 else None; center=((w-1)/2,(h-1)/2)
    out=[]
    for name,delta in main.MOVES.items():
        n=main.add(head,delta); reasons=[]
        if not main.inside(n,w,h): out.append((None,name,n,['oob'])); continue
        if n==neck and len(set(my_body[:3]))>1: out.append((None,name,n,['neck'])); continue
        if n in blocked: out.append((None,name,n,['blocked'])); continue
        if n in hazards and my_health<=hazard_damage+1: out.append((None,name,n,['hazard lethal'])); continue
        sim_blocked=set(blocked); sim_blocked.add(head)
        if n in food and my_body: sim_blocked.add(my_body[-1])
        area=main.flood(n,sim_blocked,w,h,limit=w*h)
        if area<=1: out.append((None,name,n,[f'area={area}'])); continue
        score=area*12.0; reasons.append(('area',area*12.0,area))
        h2h_bad=n in danger_equal_longer; h2h_good=n in danger_shorter
        if h2h_bad: score-=10000; reasons.append(('h2hbad',-10000,''))
        if h2h_good and my_len>max_enemy_len:
            if my_len<=max_enemy_len+3: score+=40; reasons.append(('h2hgood',40,''))
            elif my_len<=max_enemy_len+4: score+=8; reasons.append(('h2hgood',8,''))
            else: score-=70; reasons.append(('far chase',-70,''))
        exits=sum(1 for d2 in main.MOVES.values() if main.inside(main.add(n,d2),w,h) and main.add(n,d2) not in sim_blocked)
        score+=exits*18; reasons.append(('exits',exits*18,exits))
        future=sum(1 for d2 in main.MOVES.values() if main.inside(main.add(n,d2),w,h) and main.add(n,d2) not in sim_blocked and main.add(n,d2) not in danger_equal_longer)
        score+=future*10; reasons.append(('future',future*10,future))
        if my_len>=10 and my_health>45:
            static_blocked=set(sim_blocked)-set(my_body)
            if n in food: next_body=tuple([n]+my_body); lookahead_food=[f for f in food if f!=n]
            else: next_body=tuple([n]+my_body[:-1]); lookahead_food=food
            pc=main.self_path_count(next_body,lookahead_food,static_blocked,w,h,depth=6,cap=200)
            score+=min(pc,80)*2; reasons.append(('pathcnt',min(pc,80)*2,pc))
            tail_cell=next_body[-1]; tb=set(sim_blocked); tb.discard(tail_cell)
            td=main.shortest(n,[tail_cell],tb,w,h,max_depth=w*h)
            reasons.append(('taildist',0,td))
        fd=main.shortest(n,food,sim_blocked,w,h,max_depth=60)
        reasons.append(('fooddist',0,fd))
        score-= (abs(n[0]-center[0])+abs(n[1]-center[1]))*2.2
        if n[0] in (0,w-1) or n[1] in (0,h-1): score-=12
        out.append((score,name,n,reasons))
    return sorted(out, reverse=True, key=lambda x: -999999 if x[0] is None else x[0])

for line in open(p):
    o=json.loads(line)
    if o.get('turn')==turn:
        me=next(s for s in o['board']['snakes'] if s.get('name')==me_name); o['you']=me
        print('main', main.move(o), 'turn', turn)
        for sc,name,n,rs in score_moves(o): print(sc,name,n,rs)
