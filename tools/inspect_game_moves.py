#!/usr/bin/env python3
import json,sys,os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main
p=sys.argv[1]; start=int(sys.argv[2]) if len(sys.argv)>2 else 0; end=int(sys.argv[3]) if len(sys.argv)>3 else 9999
states=[]; win=None
for line in open(p):
 o=json.loads(line)
 if 'turn'in o and any(sn.get('name')=='gpt-5-5' for sn in o.get('board',{}).get('snakes',[])):
  me=next(sn for sn in o['board']['snakes'] if sn.get('name')=='gpt-5-5')
  o=dict(o); o['you']=me; states.append(o)
 elif 'winnerName'in o: win=o
print(os.path.basename(p), win)
byturn={s['turn']:s for s in states}
for idx,s in enumerate(states):
 t=s['turn']
 if t<start or t>end: continue
 nxt=states[idx+1] if idx+1<len(states) else None
 me=next(sn for sn in s['board']['snakes'] if sn['name']=='gpt-5-5')
 op=next(sn for sn in s['board']['snakes'] if sn['name']!='gpt-5-5')
 h=(me['head']['x'],me['head']['y']); oh=(op['head']['x'],op['head']['y'])
 logged='?'
 if nxt:
  me2=next((sn for sn in nxt['board']['snakes'] if sn['name']=='gpt-5-5'),None)
  if me2:
   h2=(me2['head']['x'],me2['head']['y']); d=(h2[0]-h[0],h2[1]-h[1])
   logged={v:k for k,v in main.MOVES.items()}.get(d,str(d))
 cur=main.move(s).get('move')
 food=[(f['x'],f['y']) for f in s['board'].get('food',[])]
 print(f"t{t} hp{me['health']} len{me['length']} head{h} op hp{op['health']} len{op['length']} head{oh} food{food} logged {logged} cur {cur}")
