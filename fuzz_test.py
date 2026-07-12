import random, main, time
random.seed(7)
crashes=illegal=0; maxt=0
W=H=11
for i in range(3000):
    n=random.randint(1,2)
    snakes=[]
    occ=set()
    for j in range(n):
        L=random.randint(1,8)
        hx,hy=random.randint(0,10),random.randint(0,10)
        body=[]
        x,y=hx,hy
        for k in range(L):
            body.append({"x":x,"y":y})
            occ.add((x,y))
            x=max(0,min(10,x+random.choice([-1,0,1])))
            y=max(0,min(10,y+random.choice([-1,0,1])))
        snakes.append({"id":str(j),"name":"s"+str(j),"health":random.randint(1,100),
                       "body":body,"head":body[0],"length":L})
    food=[{"x":random.randint(0,10),"y":random.randint(0,10)} for _ in range(random.randint(0,4))]
    gs={"board":{"width":W,"height":H,"snakes":snakes,"food":food},
        "you":snakes[0],"turn":i}
    t=time.time()
    try:
        r=main.move(gs)
        dt=time.time()-t; maxt=max(maxt,dt)
        d=r["move"]
        if d not in ("up","down","left","right"): illegal+=1
    except Exception as e:
        crashes+=1
        if crashes<3: print("crash",e)
print(f"crashes={crashes} illegal={illegal} maxt_ms={maxt*1000:.2f}")
