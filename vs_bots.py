import sys
sys.argv=['x']
import importlib.util
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
sys.path.insert(0,'/workspace')
import sim_test as S
new=load('/workspace/main.py','new')
old=load('/workspace/main_r0_ccsnake_backup.py','old')
aw=bw=dr=0
N=30
for i in range(N):
    # alternate who is A
    if i%2==0:
        r,_=S.run_game(new,old,i)
        if r=='A': aw+=1
        elif r=='B': bw+=1
        else: dr+=1
    else:
        r,_=S.run_game(old,new,i)
        if r=='B': aw+=1
        elif r=='A': bw+=1
        else: dr+=1
print(f"new wins {aw}, old wins {bw}, draws {dr} (of {N})")
