import json,sys,glob
d=sys.argv[1] if len(sys.argv)>1 else "/logs/rounds/0"
wins=losses=ties=0
lossinfo=[]
for f in sorted(glob.glob(d+"/sim_*.jsonl")):
    lines=open(f).read().strip().split("\n")
    if not lines: continue
    try: last=json.loads(lines[-1])
    except: continue
    wn=last.get("winnerName","")
    isd=last.get("isDraw",False)
    if isd: ties+=1; continue
    if wn=="opus-4-8": wins+=1; continue
    if not wn: continue
    losses+=1
    # find last frame where opus alive
    us=op=None
    for ln in reversed(lines):
        try: fr=json.loads(ln)
        except: continue
        board=fr.get("board") or fr
        snakes=board.get("snakes",[])
        u=[s for s in snakes if s.get("name")=="opus-4-8"]
        o=[s for s in snakes if s.get("name")!="opus-4-8"]
        if u:
            us=u[0]; op=o[0] if o else None; break
    if us:
        ul=us.get("length",len(us.get("body",[])))
        ol=op.get("length",len(op.get("body",[]))) if op else 0
        h=us.get("body",[{}])[0]
        hd=(h.get("x"),h.get("y")) if isinstance(h,dict) else h
        hp=us.get("health",0)
        onwall = hd[0] in (0,10) or hd[1] in (0,10) if hd[0] is not None else False
        mode="OUTGROWN" if ol>ul else "SELFCOIL"
        lossinfo.append((f.split("/")[-1],mode,ul,ol,hp,hd,onwall))
print("W %d L %d T %d"%(wins,losses,ties))
out=sum(1 for x in lossinfo if x[1]=="OUTGROWN")
coil=sum(1 for x in lossinfo if x[1]=="SELFCOIL")
wall=sum(1 for x in lossinfo if x[6])
print("OUTGROWN %d SELFCOIL %d onwall %d"%(out,coil,wall))
for x in lossinfo[:40]: print(x)
