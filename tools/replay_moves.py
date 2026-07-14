#!/usr/bin/env python3
"""Replay logged game states through main.move to check for exceptions.

Usage: python3 tools/replay_moves.py /logs/rounds/1
This does not know the historical moves; it just verifies the current bot returns a
valid direction for every logged state where our snake is alive.
"""
import glob
import json
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/logs/rounds/1"
VALID = {"up", "down", "left", "right"}

# Import after constants so syntax/import errors are reported directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main  # noqa: E402

checked = 0
bad = []
for path in sorted(glob.glob(os.path.join(ROOT, "sim_*.jsonl"))):
    if os.path.getsize(path) == 0:
        continue
    with open(path) as fh:
        for line_no, line in enumerate(fh, 1):
            obj = json.loads(line)
            if "turn" not in obj or "you" not in obj:
                continue
            if obj["you"].get("name") != "gpt-5-5":
                continue
            mv = main.move(obj)
            checked += 1
            if not isinstance(mv, dict) or mv.get("move") not in VALID:
                bad.append((path, line_no, mv))

print(f"checked_states={checked} bad={len(bad)}")
for item in bad[:10]:
    print(item)
sys.exit(1 if bad else 0)
