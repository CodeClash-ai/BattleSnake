#!/usr/bin/env python3
"""Summarize games not won by our snake, with last known positions.

Usage: python3 tools/analyze_losses.py /logs/rounds/0 [our-name]
"""
import glob, json, os, sys
root = sys.argv[1] if len(sys.argv) > 1 else "/logs/rounds/0"
our = sys.argv[2] if len(sys.argv) > 2 else "gpt-5-5"
for path in sorted(glob.glob(os.path.join(root, "sim_*.jsonl"))):
    states = []
    final = None
    for line in open(path):
        obj = json.loads(line)
        if "turn" in obj:
            states.append(obj)
        elif "winnerName" in obj:
            final = obj
    if not final or final.get("winnerName") == our:
        continue
    last_with_us = None
    for st in states:
        if any(s.get("name") == our for s in st.get("board", {}).get("snakes", [])):
            last_with_us = st
    print(f"{os.path.basename(path)} winner={final.get('winnerName')} draw={final.get('isDraw')} final_turn={states[-1]['turn'] if states else '?'}")
    if last_with_us:
        print(f"  last_us_turn={last_with_us['turn']} food={[ (f['x'], f['y']) for f in last_with_us['board'].get('food', []) ]}")
        for s in last_with_us["board"].get("snakes", []):
            head = s.get("head", {})
            print(f"  {s.get('name')} hp={s.get('health')} len={s.get('length')} head={(head.get('x'), head.get('y'))} tail={(s.get('body') or [{}])[-1]}")
