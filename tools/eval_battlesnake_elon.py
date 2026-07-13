import os, sys, json, subprocess, tempfile, time
N=int(os.environ.get('N','50'))
ROOT=os.path.dirname(os.path.dirname(__file__))
wins=losses=ties=0; turns=[]
for seed in range(N):
    out=tempfile.NamedTemporaryFile(delete=False,suffix='.jsonl'); out.close()
    p1=subprocess.Popen([sys.executable, os.path.join(ROOT,'main.py')], env=dict(os.environ, PORT='8000'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p2=subprocess.Popen([sys.executable, os.path.join(ROOT,'tools','battlesnake_elon_opponent.py')], env=dict(os.environ, PORT='8001'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(0.12)
        cmd=[os.path.join(ROOT,'game','battlesnake'),'play','-W','11','-H','11','-n','gpt-5-5','-u','http://127.0.0.1:8000','-n','jackisherwood__battlesnake-elon','-u','http://127.0.0.1:8001','-o',out.name,'-r',str(seed)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
        winner=None; turn=0
        for line in open(out.name):
            obj=json.loads(line)
            if 'turn' in obj: turn=obj['turn']
            if 'winnerName' in obj: winner=obj.get('winnerName')
        turns.append(turn)
        if winner=='gpt-5-5': wins+=1
        elif winner=='jackisherwood__battlesnake-elon': losses+=1
        else: ties+=1
        print(seed,winner,turn, flush=True)
    except Exception as e:
        print(seed,'ERR',e, flush=True)
    finally:
        p1.kill(); p2.kill()
        try: p1.wait(timeout=1); p2.wait(timeout=1)
        except Exception: pass
        try: os.unlink(out.name)
        except OSError: pass
print({'wins':wins,'losses':losses,'ties':ties,'avg_turn':sum(turns)/len(turns) if turns else 0})
