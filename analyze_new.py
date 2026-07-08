import json, glob, os
d="/logs/rounds/2"
wins=losses=ties=0
turns_list=[]
loss_files=[]
for f in sorted(glob.glob(d+"/sim_*.jsonl")):
    if os.path.getsize(f)==0: continue
    lines=open(f).read().strip().split("\n")
    # find last board state
    last=None
    for ln in lines:
        try:
            o=json.loads(ln)
            if "board" in o and "turn" in o:
                last=o
        except: pass
    if not last: continue
    snakes=last["board"]["snakes"]
    turn=last["turn"]
    alive={s["name"]:s for s in snakes}
    me="opus-4-8" in alive
    opp="Nettogrof__nessegrev-julia" in alive
    turns_list.append(turn)
    if me and not opp: wins+=1
    elif opp and not me: losses+=1; loss_files.append((os.path.basename(f),turn))
    else: ties+=1
print(f"games={len(turns_list)} wins={wins} losses={losses} ties={ties}")
print(f"avg_turns={sum(turns_list)/len(turns_list):.1f} max={max(turns_list)} min={min(turns_list)}")
print("losses:", loss_files[:20])
