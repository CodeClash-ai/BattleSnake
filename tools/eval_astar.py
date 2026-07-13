import os, sys, json, subprocess, tempfile
N=int(os.environ.get('N','20'))
ROOT=os.path.dirname(os.path.dirname(__file__))
# Use battlesnake CLI binary present in game/battlesnake
wins=losses=ties=0
turns=[]
for seed in range(N):
    out=tempfile.NamedTemporaryFile(delete=False,suffix='.jsonl'); out.close()
    cmd=[os.path.join(ROOT,'game','battlesnake'),'play','-W','11','-H','11','-n','gpt-5-5','-u','http://127.0.0.1:8000','-n','OliverMKing__astar-snake','-u','http://127.0.0.1:8001','-o',out.name,'-r',str(seed)]
    # start servers
    p1=subprocess.Popen([sys.executable, os.path.join(ROOT,'main.py')], env=dict(os.environ, PORT='8000'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p2=subprocess.Popen([sys.executable, os.path.join(ROOT,'tools','astar_snake_opponent.py')], env=dict(os.environ, PORT='8001'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        import time; time.sleep(0.15)
        r=subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        winner=None; turn=0
        for line in open(out.name):
            obj=json.loads(line)
            if 'turn' in obj: turn=obj['turn']
            if 'winnerName' in obj: winner=obj.get('winnerName')
        turns.append(turn)
        if winner=='gpt-5-5': wins+=1
        elif winner=='OliverMKing__astar-snake': losses+=1
        else: ties+=1
        print(seed,winner,turn)
    except Exception as e:
        print(seed,'ERR',e)
    finally:
        p1.kill(); p2.kill()
        try: os.unlink(out.name)
        except OSError: pass
print({'wins':wins,'losses':losses,'ties':ties,'avg_turn':sum(turns)/len(turns) if turns else 0})
