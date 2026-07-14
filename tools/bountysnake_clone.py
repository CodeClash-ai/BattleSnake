#!/usr/bin/env python3
"""Local clone-ish opponent for rdbrck__bountysnake2018.

Profile from logs: balanced but strongly vertical food/space snake. This
server is intentionally simple/offline for smoke tests only; it greedily
routes to food with flood-fill and vertical tie-breaks.
"""
import sys
from flask import Flask, jsonify, request

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8011
app = Flask(__name__)
MOVES = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}

def pt(o): return (o["x"], o["y"])
def add(a,d): return (a[0]+d[0], a[1]+d[1])
def inside(p,w,h): return 0 <= p[0] < w and 0 <= p[1] < h
def md(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])

def flood(st, blocked, w, h):
    if st in blocked or not inside(st,w,h): return 0
    q=[st]; seen={st}; qi=0
    while qi < len(q):
        p=q[qi]; qi+=1
        for d in MOVES.values():
            n=add(p,d)
            if inside(n,w,h) and n not in blocked and n not in seen:
                seen.add(n); q.append(n)
    return len(seen)

def choose(gs):
    b,you=gs['board'],gs['you']; w,h=b['width'],b['height']
    body=[pt(x) for x in you['body']]; head=body[0]; neck=body[1] if len(body)>1 else None
    food=[pt(f) for f in b.get('food',[])]
    occupied=set()
    for s in b.get('snakes',[]):
        sb=[pt(x) for x in s.get('body',[])]
        for c in sb[:-1]: occupied.add(c)
    best=(-10**9,'up')
    for name,d in MOVES.items():
        n=add(head,d)
        if not inside(n,w,h) or n in occupied or (n==neck and len(set(body[:3]))>1):
            continue
        sim=set(occupied); sim.add(head)
        area=flood(n,sim,w,h)
        fd=min([md(n,f) for f in food], default=8)
        vertical = 1.8 if name in ('up','down') else 0
        center = -0.6*(abs(n[0]-(w-1)/2)+abs(n[1]-(h-1)/2))
        edge = -3 if (n[0] in (0,w-1) or n[1] in (0,h-1)) else 0
        score=area*1.2 - fd*9 + vertical + center + edge
        if n in food: score += 35
        if score>best[0]: best=(score,name)
    return best[1]

@app.get('/')
def info(): return jsonify({'apiversion':'1','author':'bountyclone','color':'#5DD284','head':'bendr','tail':'fat-rattle'})
@app.post('/start')
def start(): return jsonify({})
@app.post('/end')
def end(): return jsonify({})
@app.post('/move')
def move(): return jsonify({'move': choose(request.get_json())})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
