#!/usr/bin/env python3
"""Tiny local Battlesnake opponent for smoke tests.

Usage examples:
  python3 tools/simple_opponent.py up 8001
  python3 tools/simple_opponent.py food 8001

Styles: up/down/left/right repeat that direction; food greedily moves toward
nearest food while avoiding immediate walls/body if possible.
"""
import sys
from flask import Flask, jsonify, request

style = sys.argv[1] if len(sys.argv) > 1 else "up"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8001
app = Flask(__name__)
MOVES = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}

def pt(o): return (o["x"], o["y"])
def inside(p, w, h): return 0 <= p[0] < w and 0 <= p[1] < h

def choose_food(gs):
    b, you = gs["board"], gs["you"]
    w, h = b["width"], b["height"]
    head = pt(you["head"])
    neck = pt(you["body"][1]) if len(you.get("body", [])) > 1 else None
    occupied = {pt(seg) for s in b.get("snakes", []) for seg in s.get("body", [])[:-1]}
    food = [pt(f) for f in b.get("food", [])]
    def score(item):
        name, d = item; n = (head[0]+d[0], head[1]+d[1])
        if not inside(n, w, h) or n in occupied or n == neck: return 10**9
        if not food: return abs(n[0]-w//2)+abs(n[1]-h//2)
        return min(abs(n[0]-f[0])+abs(n[1]-f[1]) for f in food)
    return min(MOVES.items(), key=score)[0]

@app.get("/")
def info(): return jsonify({"apiversion":"1","author":"local","color":"#cc2244","head":"default","tail":"default"})
@app.post("/start")
def start(): return jsonify({})
@app.post("/end")
def end(): return jsonify({})
@app.post("/move")
def move():
    return jsonify({"move": choose_food(request.get_json()) if style == "food" else style})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
