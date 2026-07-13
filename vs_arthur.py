import sys
sys.argv=['x']
import importlib.util
sys.path.insert(0,'/workspace')
import sim_test as S
def load(p,n):
    spec=importlib.util.spec_from_file_location(n,p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
bot=load(sys.argv[1] if len(sys.argv)>1 else '/workspace/main.py','bot') if False else None
botfile=sys.argv[1] if len(sys.argv)>1 else 'main.py'
N=int(sys.argv[2]) if len(sys.argv)>2 else 100
me=load('/workspace/'+botfile,'me')
opp=load('/workspace/opp_amphibious_arthur.py','opp')
aw=bw=dr=0
for i in range(N):
    if i%2==0:
        r,_=S.run_game(me,opp,i)
        if r=='A':aw+=1
        elif r=='B':bw+=1
        else:dr+=1
    else:
        r,_=S.run_game(opp,me,i)
        if r=='B':aw+=1
        elif r=='A':bw+=1
        else:dr+=1
print(f"{botfile}: me {aw}, opp {bw}, draws {dr} (of {N})")
