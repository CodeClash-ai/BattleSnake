import os, sys, json, subprocess, tempfile, time
N=int(os.environ.get('N','50'))
ROOT=os.path.dirname(os.path.dirname(__file__))
wins=losses=ties=0; turns=[]
p1=subprocess.Popen([sys.executable, os.path.join(ROOT,'main.py')], env=dict(os.environ, PORT='8000'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
p2=subprocess.Popen([sys.executable, os.path.join(ROOT,'tools','tyrelh_python_opponent.py')], env=dict(os.environ, PORT='8001'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
try:
  for seed in range(N):
    out=tempfile.NamedTemporaryFile(delete=False,suffix='.jsonl'); out.close()
    try:
      cmd=[os.path.join(ROOT,'game','battlesnake'),'play','-W','11','-H','11','-n','tyrelh__tyrelh-python','-u','http://127.0.0.1:8001','-n','gpt-5-5','-u','http://127.0.0.1:8000','-o',out.name,'-r',str(seed)]
      subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
      winner=None; turn=0; alive=[]
      for line in open(out.name):
        obj=json.loads(line)
        if 'turn' in obj:
          turn=obj['turn']; alive=[s['name'] for s in obj['board']['snakes']]
        if 'winnerName' in obj: winner=obj.get('winnerName')
      turns.append(turn)
      if winner=='gpt-5-5' or ('gpt-5-5' in alive and 'tyrelh__tyrelh-python' not in alive): wins+=1; res='win'
      elif winner=='tyrelh__tyrelh-python' or ('tyrelh__tyrelh-python' in alive and 'gpt-5-5' not in alive): losses+=1; res='loss'
      else: ties+=1; res='tie'
      print(seed,res,winner,turn, flush=True)
    finally:
      try: os.unlink(out.name)
      except OSError: pass
finally:
  p1.kill(); p2.kill()
  try: p1.wait(timeout=1); p2.wait(timeout=1)
  except Exception: pass
print({'wins':wins,'losses':losses,'ties':ties,'avg_turn':sum(turns)/len(turns) if turns else 0})
