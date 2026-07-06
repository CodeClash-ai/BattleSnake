import json,sys
f=sys.argv[1]; target=int(sys.argv[2]); me="opus-4-8"
lines=[json.loads(l) for l in open(f) if l.strip()]
turns=[l for l in lines if "turn" in l and "board" in l]
t=[x for x in turns if x["turn"]==target][0]
b=t["board"]; W,H=b["width"],b["height"]
grid=[["." for _ in range(W)] for _ in range(H)]
for s in b["snakes"]:
    c='M' if s["name"]==me else 'E'
    for i,seg in enumerate(s["body"]):
        ch = c if i>0 else c.lower()
        if 0<=seg["y"]<H and 0<=seg["x"]<W:
            grid[seg["y"]][seg["x"]]=ch
for fd in b["food"]:
    if grid[fd["y"]][fd["x"]]==".": grid[fd["y"]][fd["x"]]="*"
for y in range(H-1,-1,-1):
    print("".join(grid[y]))
ms=[s for s in b["snakes"] if s["name"]==me][0]
print("my head",ms["head"],"len",ms["length"])
