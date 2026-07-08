# Naive pambrose SimpleSnake opponent for local testing.
import sys, os
def info():
    return {"apiversion":"1","author":"pam","color":"#ff00ff","head":"beluga","tail":"bolt"}
def start(gs): return None
def end(gs): return None
def _man(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])
def _center(w,h):
    cx=(w//2 if w%2==0 else (w+1)//2)-1
    cy=(h//2 if h%2==0 else (h+1)//2)-1
    return (cx,cy)
def _moveto(head,t):
    hx,hy=head; tx,ty=t
    if hx>tx: return "left"
    if hx<tx: return "right"
    if hy>ty: return "down"
    return "up"
def move(gs):
    try:
        b=gs["board"]; w,h=b["width"],b["height"]
        hs=gs["you"]["body"][0]; head=(hs["x"],hs["y"])
        food=b.get("food",[])
        if food:
            target=None; best=-1
            for f in food:
                fp=(f["x"],f["y"]); d=_man(head,fp)
                if d>best: best=d; target=fp
        else:
            target=_center(w,h)
        return {"move":_moveto(head,target)}
    except Exception:
        return {"move":"up"}
if __name__=="__main__":
    sys.path.insert(0,"/workspace")
    from server import run_server
    run_server({"info":info,"start":start,"move":move,"end":end})
