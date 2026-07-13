import subprocess, time, os, sys, json, tempfile
ROOT=os.path.dirname(os.path.dirname(__file__))
p1=subprocess.Popen([sys.executable, os.path.join(ROOT,'main.py')], env=dict(os.environ, PORT='8000'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
p2=subprocess.Popen([sys.executable, os.path.join(ROOT,'tools','untimely_neglected_wearable_opponent.py')], env=dict(os.environ, PORT='8001'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
wins=losses=ties=0
N=int(os.environ.get('N','20'))
try:
  for seed in range(N):
    with tempfile.NamedTemporaryFile(delete=False,suffix='.jsonl') as out:
      cmd=[os.path.join(ROOT,'game','battlesnake'),'play','-W','11','-H','11','-n','gpt-5-5','-u','http://127.0.0.1:8000','-n','altersaddle__untimely-neglected-wearable','-u','http://127.0.0.1:8001','-o',out.name,'-r',str(seed)]
      subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
      states=[]
      for line in open(out.name):
        if line.strip() and '"board"' in line and '"you"' in line:
          states.append(json.loads(line))
      os.unlink(out.name)
      if not states:
        ties+=1; continue
      last=states[-1]
      names=[s['name'] for s in last['board']['snakes']]
      if 'gpt-5-5' in names and 'altersaddle__untimely-neglected-wearable' not in names: wins+=1
      elif 'altersaddle__untimely-neglected-wearable' in names and 'gpt-5-5' not in names: losses+=1
      else: ties+=1
    print(seed, wins, losses, ties, flush=True)
finally:
  for p in (p1,p2):
    try: p.terminate(); p.wait(timeout=2)
    except Exception: p.kill()
print('RESULT',wins,losses,ties)
