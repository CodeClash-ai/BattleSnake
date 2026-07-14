import json

with open("/logs/rounds/0/sim_10.jsonl") as f:
    lines = [json.loads(line) for line in f if line.strip()]

board_lines = [line for line in lines if "board" in line]
for line in board_lines[-5:]:
    print("Turn:", line["turn"])
    for s in line["board"]["snakes"]:
        print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']} body={s['body'][:4]}")
