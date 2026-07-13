"""Quick local batch runner against tools/nbw_ruby_opponent.py."""
import collections, json, os, subprocess, time
N=int(os.environ.get('N','50'))
me=subprocess.Popen(['python3','main.py'],cwd='/workspace',env=dict(os.environ,PORT='8000'),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
opp=subprocess.Popen(['python3','tools/nbw_ruby_opponent.py'],cwd='/workspace',env=dict(os.environ,PORT='8001'),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1)
ctr=collections.Counter(); turns=[]; bad=[]
try:
  for seed in range(N):
    out=f'/tmp/nbwruby_{seed}.jsonl'
    try:
      subprocess.run(['./game/battlesnake','play','-W','11','-H','11','-n','gpt-5-5','-u','http://127.0.0.1:8000','-n','nbw__nbw-ruby','-u','http://127.0.0.1:8001','-r',str(seed),'-o',out],cwd='/workspace',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
      states=[json.loads(l) for l in open(out) if '"turn"' in l]
      last=states[-1]; alive=[s['name'] for s in last['board']['snakes']]
      if 'gpt-5-5' in alive and 'nbw__nbw-ruby' not in alive: res='win'
      elif 'nbw__nbw-ruby' in alive and 'gpt-5-5' not in alive: res='loss'
      elif 'nbw__nbw-ruby' not in alive and 'gpt-5-5' not in alive: res='tie'
      else: res='both'
      ctr[res]+=1; turns.append(last['turn'])
      if res!='win': bad.append((seed,res,last['turn']))
    except Exception as e:
      ctr['err']+=1; bad.append((seed,'err',repr(e)))
  print(ctr,'avgturn',sum(turns)/len(turns) if turns else None,'bad',bad[:50])
finally:
  for p in (me,opp):
    p.terminate()
    try: p.wait(timeout=2)
    except Exception: p.kill()
