import json

with open("/logs/rounds/0/sim_45.jsonl") as f:
    lines = [json.loads(line) for line in f if line.strip()]

board_lines = [line for line in lines if "board" in line]
print("Total board turns:", len(board_lines))
for line in board_lines[200:210]:
    print(f"Turn {line['turn']}:")
    for s in line["board"]["snakes"]:
        print(f"  {s['name']}: head={s['head']} len={s['length']} health={s['health']}")
