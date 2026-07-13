import sys
sys.path.insert(0,'/workspace')
import sim_test as S
new=S.load('/workspace/main.py')
old=S.load('/workspace/main_prev_committed_backup.py')
opp=S.load('/workspace/opp_beames.py')
N=int(sys.argv[1]); off=int(sys.argv[2]) if len(sys.argv)>2 else 1
def bench(bot):
    w=l=d=0
    for i in range(N):
        if i%2==0:
            r,_=S.run_game(bot,opp,i*13+off)
            if r=="A":w+=1
            elif r=="B":l+=1
            else:d+=1
        else:
            r,_=S.run_game(opp,bot,i*13+off)
            if r=="B":w+=1
            elif r=="A":l+=1
            else:d+=1
    return w,l,d
print("NEW",bench(new))
print("OLD",bench(old))
