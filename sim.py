"""Lightweight standard-ruleset simulator for local testing (1v1, 11x11).
Not 100% engine-faithful but close enough for A/B testing bots.
Usage: python3 sim.py <N_games>
"""
import importlib, random, sys, copy

W = H = 11
FOOD_SPAWN_CHANCE = 15
MIN_FOOD = 1

def load(mod):
    m = importlib.import_module(mod)
    importlib.reload(m)
    return m

DIRS = {"up":(0,1),"down":(0,-1),"left":(-1,0),"right":(1,0)}

def make_state(snakes, food, turn):
    return {
        "board": {"width":W,"height":H,
                  "snakes":[snake_json(s) for s in snakes if s["alive"]],
                  "food":[{"x":x,"y":y} for x,y in food],
                  "hazards":[]},
        "turn": turn,
        "game":{"id":"sim","ruleset":{"name":"standard","settings":{}},"map":"standard","timeout":500},
    }

def snake_json(s):
    return {"id":s["id"],"name":s["id"],"health":s["health"],
            "body":[{"x":x,"y":y} for x,y in s["body"]],
            "head":{"x":s["body"][0][0],"y":s["body"][0][1]},
            "length":len(s["body"]),"latency":"0","shout":""}

def run_game(botA, botB, seed):
    rng = random.Random(seed)
    # standard start positions (corners-ish)
    starts = [(1,9),(9,1),(9,9),(1,1),(1,5),(9,5),(5,1),(5,9)]
    rng.shuffle(starts)
    snakes = []
    for i,(bot,name) in enumerate([(botA,"A"),(botB,"B")]):
        p = starts[i]
        snakes.append({"id":name,"bot":bot,"health":100,"body":[p,p,p],"alive":True})
    # initial food: one near each snake + center
    food = set()
    food.add((5,5))
    for s in snakes:
        hx,hy=s["body"][0]
        # place food 2 diagonal
        food.add((min(max(hx+ (1 if hx<5 else -1),0),W-1), hy))
    food=set(food)

    for turn in range(500):
        alive = [s for s in snakes if s["alive"]]
        if len(alive)<=1:
            break
        moves={}
        for s in alive:
            state = make_state(snakes, food, turn)
            state["you"] = snake_json(s)
            try:
                mv = s["bot"].move(state).get("move","up")
            except Exception:
                mv="up"
            if mv not in DIRS: mv="up"
            moves[s["id"]]=mv
        # apply moves
        for s in alive:
            dx,dy=DIRS[moves[s["id"]]]
            hx,hy=s["body"][0]
            s["body"]=[(hx+dx,hy+dy)]+s["body"][:-1]
            s["health"]-=1
        # food consumption
        ate=set()
        for s in alive:
            head=s["body"][0]
            if head in food:
                s["health"]=100
                s["body"].append(s["body"][-1])
                ate.add(head)
        food-=ate
        # eliminations
        for s in alive:
            head=s["body"][0]
            if not (0<=head[0]<W and 0<=head[1]<H):
                s["alive"]=False; continue
            if s["health"]<=0:
                s["alive"]=False; continue
        # collisions
        for s in alive:
            if not s["alive"]: continue
            head=s["body"][0]
            # self / body collisions
            for o in alive:
                if o["body"] and head in o["body"][1:]:
                    s["alive"]=False; break
        # head to head
        for s in alive:
            if not s["alive"]: continue
            head=s["body"][0]
            for o in alive:
                if o["id"]==s["id"]: continue
                if o["body"][0]==head:
                    if len(o["body"])>=len(s["body"]):
                        s["alive"]=False
        # spawn food
        if len(food)<MIN_FOOD or rng.randint(1,100)<=FOOD_SPAWN_CHANCE:
            empty=[(x,y) for x in range(W) for y in range(H)
                   if (x,y) not in food and not any((x,y) in ss["body"] for ss in snakes if ss["alive"])]
            if empty and (len(food)<MIN_FOOD or rng.randint(1,100)<=FOOD_SPAWN_CHANCE):
                food.add(rng.choice(empty))
    alive=[s for s in snakes if s["alive"]]
    if len(alive)==1: return alive[0]["id"]
    return "tie"

if __name__=="__main__":
    n=int(sys.argv[1]) if len(sys.argv)>1 else 100
    A=load("main"); B=load("main_original_backup")
    res={"A":0,"B":0,"tie":0}
    for i in range(n):
        r=run_game(A,B,i*7+1)
        res[r]+=1
    print(f"Games={n}  A(new main)={res['A']}  B(original)={res['B']}  tie={res['tie']}")
