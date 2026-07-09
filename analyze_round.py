import json, glob, os
from collections import defaultdict

d="/logs/rounds/4"
games=defaultdict(list)
for f in glob.glob(os.path.join(d,"sim_*.jsonl")):
    lines=open(f).read().strip().split("\n")
    gid=None; frames=[]
    for ln in lines:
        try: o=json.loads(ln)
        except: continue
        if "board" in o:
            gid=o["game"]["id"]; frames.append(o)
    if gid and frames:
        games[gid]=frames

opp_wins=0; opus_wins=0; draws=0; lengths=[]
opp_lat=[]; opus_lat=[]
loss_games=[]
for gid,frames in games.items():
    last=frames[-1]
    snakes=last["board"]["snakes"]
    names=[s["name"] for s in snakes]
    lengths.append(last["turn"])
    # collect latencies
    for fr in frames:
        for s in fr["board"]["snakes"]:
            try: lat=int(s["latency"])
            except: lat=0
            if s["name"].startswith("opus"): opus_lat.append(lat)
            else: opp_lat.append(lat)
    alive=[s["name"] for s in snakes]
    if len(alive)==1:
        if alive[0].startswith("opus"): opus_wins+=1
        else: opp_wins+=1; loss_games.append((gid,frames))
    else:
        draws+=1

print(f"games={len(games)} opus_wins={opus_wins} opp_wins={opp_wins} draws={draws}")
print(f"avg game len={sum(lengths)/len(lengths):.2f} max={max(lengths)}")
import statistics
print(f"opp latency avg={statistics.mean(opp_lat):.1f} max={max(opp_lat)} n>=490={sum(1 for x in opp_lat if x>=490)}/{len(opp_lat)}")
print(f"opus latency avg={statistics.mean(opus_lat):.2f} max={max(opus_lat)}")

# analyze losses
print("\n=== LOSS GAMES (opp won) ===")
for gid,frames in loss_games[:10]:
    last=frames[-1]
    print(f"\ngame {gid[:8]} turns={last['turn']}")
    # who died and how - look at our snake's last position
    for fr in frames[-3:]:
        for s in fr["board"]["snakes"]:
            if s["name"].startswith("opus"):
                print(f"  turn {fr['turn']}: opus head={s['head']} health={s['health']} len={s['length']} lat={s['latency']}")
