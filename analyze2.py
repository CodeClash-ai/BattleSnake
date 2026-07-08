import json, glob
d = "/logs/rounds/2"
# check who dies. Find frames with snake elimination info
myturn_deaths=0
for f in sorted(glob.glob(d+"/sim_*.jsonl"))[:250]:
    lines=open(f).read().strip().split("\n")
    frames=[json.loads(l) for l in lines]
    # find last frame with board
    board_frames=[fr for fr in frames if "board" in fr]
    if not board_frames: continue
    last_board=board_frames[-1]
    # snakes
    snakes = last_board.get("board",{}).get("snakes",[])
    # who's alive
    # actual elimination is in prior frame usually; check death causes
    for fr in board_frames:
        for s in fr.get("board",{}).get("snakes",[]):
            pass
# Instead print structure of a board frame
f=sorted(glob.glob(d+"/sim_0.jsonl"))[0] if False else d+"/sim_0.jsonl"
lines=open(f).read().strip().split("\n")
for l in lines:
    o=json.loads(l)
    if "board" in o:
        print("turn",o.get("turn"),"snakes:",[(s["name"],len(s["body"]),s.get("health")) for s in o["board"]["snakes"]])
