import json,sys,glob
d=sys.argv[2] if len(sys.argv)>2 else "/logs/rounds/0"
gid=sys.argv[1]
f=d+"/"+gid+".jsonl"
lines=open(f).read().strip().split("\n")
start=int(sys.argv[3]) if len(sys.argv)>3 else 0
for ln in lines:
    try: fr=json.loads(ln)
    except: continue
    board=fr.get("board") or fr
    t=fr.get("turn",board.get("turn",-1))
    if t<start: continue
    snakes=board.get("snakes",[])
    u=[s for s in snakes if s.get("name")=="opus-4-8"]
    o=[s for s in snakes if s.get("name")!="opus-4-8"]
    if not u: 
        print("t%d US DEAD"%t); break
    us=u[0]; op=o[0] if o else None
    uh=us["body"][0]; 
    fstr=len(board.get("food",[]))
    print("t%d US len%d hp%d head(%d,%d) | OP %s | food%d"%(
        t,us.get("length",len(us["body"])),us.get("health",0),uh["x"],uh["y"],
        ("len%d"%op.get("length",len(op["body"])) if op else "gone"),fstr))
