"""Local batch eval against copied rdbrck bountysnake2018 opponent."""
import collections, json, os, subprocess, time, sys
N = int(os.environ.get('N','20'))
START = int(os.environ.get('START','0'))
me = subprocess.Popen(['python3','main.py'], cwd='/workspace', env=dict(os.environ, PORT='8000'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
opp = subprocess.Popen(['python3','tools/bountysnake2018_opponent.py'], cwd='/workspace', env=dict(os.environ, PORT='8001', BOUNTY_TIME_LIMIT=os.environ.get('BOUNTY_TIME_LIMIT','0.03')), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ctr=collections.Counter(); turns=[]
try:
  for seed in range(START, START+N):
    out=f'/tmp/bounty_{seed}.jsonl'
    try:
      subprocess.run(['./game/battlesnake','play','-W','11','-H','11','-n','gpt-5-5','-u','http://127.0.0.1:8000','-n','rdbrck__bountysnake2018','-u','http://127.0.0.1:8001','-r',str(seed),'-o',out], cwd='/workspace', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
      states=[json.loads(line) for line in open(out) if '"turn"' in line]
      if not states:
        ctr['nostate']+=1; continue
      last=states[-1]; alive=[s['name'] for s in last['board']['snakes']]
      if 'gpt-5-5' in alive and 'rdbrck__bountysnake2018' not in alive: res='win'
      elif 'rdbrck__bountysnake2018' in alive and 'gpt-5-5' not in alive: res='loss'
      elif 'rdbrck__bountysnake2018' not in alive and 'gpt-5-5' not in alive: res='tie'
      else: res='both'
      ctr[res]+=1; turns.append(last['turn'])
      print(seed, res, last['turn'], flush=True)
    except subprocess.TimeoutExpired:
      ctr['timeout']+=1; print(seed, 'timeout', flush=True)
  print(ctr, 'avgturn', (sum(turns)/len(turns) if turns else None))
finally:
  me.terminate(); opp.terminate()
  try: me.wait(timeout=2); opp.wait(timeout=2)
  except Exception: pass
