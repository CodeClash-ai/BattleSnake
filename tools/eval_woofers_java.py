import subprocess, time, os, sys, json, tempfile
ROOT=os.path.dirname(os.path.dirname(__file__))
p1=subprocess.Popen([sys.executable, os.path.join(ROOT,'main.py')], env=dict(os.environ, PORT='8000'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
p2=subprocess.Popen([sys.executable, os.path.join(ROOT,'tools','woofers_java_opponent.py')], env=dict(os.environ, PORT='8001'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
wins=losses=ties=0
N=int(os.environ.get('N','20'))
try:
  for seed in range(N):
    with tempfile.NamedTemporaryFile(delete=False,suffix='.jsonl') as out:
      cmd=[os.path.join(ROOT,'game','battlesnake'),'play','-W','11','-H','11','-n','gpt-5-5','-u','http://127.0.0.1:8000','-n','woofers__woofers-java','-u','http://127.0.0.1:8001','-o',out.name,'-r',str(seed)]
      subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
      states=[json.loads(line) for line in open(out.name) if line.strip() and '"turn"' in line]
      os.unlink(out.name)
      if not states:
        ties+=1; continue
      names=[s['name'] for s in states[-1]['board']['snakes']]
      if 'gpt-5-5' in names and 'woofers__woofers-java' not in names: wins+=1
      elif 'woofers__woofers-java' in names and 'gpt-5-5' not in names: losses+=1
      else: ties+=1
    print(seed, wins, losses, ties, flush=True)
finally:
  for p in (p1,p2):
    try: p.terminate(); p.wait(timeout=2)
    except Exception: p.kill()
print('RESULT',wins,losses,ties)
