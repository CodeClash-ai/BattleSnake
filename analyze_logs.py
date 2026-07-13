import json, glob, os, collections
NAME='gpt-5-5'; OPP='pambrose__pambrose-kotlin'
ctr=collections.Counter(); reasons=collections.Counter(); turns=[]; starts=collections.Counter(); deaths=[]
for path in sorted(glob.glob('/logs/rounds/0/sim_*.jsonl'), key=lambda p:int(os.path.basename(p).split('_')[1].split('.')[0])):
    states=[]
    for line in open(path):
        obj=json.loads(line)
        if 'turn' in obj: states.append(obj)
    if not states: continue
    last=states[-1]
    alive=[s['name'] for s in last['board']['snakes']]
    if NAME in alive and OPP not in alive: res=NAME
    elif OPP in alive and NAME not in alive: res=OPP
    elif NAME not in alive and OPP not in alive: res='Tie'
    else: res='BothAlive'
    ctr[res]+=1; turns.append(last['turn'])
    s0=states[0]['board']
    starts[tuple((sn['name'],sn['head']['x'],sn['head']['y']) for sn in s0['snakes'])]+=1
    if len(states)>=2:
        prev=states[-2]
        prev_alive={sn['name']:sn for sn in prev['board']['snakes']}
        last_alive={sn['name']:sn for sn in last['board']['snakes']}
        for n in [NAME,OPP]:
            if n in prev_alive and n not in last_alive:
                deaths.append((res,path,last['turn'],n,prev_alive[n]['head'],prev_alive[n]['length'],prev_alive[n]['health']))
print('results',ctr,'n',sum(ctr.values()),'avgturn',sum(turns)/len(turns), 'max', max(turns), 'min', min(turns))
print('starts top')
for k,v in starts.most_common(10): print(v,k)
print('sample deaths')
for d in deaths[:20]: print(d)
print('death res counter', collections.Counter((res,n) for res,_,_,n,_,_,_ in deaths))
