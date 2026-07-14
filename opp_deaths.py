"""How does the opponent die? Usage: python3 opp_deaths.py [logdir]
Auto-detects the opponent as the non-'opus-4-8' snake."""
import json, glob, os, sys
logdir = sys.argv[1] if len(sys.argv) > 1 else "/logs/rounds/0"
files = sorted(glob.glob(os.path.join(logdir, "sim_*.jsonl")))
wall = 0; other = 0; opp_survived = 0
for f in files:
    if os.path.getsize(f) == 0:
        continue
    lines = [l for l in open(f).read().strip().split("\n") if l.strip()]
    boards = [json.loads(l) for l in lines if '"turn"' in l]
    if len(boards) < 2:
        continue
    # find last board where opp present, and its head at that time
    prev_opp = None
    W = boards[0]['board']['width']; H = boards[0]['board']['height']
    for b in boards:
        opp = None
        for s in b['board']['snakes']:
            if s['name'] != 'opus-4-8':
                opp = s
        if opp is None:
            break
        prev_opp = opp
    else:
        opp_survived += 1
        continue
    if prev_opp is None:
        continue
    h = prev_opp['head']
    # can't easily know exact death cause from last-alive frame; approximate:
    # near a wall = likely wall death
    if h['x'] <= 0 or h['x'] >= W - 1 or h['y'] <= 0 or h['y'] >= H - 1:
        wall += 1
    else:
        other += 1
print("opp died near wall:", wall, "| died mid-board (trap/h2h):", other,
      "| opp survived to end:", opp_survived)
