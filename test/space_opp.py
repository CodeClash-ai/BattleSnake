"""Strong space-control opponent proxy for astar-snake: pure flood-fill space
maximizer + tail-chase + light food. Survives long, contests space aggressively.
"""
from collections import deque
DIRS={"up":(0,1),"down":(0,-1),"left":(-1,0),"right":(1,0)}
def info(): return {"apiversion":"1","author":"t","color":"#ff8800","head":"tiger","tail":"bolt"}
def start(g): return None
def end(g): return None
def move(g):
    try: return {"move":_m(g)}
    except Exception: return {"move":"up"}
def _flood(head,occ,W,H,limit):
    seen={head}; q=deque([head]); c=0
    while q and c<limit:
        x,y=q.popleft(); c+=1
        for dx,dy in DIRS.values():
            n=(x+dx,y+dy)
            if 0<=n[0]<W and 0<=n[1]<H and n not in seen and n not in occ:
                seen.add(n); q.append(n)
    return c
def _m(g):
    b=g["board"]; W=b["width"]; H=b["height"]; you=g["you"]
    body=[(s["x"],s["y"]) for s in you["body"]]; head=body[0]; mylen=you["length"]; hp=you["health"]
    occ=set()
    for s in b["snakes"]:
        bd=[(c["x"],c["y"]) for c in s["body"]]
        for seg in bd[:-1]: occ.add(seg)
        if s["health"]==100: occ.add(bd[-1])
    opps=[s for s in b["snakes"] if s["id"]!=you["id"]]
    enext={}
    for s in opps:
        oh=(s["body"][0]["x"],s["body"][0]["y"]); ol=s["length"]
        for dx,dy in DIRS.values():
            c=(oh[0]+dx,oh[1]+dy); enext[c]=max(enext.get(c,0),ol)
    food=[(f["x"],f["y"]) for f in b["food"]]
    def ib(c): return 0<=c[0]<W and 0<=c[1]<H
    best=None; bestsc=-1e9
    for nm,(dx,dy) in DIRS.items():
        nc=(head[0]+dx,head[1]+dy)
        if not ib(nc) or nc in occ: continue
        if enext.get(nc,0)>mylen: continue
        if enext.get(nc,0)==mylen: 
            sc_pen=-500
        else: sc_pen=0
        sp=_flood(nc,occ,W,H,W*H)
        sc=sp*10+sc_pen
        if sp<mylen: sc-=(mylen-sp)*80
        if food and (hp<50 or mylen<=max([s["length"] for s in opps]+[0])):
            fd=min(abs(nc[0]-f[0])+abs(nc[1]-f[1]) for f in food)
            sc-=fd*2.0
        # center pull mild
        sc-=(abs(nc[0]-W//2)+abs(nc[1]-H//2))*0.5
        if sc>bestsc: bestsc=sc; best=nm
    return best or "up"
