import json, sys, glob, os
d=sys.argv[1] if len(sys.argv)>1 else "/logs/rounds/0"
losses=[]
for f in sorted(glob.glob(os.path.join(d,"sim_*.jsonl"))):
    lines=[l for l in open(f) if l.strip()]
    if not lines: continue
    last=json.loads(lines[-1])
    if last.get("winnerName")=="opus-4-8": continue
    # find last turn frame
    frames=[]
    for l in lines:
        j=json.loads(l)
        if "turn" in j: frames.append(j)
    if not frames: continue
    lf=frames[-1]
    snakes={s["name"]:s for s in lf["board"]["snakes"]} if "board" in lf else {}
    # need pre-death: find opus in last frame with snakes
    turn=lf.get("turn")
    # gather lengths from second-to-last frame with both
    opus=None;opp=None
    for fr in reversed(frames):
        sn={s["name"]:s for s in fr.get("board",{}).get("snakes",[])}
        if "opus-4-8" in sn:
            opus=sn["opus-4-8"]; 
            for k in sn:
                if k!="opus-4-8": opp=sn[k]
            turn=fr.get("turn")
            break
    ol=opus.get("length",len(opus["body"])) if opus else None
    oh=opus["body"][0] if opus else None
    pl=opp.get("length",len(opp["body"])) if opp else None
    losses.append((os.path.basename(f),turn,ol,pl,(oh["x"],oh["y"]) if oh else None,last.get("isDraw")))
print("num losses:",len(losses))
import collections
short=eq=lng=0
for f,t,ol,pl,oh,dr in losses:
    if ol is None or pl is None: continue
    if ol<pl: short+=1
    elif ol==pl: eq+=1
    else: lng+=1
print("shorter:",short,"equal:",eq,"longer:",lng)
# death turns
turns=[t for f,t,ol,pl,oh,dr in losses if t]
print("median turn:",sorted(turns)[len(turns)//2] if turns else None,"min",min(turns) if turns else None,"max",max(turns) if turns else None)
# head positions on edge?
edgedeaths=sum(1 for f,t,ol,pl,oh,dr in losses if oh and (oh[0] in (0,10) or oh[1] in (0,10)))
print("edge/corner head deaths:",edgedeaths)
for f,t,ol,pl,oh,dr in losses[:25]:
    print(f,"turn",t,"opusL",ol,"oppL",pl,"opusHead",oh)
