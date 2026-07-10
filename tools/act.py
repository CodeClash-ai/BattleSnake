import json,glob
d="/logs/rounds/0"
tot=0;to=0;glens=[]
for f in sorted(glob.glob(d+"/sim_*.jsonl"))[:60]:
    lines=open(f).read().strip().split("\n")
    frames=[json.loads(l) for l in lines if l.strip() and l.strip()[0]=="{"]
    if frames:
        glens.append(frames[-1].get("turn",0) if "turn" in frames[-1] else (frames[-1].get("board") or {}).get("turn",len(frames)))
    for fr in frames:
        b=fr.get("board") or fr
        for s in b.get("snakes",[]):
            if s.get("name")!="opus-4-8":
                lat=s.get("latency","0")
                try: lat=float(lat)
                except: lat=0
                if lat>0: tot+=1
                if lat>=490: to+=1
print("opp moves sampled",tot,"timeouts>=490",to)
print("avg game len", sum(glens)/len(glens) if glens else 0, "max", max(glens) if glens else 0)
