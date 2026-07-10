import json,glob
d="/logs/rounds/0"
gaps={}
for f in sorted(glob.glob(d+"/sim_*.jsonl")):
    lines=open(f).read().strip().split("\n")
    if not lines: continue
    try: last=json.loads(lines[-1])
    except: continue
    if last.get("isDraw") or last.get("winnerName")=="opus-4-8": continue
    usl=opl=0
    for ln in lines:
        try: fr=json.loads(ln)
        except: continue
        b=fr.get("board") or fr
        for s in (b.get("snakes") or []):
            if s.get("name")=="opus-4-8":
                usl=len(s.get("body") or [])
            else:
                opl=len(s.get("body") or [])
    g=opl-usl
    gaps[g]=gaps.get(g,0)+1
for g in sorted(gaps): print(f"opp-us gap {g:+d}: {gaps[g]} losses")
