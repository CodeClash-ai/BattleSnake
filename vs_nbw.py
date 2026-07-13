import sys
sys.path.insert(0, '/workspace')
import sim_test as S
me = S.load(sys.argv[1])
opp = S.load('/workspace/opp_nbw_ruby.py')
N = int(sys.argv[2]) if len(sys.argv)>2 else 100
w=l=d=0
for i in range(N):
    if i%2==0:
        r,_ = S.run_game(me, opp, i*7+1)
        if r=="A": w+=1
        elif r=="B": l+=1
        else: d+=1
    else:
        r,_ = S.run_game(opp, me, i*7+1)
        if r=="B": w+=1
        elif r=="A": l+=1
        else: d+=1
print(f"{sys.argv[1]} vs opp: wins={w} losses={l} draws={d} (N={N})")
