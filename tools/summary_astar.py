#!/usr/bin/env python3
import glob,json,os,sys,statistics,collections
root=sys.argv[1]
rows=[]
for path in glob.glob(root+'/sim_*.jsonl'):
 if os.path.getsize(path)==0: continue
 states=[]; winner=None
 for line in open(path):
  o=json.loads(line)
  if 'turn'in o: states.append(o)
  elif 'winnerName'in o: winner=o.get('winnerName') or 'DRAW'
 if not states: continue
 st=states[-2] if states[-1]["you"].get("name")!="gpt-5-5" and len(states)>1 else states[-1]
 ss=st['board']['snakes']
 mine=next((s for s in ss if s['name']=='gpt-5-5'),None); opp=next((s for s in ss if s['name']!='gpt-5-5'),None)
 if not mine or not opp: continue
 rows.append((winner,st['turn'],mine['length']-opp['length'],mine['health']-opp['health'],mine['length'],opp['length'],path))
for k,grp in collections.defaultdict(list,{}).items(): pass
by=collections.defaultdict(list)
for r in rows: by[r[0]].append(r)
for w,g in by.items():
 print(w,len(g),'turn avg',statistics.mean(r[1] for r in g),'lendiff avg',statistics.mean(r[2] for r in g),'hpdiff avg',statistics.mean(r[3] for r in g))
 print(' lendiff counts',collections.Counter(r[2] for r in g).most_common(10))
print('loss samples by diff')
for r in sorted([r for r in rows if r[0] not in ('gpt-5-5','DRAW')], key=lambda x:(x[2],x[1]))[:20]: print(r)
