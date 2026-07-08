# Robust win/loss analysis using winnerName (works for any opponent series).
# Usage: python3 analyze_winner.py [/logs/rounds/N]  (default: rounds/2)
import json, glob, os, sys, statistics
d = sys.argv[1] if len(sys.argv) > 1 else "/logs/rounds/2"
w = l = t = 0; lens = []; loss_files = []
for f in glob.glob(d + "/sim_*.jsonl"):
    txt = open(f).read().strip()
    if not txt: continue
    lines = [x for x in txt.split("\n") if x.strip()]
    last = json.loads(lines[-1])
    maxt = 0
    for ln in lines:
        try:
            o = json.loads(ln)
            if isinstance(o, dict) and "turn" in o: maxt = max(maxt, o["turn"])
        except: pass
    lens.append(maxt)
    if last.get("isDraw"): t += 1
    elif last.get("winnerName") == "opus-4-8": w += 1
    else: l += 1; loss_files.append(os.path.basename(f))
print(f"dir={d}")
print(f"games={w+l+t} wins={w} losses={l} ties={t}")
if lens: print(f"avg_turns={round(statistics.mean(lens),1)} max={max(lens)} min={min(lens)}")
print("losses:", loss_files)
