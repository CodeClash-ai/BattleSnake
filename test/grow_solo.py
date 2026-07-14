# Grow-solo stress test: our bot alone with lots of food, many turns.
# Directly tests the DOMINANCE SELF-COIL failure mode vs coreyja__eremetic-eric:
# we grow HUGE (len 40-60) and must NOT seal ourselves in.
import sys
sys.path.insert(0, '/workspace')
import main, random
W=H=11
DIRS=main.DIRS

def run(seed, turns=600, nfood=6):
    random.seed(seed)
    body=[(5,5),(5,4),(5,3)]
    health=100; length=3
    foods=set()
    while len(foods)<nfood:
        foods.add((random.randrange(W),random.randrange(H)))
    for turn in range(turns):
        st={"turn":turn,"board":{"width":W,"height":H,
            "food":[{"x":f[0],"y":f[1]} for f in foods],
            "hazards":[],
            "snakes":[{"id":"me","name":"opus-4-8","length":length,"health":health,
                       "body":[{"x":b[0],"y":b[1]} for b in body]}]},
            "you":{"id":"me","name":"opus-4-8","length":length,"health":health,
                   "body":[{"x":b[0],"y":b[1]} for b in body]}}
        mv=main.move(st)["move"]
        dx,dy=DIRS[mv]
        nh=(body[0][0]+dx,body[0][1]+dy)
        # collision checks
        if not(0<=nh[0]<W and 0<=nh[1]<H):
            return ('WALL',turn,length,nh)
        if nh in set(body[:-1]):
            return ('SELF',turn,length,nh)
        ate = nh in foods
        body=[nh]+body
        if ate:
            foods.discard(nh)
            length+=1; health=100
            # respawn a food
            while len(foods)<nfood:
                nf=(random.randrange(W),random.randrange(H))
                if nf not in set(body) and nf not in foods:
                    foods.add(nf)
        else:
            body=body[:-1]
            health-=1
            if health<=0:
                return ('STARVE',turn,length,nh)
    return ('SURVIVED',turns,length,body[0])

if __name__=="__main__":
    results=[]
    for s in range(int(sys.argv[1]) if len(sys.argv)>1 else 20):
        r=run(s)
        results.append(r)
        print('seed',s,r)
    died=[r for r in results if r[0] not in ('SURVIVED',)]
    print('===',len(results)-len(died),'survived,',len(died),'died',[ (d[0],d[1],d[2]) for d in died])
