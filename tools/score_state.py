#!/usr/bin/env python3
# crude: monkeypatch by copying main.move? Instead print selected move and board
import json,sys,os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main
p=sys.argv[1]; turn=int(sys.argv[2])
for line in open(p):
 o=json.loads(line)
 if o.get('turn')==turn:
  me=next(sn for sn in o['board']['snakes'] if sn['name']=='gpt-5-5')
  o['you']=me
  print('move',main.move(o))
  print('food',o['board']['food'])
  for s in o['board']['snakes']: print(s['name'],s['health'],s['length'],s['head'],s['body'])
