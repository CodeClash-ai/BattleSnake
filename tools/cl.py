import json,glob,sys
d=sys.argv[1] if len(sys.argv)>1 else "/logs/rounds/0"
wins=losses=ties=0
lossinfo=[]
for f in sorted(glob.glob(d+"/sim_*.jsonl")):
    lines=open(f).read().strip().split("\n")
    if not lines or not lines[-1].strip(): continue
    try: last=json.loads(lines[-1])
    except: continue
    wn=last.get("winnerName"); isd=last.get("isDraw")
    if isd: ties+=1; continue
    if wn=="opus-4-8": wins+=1; continue
    losses+=1
    # find last frame where opus alive
    us=op=None; head=None; usl=opl=0; hp=0; legal=0; food=0
    for ln in lines:
        try: fr=json.loads(ln)
        except: continue
        b=fr.get("board") or fr
        snakes=b.get("snakes") or b.get("Snakes") or []
        me=en=None
        for s in snakes:
            nm=s.get("name","")
            if nm=="opus-4-8": me=s
            else: en=s
        if me:
            body=me.get("body") or me.get("Body") or []
            if body:
                h=body[0]; head=(h.get("x",h.get("X")),h.get("y",h.get("Y")))
                usl=len(body); hp=me.get("health",me.get("Health",0))
                food=len(b.get("food") or b.get("Food") or [])
            if en:
                eb=en.get("body") or en.get("Body") or []
                opl=len(eb)
    tag="OUTGROWN" if opl>usl else "SELFCOIL"
    onwall = head and (head[0] in (0,10) or head[1] in (0,10))
    lossinfo.append((f.split("/")[-1],tag,usl,hp,opl,head,"wall" if onwall else "mid"))
print(f"W={wins} L={losses} T={ties}")
og=sum(1 for x in lossinfo if x[1]=="OUTGROWN")
sc=sum(1 for x in lossinfo if x[1]=="SELFCOIL")
wl=sum(1 for x in lossinfo if x[6]=="wall")
print(f"OUTGROWN={og} SELFCOIL={sc} wall_deaths={wl}")
for x in lossinfo[:25]: print(x)
