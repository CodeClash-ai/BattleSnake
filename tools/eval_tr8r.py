"""Local batch eval against copied noahspriggs TR-8R opponent."""
import json, os, subprocess, sys, tempfile, time
ROOT=os.path.dirname(os.path.dirname(__file__))
N=int(os.environ.get('N','20'))
seed0=int(os.environ.get('SEED','0'))
p1=subprocess.Popen([sys.executable, os.path.join(ROOT,'main.py')], cwd=ROOT, env=dict(os.environ, PORT='8000'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
p2=subprocess.Popen([sys.executable, os.path.join(ROOT,'tools','tr8r_opponent.py')], cwd=ROOT, env=dict(os.environ, PORT='8001'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(0.7)
wins=losses=ties=errs=0
try:
  for i in range(N):
    seed=seed0+i
    with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f: out=f.name
    try:
      cmd=[os.path.join(ROOT,'game','battlesnake'),'play','-W','11','-H','11','-n','gpt-5-5','-u','http://127.0.0.1:8000','-n','noahspriggs__tr-8r','-u','http://127.0.0.1:8001','-o',out,'-r',str(seed)]
      subprocess.run(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
      states=[json.loads(l) for l in open(out) if '"turn"' in l]
      alive={s['name'] for s in states[-1]['board']['snakes']} if states else set()
      if 'gpt-5-5' in alive and 'noahspriggs__tr-8r' not in alive: wins+=1; res='win'
      elif 'noahspriggs__tr-8r' in alive and 'gpt-5-5' not in alive: losses+=1; res='loss'
      elif 'noahspriggs__tr-8r' not in alive and 'gpt-5-5' not in alive: ties+=1; res='tie'
      else: errs+=1; res='err'
      print(seed, res, states[-1]['turn'] if states else '?', 'tot', wins, losses, ties, flush=True)
    except Exception as e:
      errs+=1; print(seed,'err',e, flush=True)
    finally:
      try: os.unlink(out)
      except OSError: pass
finally:
  p1.terminate(); p2.terminate(); p1.wait(timeout=2); p2.wait(timeout=2)
print('FINAL',wins,losses,ties,errs)
