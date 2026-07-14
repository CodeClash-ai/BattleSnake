"""Smart test opponent: flood-fill survival + pursuit + center control.
Mimics a genuine combat opponent (like kreuzotter) to stress-test main.py.
"""
from collections import deque
DIRS={"up":(0,1),"down":(0,-1),"left":(-1,0),"right":(1,0)}
def info(): return {"apiversion":"1","author":"t","color":"#00ff00","head":"beluga","tail":"bolt"}
def start(g): return None
def end(g): return None
def move(g):
    try: return {"move":_m(g)}
    except Exception: return {"move":"up"}
def _m(g):
    b=g["board"]; W=b["width"]; H=b["height"]; you=g["you"]
    body=[(s["x"],s["y"]) for s in you["body"]]; head=body[0]; mylen=you["length"]
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
    def ib(c): return 0<=c[0]<W and 0<=c[1]<H
    cands=[]
    for nm,(dx,dy) in DIRS.items():
        nc=(head[0]+dx,head[1]+dy)
        if not ib(nc) or nc in occ: continue
        lose=enext.get(nc,0)>=mylen
        cands.append((nm,nc,lose))
    if not cands: return "up"
    def flood(sc):
        seen={sc}; dq=deque([sc]); cnt=0
        while dq:
            cur=dq.popleft(); cnt+=1
            for dx,dy in DIRS.values():
                nn=(cur[0]+dx,cur[1]+dy)
                if nn in seen or not ib(nn) or nn in occ: continue
                seen.add(nn); dq.append(nn)
        return cnt
    food=[(f["x"],f["y"]) for f in b["food"]]
    ophead=(opps[0]["body"][0]["x"],opps[0]["body"][0]["y"]) if opps else None
    cx,cy=W//2,H//2
    def sc(c):
        nm,nc,lose=c; s=0.0
        if lose: s-=1000
        s+=flood(nc)*3
        # pursue enemy head
        if ophead: s-=(abs(nc[0]-ophead[0])+abs(nc[1]-ophead[1]))*2
        # center control
        s-=(abs(nc[0]-cx)+abs(nc[1]-cy))*0.5
        if you["health"]<50 and food:
            s-=min(abs(nc[0]-f[0])+abs(nc[1]-f[1]) for f in food)*1.5
        return s
    cands.sort(key=sc,reverse=True)
    return cands[0][0]
