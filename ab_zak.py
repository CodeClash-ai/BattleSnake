import sys
sys.path.insert(0, '/workspace')
import sim_test as S
new = S.load(sys.argv[1])   # new bot file
old = S.load(sys.argv[2])   # old bot file
opp = S.load('/workspace/opp_zakwht.py')
N = int(sys.argv[3]) if len(sys.argv)>3 else 12
off = int(sys.argv[4]) if len(sys.argv)>4 else 1
def bench(bot):
    w=l=d=0
    for i in range(N):
        seed = i*13+off
        if i%2==0:
            r,_ = S.run_game(bot, opp, seed)
            if r=="A": w+=1
            elif r=="B": l+=1
            else: d+=1
        else:
            r,_ = S.run_game(opp, bot, seed)
            if r=="B": w+=1
            elif r=="A": l+=1
            else: d+=1
    return w,l,d
nw = bench(new)
ow = bench(old)
print(f"NEW {sys.argv[1]}: W={nw[0]} L={nw[1]} D={nw[2]}")
print(f"OLD {sys.argv[2]}: W={ow[0]} L={ow[1]} D={ow[2]}")
