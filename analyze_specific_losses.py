import os
import json

loss_files = [
    ("0", "sim_104.jsonl"),
    ("0", "sim_15.jsonl"),
    ("0", "sim_42.jsonl"),
    ("1", "sim_122.jsonl"),
    ("1", "sim_134.jsonl"),
    ("1", "sim_190.jsonl"),
    ("1", "sim_198.jsonl"),
    ("1", "sim_26.jsonl")
]

for r, sf in loss_files:
    path = f"/logs/rounds/{r}/{sf}"
    if not os.path.exists(path):
        continue
    with open(path) as f:
        lines = f.readlines()
    if not lines:
        continue
    last_line = lines[-1]
    data = json.loads(last_line)
    turn = data.get("turn")
    snakes = data.get("board", {}).get("snakes", [])
    print(f"\n--- Loss in Round {r} {sf} at turn {turn} ---")
    for s in snakes:
        print(f"Snake: {s['name']}, Length: {s['length']}, Health: {s['health']}, Head: {s['head']}")
    # Print the last 3 turns
    for offset in range(min(len(lines), 4), 0, -1):
        turn_data = json.loads(lines[-offset])
        t = turn_data.get("turn")
        print(f"Turn {t}:")
        for s in turn_data.get("board", {}).get("snakes", []):
            print(f"  {s['name']}: {s['head']} health={s['health']} body={s['body'][:3]}... len={s['length']}")
