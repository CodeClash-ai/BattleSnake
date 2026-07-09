import json, glob, os
for r in [0,1,2]:
    wins=losses=ties=0
    loss_files=[]
    for f in sorted(glob.glob(f'/logs/rounds/{r}/sim_*.jsonl')):
        try:
            with open(f) as fh:
                lines=fh.readlines()
            if not lines: continue
            last=json.loads(lines[-1])
            if last.get('isDraw'): 
                ties+=1
            elif last.get('winnerName')=='opus-4-7':
                wins+=1
            else:
                losses+=1
                loss_files.append(f)
        except Exception as e:
            pass
    print(f"Round {r}: W={wins} L={losses} T={ties}  loss_files={len(loss_files)}")
    for lf in loss_files[:3]:
        print(f"  loss: {lf}")
