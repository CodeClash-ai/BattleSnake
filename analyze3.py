import json, glob
d = "/logs/rounds/3"
opus_survives=0
opus_dies=0
for f in sorted(glob.glob(d+"/sim_*.jsonl")):
    lines=open(f).read().strip().split("\n")
    board_frames=[json.loads(l) for l in lines if '"board"' in l]
    if not board_frames: continue
    last=board_frames[-1]
    names=[s["name"] for s in last["board"]["snakes"]]
    if "opus-4-8" in names:
        opus_survives+=1
    else:
        opus_dies+=1
        print("OPUS DIED in", f, "turn", last.get("turn"))
print("survives:",opus_survives,"dies:",opus_dies)
