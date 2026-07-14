#!/usr/bin/env python3
import json,sys,os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main
p=sys.argv[1]; turn=int(sys.argv[2])
for line in open(p):
    o=json.loads(line)
    if o.get('turn')==turn:
        me=next(sn for sn in o['board']['snakes'] if sn['name']=='gpt-5-5')
        o['you']=me
        board=o['board']; w=board['width']; h=board['height']; food=[main.pt(f) for f in board.get('food',[])]
        my_body=[main.pt(x) for x in me['body']]; head=my_body[0]; my_len=len(my_body); my_id=me['id']
        snakes=board['snakes']; enemies=[s for s in snakes if s['id']!=my_id]; max_enemy=max([s['length'] for s in enemies]+[0])
        blocked=set()
        for s in snakes:
            body=[main.pt(x) for x in s['body']]; is_me=s['id']==my_id
            could=(not is_me) and main.adjacent_food(body[0], food, w,h)
            for i,c in enumerate(body):
                if i==len(body)-1 and not could: continue
                blocked.add(c)
        print('move', main.move(o), 'head',head,'len',my_len,'hp',me['health'],'maxe',max_enemy,'tail',my_body[-1])
        for name,d in main.MOVES.items():
            n=main.add(head,d)
            if not main.inside(n,w,h) or (len(my_body)>1 and n==my_body[1] and len(set(my_body[:3]))>1) or n in blocked:
                print(name,n,'illegal')
                continue
            sim=set(blocked); sim.add(head)
            if n in food: sim.add(my_body[-1])
            area=main.flood(n,sim,w,h,limit=w*h)
            exits=sum(1 for d2 in main.MOVES.values() if main.inside(main.add(n,d2),w,h) and main.add(n,d2) not in sim)
            nb=tuple([n]+(my_body if n in food else my_body[:-1]))
            static=set(sim)-set(my_body)
            pc=main.self_path_count(nb,[f for f in food if f!=n],static,w,h,depth=6,cap=200)
            tail=nb[-1]; tb=set(sim); tb.discard(tail)
            td=main.shortest(n,[tail],tb,w,h,max_depth=w*h)
            fd=main.shortest(n,food,sim,w,h,max_depth=60)
            print(name,n,'area',area,'exits',exits,'food?',n in food,'fd',fd,'pc',pc,'tail',tail,'td',td)
