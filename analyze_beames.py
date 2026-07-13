import json, glob, sys
shorter=equal=longer=0
edgedeaths=0
early=0
losses=[]
for f in sorted(glob.glob('/logs/rounds/0/sim_*.jsonl')):
    lines=open(f).read().strip().split('\n')
    if not lines or not lines[-1].strip(): continue
    try: last=json.loads(lines[-1])
    except: continue
    wn=last.get('winnerName','')
    if 'opus' in wn.lower(): continue
    if wn=='' : continue  # draw
    # find last frame with both snakes to get lengths
    # reconstruct: parse the last full turn state
    # frames are per-turn; get opus & opp length near death
    opus_len=opp_len=None
    turn=last.get('turn',0)
    for ln in reversed(lines):
        try: d=json.loads(ln)
        except: continue
        board=d.get('board') or d
        snakes=board.get('snakes') if isinstance(board,dict) else None
        if not snakes:
            # maybe format different
            snakes=d.get('snakes')
        if snakes:
            for s in snakes:
                nm=s.get('name','')
                L=s.get('length',len(s.get('body',[])))
                if 'opus' in nm.lower(): opus_len=L
                else: opp_len=L
            if opus_len and opp_len: break
    if opus_len and opp_len:
        if opus_len<opp_len: shorter+=1
        elif opus_len==opp_len: equal+=1
        else: longer+=1
        losses.append((f.split('/')[-1],turn,opus_len,opp_len))
print("shorter(us):",shorter,"equal:",equal,"longer(us):",longer)
for l in losses[:30]: print(l)
