"""Quick local batch runner against MorganConrad__sisiutl reference port.
Usage: N=50 python tools/eval_sisiutl.py
"""
import json, os, subprocess, time
N=int(os.environ.get('N','50'))
me=subprocess.Popen(['python3','main.py'], cwd='/workspace', env=dict(os.environ, PORT='8000'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
opp=subprocess.Popen(['python3','tools/sisiutl_opponent.py'], cwd='/workspace', env=dict(os.environ, PORT='8001'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
try:
    res={'win':0,'loss':0,'tie':0}; turns=[]
    for seed in range(N):
        out=f'/tmp/sisiutl_{seed}.jsonl'
        try:
            subprocess.run(['./game/battlesnake','play','-W','11','-H','11','-n','gpt-5-5','-u','http://127.0.0.1:8000','-n','MorganConrad__sisiutl','-u','http://127.0.0.1:8001','-r',str(seed),'-o',out], cwd='/workspace', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except subprocess.TimeoutExpired:
            continue
        last=None
        for line in open(out):
            if line.strip(): last=json.loads(line)
        if not last: continue
        if 'board' not in last:
            states=[json.loads(line) for line in open(out) if '"board"' in line]
            if not states: continue
            last=states[-1]
        alive=[s['name'] for s in last['board']['snakes']]
        if 'gpt-5-5' in alive and 'MorganConrad__sisiutl' not in alive: r='win'
        elif 'MorganConrad__sisiutl' in alive and 'gpt-5-5' not in alive: r='loss'
        elif 'MorganConrad__sisiutl' not in alive and 'gpt-5-5' not in alive: r='tie'
        else: r='tie'
        res[r]+=1; turns.append(last.get('turn',0))
    print(res, 'avgturn', (sum(turns)/len(turns) if turns else 0), 'n', len(turns))
finally:
    me.terminate(); opp.terminate()
