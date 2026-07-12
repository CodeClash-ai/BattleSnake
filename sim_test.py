"""Lightweight local simulator to test bots vs each other (standard, 11x11, 2 snakes).
Not a perfect replica of the Go engine but captures core rules well enough
for relative comparison. Usage: python3 sim_test.py [num_games]
"""
import random, sys, importlib.util, copy

W = H = 11
MAX_HEALTH = 100

def load(path):
    spec = importlib.util.spec_from_file_location(path.replace('/','_').replace('.',''), path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

DIRS = {"up":(0,1),"down":(0,-1),"left":(-1,0),"right":(1,0)}

def make_state(snakes, food, turn):
    board = {"width":W,"height":H,"food":[{"x":x,"y":y} for x,y in food],
             "hazards":[],"snakes":[]}
    for s in snakes:
        board["snakes"].append({"id":s["id"],"name":s["id"],"health":s["health"],
            "body":[{"x":x,"y":y} for x,y in s["body"]],
            "head":{"x":s["body"][0][0],"y":s["body"][0][1]},"length":len(s["body"])})
    return board

def run_game(botA, botB, seed):
    rng = random.Random(seed)
    # start positions (corners-ish like real engine)
    snakes = [
        {"id":"A","health":MAX_HEALTH,"body":[(1,1)]*3,"bot":botA,"alive":True},
        {"id":"B","health":MAX_HEALTH,"body":[(9,9)]*3,"bot":botB,"alive":True},
    ]
    food = set([(5,5),(0,2),(10,8)])
    for turn in range(500):
        board = make_state([s for s in snakes], list(food), turn)
        moves = {}
        for s in snakes:
            if not s["alive"]: continue
            gs = {"game":{"id":"g"},"turn":turn,"board":copy.deepcopy(board),
                  "you":next(x for x in board["snakes"] if x["id"]==s["id"])}
            try:
                mv = s["bot"].move(gs).get("move","up")
            except Exception:
                mv = "up"
            moves[s["id"]] = mv if mv in DIRS else "up"
        # apply moves
        for s in snakes:
            if not s["alive"]: continue
            dx,dy = DIRS[moves[s["id"]]]
            hx,hy = s["body"][0]
            newhead = (hx+dx, hy+dy)
            s["body"] = [newhead] + s["body"]
            s["health"] -= 1
            if newhead in food:
                s["health"] = MAX_HEALTH
                food.discard(newhead)
            else:
                s["body"].pop()
        # spawn food occasionally / minimum food
        if len(food) < 1 or rng.randint(0,99) < 15:
            empty = [(x,y) for x in range(W) for y in range(H)
                     if (x,y) not in food and all((x,y) not in s["body"] for s in snakes if s["alive"])]
            if empty and (len(food)<1 or rng.randint(0,99)<15):
                food.add(rng.choice(empty))
        # eliminations
        for s in snakes:
            if not s["alive"]: continue
            head = s["body"][0]
            if not (0<=head[0]<W and 0<=head[1]<H):
                s["alive"]=False; continue
            if s["health"]<=0:
                s["alive"]=False; continue
        # collisions
        dead=set()
        alive=[s for s in snakes if s["alive"]]
        for s in alive:
            head=s["body"][0]
            for o in alive:
                if o is s:
                    if head in s["body"][1:]:
                        dead.add(s["id"])
                else:
                    if head in o["body"][1:]:
                        dead.add(s["id"])
                    elif head==o["body"][0]:
                        if len(s["body"])<=len(o["body"]):
                            dead.add(s["id"])
        for s in snakes:
            if s["id"] in dead: s["alive"]=False
        alive=[s for s in snakes if s["alive"]]
        if len(alive)<=1:
            if len(alive)==1: return alive[0]["id"], turn
            return "draw", turn
    return "draw", 500

if __name__=="__main__":
    n = int(sys.argv[1]) if len(sys.argv)>1 else 100
    me = load("main.py")
    opp = load("main_naive_backup.py")
    winsA=winsB=draws=0
    for i in range(n):
        # alternate start advantage by swapping
        if i%2==0:
            r,_ = run_game(me,opp,i)
            if r=="A": winsA+=1
            elif r=="B": winsB+=1
            else: draws+=1
        else:
            r,_ = run_game(opp,me,i)
            if r=="B": winsA+=1
            elif r=="A": winsB+=1
            else: draws+=1
    print(f"me wins: {winsA}, opp wins: {winsB}, draws: {draws} (of {n})")
