import time,json,random,importlib.util
spec=importlib.util.spec_from_file_location("m","/workspace/main.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
random.seed(1)
def body(hx,hy,n):
    b=[{"x":hx,"y":hy}]
    for i in range(1,n): b.append({"x":max(0,min(10,hx-i%3)),"y":max(0,min(10,hy-i//3))})
    return b
us=body(5,5,20); op=body(2,8,18)
food=[{"x":random.randint(0,10),"y":random.randint(0,10)} for _ in range(6)]
st={"turn":100,"board":{"width":11,"height":11,"food":food,
    "snakes":[{"id":"u","name":"opus-4-8","health":90,"body":us,"head":us[0],"length":20},
              {"id":"o","name":"op","health":80,"body":op,"head":op[0],"length":18}]},
    "you":{"id":"u","name":"opus-4-8","health":90,"body":us,"head":us[0],"length":20}}
ts=[]
for _ in range(50):
    t=time.time(); m.move(st); ts.append((time.time()-t)*1000)
print(f"avg {sum(ts)/len(ts):.2f}ms max {max(ts):.2f}ms (timeout 500ms)")
