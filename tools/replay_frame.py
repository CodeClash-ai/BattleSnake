#!/usr/bin/env python3
"""Reusable helper for replaying a real sim_*.jsonl frame through main.move().

Suggested by at least 6 previous agent sessions in README_agent.md (search
"replay_frame.py" there) -- this exact snippet has been hand-rewritten from
scratch many times across sessions. Finally saved as a standalone tool.

Usage:
    python3 tools/replay_frame.py <sim_file.jsonl> [--turn N] [--last] \
        [--name SNAKE_NAME] [--legal-only]

Examples:
    # Show move() decision + legal-move count for OUR snake's very last
    # logged frame (useful first check: "were we already dead by then?"):
    python3 tools/replay_frame.py /logs/rounds/0/sim_125.jsonl --last

    # Replay a specific turn:
    python3 tools/replay_frame.py /logs/rounds/0/sim_125.jsonl --turn 96

    # Dump per-candidate diagnostics (space/reached_tail/danger_h2h-ish)
    # without needing to hand-edit main.py -- reimplements just enough of
    # the early scoring-loop setup to give useful numbers:
    python3 tools/replay_frame.py /logs/rounds/0/sim_125.jsonl --turn 96 --diag
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main as M


def load_our_frames(path, name):
    frames = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "board" not in obj:
                continue
            if any(s.get("name") == name for s in obj["board"]["snakes"]):
                frames.append(obj)
    return frames


def legal_moves(frame, you):
    board = frame["board"]
    blocked, heads, lengths, tails = M._occupied_cells(board, you["id"])
    head = (you["body"][0]["x"], you["body"][0]["y"])
    out = []
    for name, (dx, dy) in M.DIRS.items():
        npt = (head[0] + dx, head[1] + dy)
        if M._in_bounds(npt, board["width"], board["height"]) and npt not in blocked:
            out.append(name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("simfile")
    ap.add_argument("--turn", type=int, default=None)
    ap.add_argument("--last", action="store_true")
    ap.add_argument("--name", default="sonnet-5")
    ap.add_argument("--diag", action="store_true", help="dump per-candidate space/reached_tail")
    args = ap.parse_args()

    frames = load_our_frames(args.simfile, args.name)
    if not frames:
        print(f"No frames found containing a snake named {args.name!r} in {args.simfile}")
        sys.exit(1)

    if args.turn is not None:
        fr = next((f for f in frames if f["turn"] == args.turn), None)
        if fr is None:
            avail = [f["turn"] for f in frames]
            print(f"Turn {args.turn} not logged for us. Available turns (first/last 10): "
                  f"{avail[:10]} ... {avail[-10:]}")
            sys.exit(1)
    else:
        fr = frames[-1]  # --last or default

    you = next(s for s in fr["board"]["snakes"] if s["name"] == args.name)
    state = {
        "game": {"id": "replay-debug", "timeout": 500},
        "turn": fr["turn"],
        "board": fr["board"],
        "you": you,
    }

    lm = legal_moves(fr, you)
    print(f"turn={fr['turn']} head={(you['body'][0]['x'], you['body'][0]['y'])} "
          f"my_len={len(you['body'])} health={you.get('health')} legal_moves={lm}")
    for s in fr["board"]["snakes"]:
        if s["name"] != args.name:
            print(f"  opp={s['name']} len={len(s['body'])} health={s.get('health')} "
                  f"head={(s['body'][0]['x'], s['body'][0]['y'])}")

    if not lm:
        print("*** Already had ZERO legal moves at this frame -- the fatal decision "
              "happened earlier and isn't recoverable from this exact frame alone. "
              "Try an earlier --turn if this sim file logs one for us. ***")

    decision = M.move(state)
    print("move() decision:", decision)

    if args.diag:
        board = fr["board"]
        width, height = board["width"], board["height"]
        blocked, heads, lengths, tails = M._occupied_cells(board, you["id"])
        head = (you["body"][0]["x"], you["body"][0]["y"])
        my_tail = tails.get(you["id"])
        food = board.get("food", [])
        food_cells = {(f["x"], f["y"]) for f in food}
        print("--- per-candidate diagnostics ---")
        for name, (dx, dy) in M.DIRS.items():
            npt = (head[0] + dx, head[1] + dy)
            if not M._in_bounds(npt, width, height) or npt in blocked:
                print(f"{name:6s} {npt} BLOCKED/OOB")
                continue
            will_eat = npt in food_cells
            eff_blocked = blocked | {my_tail} if (will_eat and my_tail and my_tail not in blocked) else blocked
            space, reached_tail = M._flood_fill(npt, eff_blocked, width, height, target=my_tail)
            print(f"{name:6s} {npt} space={space} reached_tail={reached_tail} will_eat={will_eat}")


if __name__ == "__main__":
    main()
