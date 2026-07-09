# Passive survival bot: avoids walls/self, prefers to stay compact, rarely eats.
def info(): return {"apiversion":"1","author":"p","color":"#88CC88","head":"default","tail":"default"}
def start(gs): return None
def end(gs): return None
def move(gs):
    b=gs["board"]; me=gs["you"]; h=me["body"][0]
    W=b["width"];H=b["height"]
    occ=set()
    for s in b["snakes"]:
        for c in s["body"][:-1]:
            occ.add((c["x"],c["y"]))
    dirs={"up":(0,1),"down":(0,-1),"left":(-1,0),"right":(1,0)}
    best=None;bestn=-1
    for m,(dx,dy) in dirs.items():
        nx,ny=h["x"]+dx,h["y"]+dy
        if nx<0 or ny<0 or nx>=W or ny>=H: continue
        if (nx,ny) in occ: continue
        # count free neighbors (prefer open space, stay alive)
        n=0
        for dx2,dy2 in dirs.values():
            ax,ay=nx+dx2,ny+dy2
            if 0<=ax<W and 0<=ay<H and (ax,ay) not in occ: n+=1
        if n>bestn: bestn=n; best=m
    return {"move": best or "up"}
if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
