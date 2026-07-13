import sys
sys.path.insert(0, '/workspace')
import sim_test as S
me = S.load(sys.argv[1])
opp = S.load('/workspace/opp_gigantic_george.py')
N = int(sys.argv[2]) if len(sys.argv)>2 else 100
w=l=d=0
losses=[]
for i in range(N):
    if i%2==0:
        r,_ = S.run_game(me, opp, i*7+1)
        res = 'W' if r=="A" else ('L' if r=="B" else 'D')
    else:
        r,_ = S.run_game(opp, me, i*7+1)
        res = 'W' if r=="B" else ('L' if r=="A" else 'D')
    if res=='W': w+=1
    elif res=='L': l+=1; losses.append(i)
    else: d+=1
print(f"{sys.argv[1]} vs gigantic: wins={w} losses={l} draws={d} (N={N})")
if losses: print("loss seeds:", losses[:20])
