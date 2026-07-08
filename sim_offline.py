import sys, random, copy
sys.path.insert(0,'/workspace')
import importlib.util
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
me=load('me','/workspace/main.py')
opp=load('opp','/workspace/main_old_naive.py')

MOVES={'up':(0,1),'down':(0,-1),'left':(-1,0),'right':(1,0)}

def new_game(seed):
    random.seed(seed)
    W=H=11
    # standard start positions (corners-ish). Use two fixed spots.
    p1=(1,1); p2=(9,9)
    snakes={
      'me':{'id':'me','name':'me','health':100,'body':[p1,p1,p1]},
      'opp':{'id':'opp','name':'opp','health':100,'body':[p2,p2,p2]},
    }
    food=[(5,5),(1,9),(9,1)]
    return W,H,snakes,food

def gs_for(sid,W,H,snakes,food):
    sl=[]
    for k,s in snakes.items():
        sl.append({'id':s['id'],'name':s['name'],'health':s['health'],'length':len(s['body']),
                   'head':{'x':s['body'][0][0],'y':s['body'][0][1]},
                   'body':[{'x':x,'y':y} for x,y in s['body']]})
    you=next(x for x in sl if x['id']==sid)
    return {'turn':0,'board':{'width':W,'height':H,'food':[{'x':x,'y':y} for x,y in food],'snakes':sl},'you':you}

def play(seed):
    W,H,snakes,food=new_game(seed)
    for turn in range(200):
        moves={}
        for sid,bot in (('me',me),('opp',opp)):
            if sid not in snakes: continue
            try:
                mv=bot.move(gs_for(sid,W,H,snakes,food))['move']
            except Exception:
                mv='up'
            moves[sid]=mv
        # apply
        newheads={}
        for sid in list(snakes):
            dx,dy=MOVES.get(moves[sid],(0,1))
            hx,hy=snakes[sid]['body'][0]
            nh=(hx+dx,hy+dy)
            newheads[sid]=nh
            snakes[sid]['body'].insert(0,nh)
            snakes[sid]['health']-=1
            if nh in food:
                food.remove(nh); snakes[sid]['health']=100
            else:
                snakes[sid]['body'].pop()
        # spawn food occasionally
        if random.random()<0.15 or not food:
            for _ in range(5):
                fx,fy=random.randint(0,W-1),random.randint(0,H-1)
                allocc=set()
                for s in snakes.values(): allocc|=set(s['body'])
                if (fx,fy) not in allocc and (fx,fy) not in food:
                    food.append((fx,fy)); break
        # eliminations
        dead=set()
        for sid,s in snakes.items():
            hx,hy=s['body'][0]
            if not (0<=hx<W and 0<=hy<H): dead.add(sid); continue
            if s['health']<=0: dead.add(sid); continue
            # self collision (head hits own body[1:])
            if s['body'][0] in s['body'][1:]: dead.add(sid); continue
        # collisions between snakes
        ids=list(snakes)
        for a in ids:
            for b in ids:
                if a==b: continue
                if a in dead: continue
                ha=snakes[a]['body'][0]
                # hit b's body (not head)
                if ha in snakes[b]['body'][1:]: dead.add(a)
                # head-to-head
                if ha==snakes[b]['body'][0]:
                    la,lb=len(snakes[a]['body']),len(snakes[b]['body'])
                    if la<=lb: dead.add(a)
        for d in dead: del snakes[d]
        if 'me' not in snakes and 'opp' not in snakes: return 'tie',turn
        if 'opp' not in snakes: return 'me',turn
        if 'me' not in snakes: return 'opp',turn
    return 'tie',200

res={'me':0,'opp':0,'tie':0}
for s in range(40):
    w,t=play(s); res[w]+=1
print(res)
