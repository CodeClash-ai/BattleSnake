import json,sys
f="/logs/rounds/0/"+sys.argv[1]
start=int(sys.argv[2]) if len(sys.argv)>2 else 0
lines=open(f).read().strip().split("\n")
for i,ln in enumerate(lines):
    try: fr=json.loads(ln)
    except: continue
    b=fr.get("board") or fr
    t=fr.get("turn",i)
    if t<start: continue
    me=en=None
    for s in (b.get("snakes") or []):
        if s.get("name")=="opus-4-8": me=s
        else: en=s
    if not me: continue
    mb=me.get("body") or []; eb=en.get("body") or [] if en else []
    mh=(mb[0]["x"],mb[0]["y"]) if mb else None
    eh=(eb[0]["x"],eb[0]["y"]) if eb else None
    food=[(x["x"],x["y"]) for x in (b.get("food") or [])]
    print(f"t{t} US{mh} L{len(mb)} hp{me.get('health')} | OP{eh} L{len(eb)} | food{food}")
