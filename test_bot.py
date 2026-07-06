import json, main

# Test on all recorded game states from logs to ensure no crashes and legal moves.
import glob
count = 0
crashes = 0
illegal = 0
for path in glob.glob("/logs/rounds/0/sim_*.jsonl"):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if "you" not in obj or "board" not in obj:
                continue
            # Only test states where 'you' is our bot
            gs = obj
            you = gs["you"]
            board = gs["board"]
            w, h = board["width"], board["height"]
            head = you["body"][0]
            count += 1
            try:
                res = main.move(gs)
                mv = res["move"]
                dx, dy = main.DIRS[mv]
                nx, ny = head["x"]+dx, head["y"]+dy
                # legal = in bounds
                if not (0 <= nx < w and 0 <= ny < h):
                    illegal += 1
            except Exception as e:
                crashes += 1
                print("CRASH", e)
print(f"tested={count} crashes={crashes} out_of_bounds={illegal}")
