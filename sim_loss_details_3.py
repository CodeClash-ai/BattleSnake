import json

log_path = "/logs/rounds/0/sim_100.jsonl"
with open(log_path, 'r') as f:
    lines = f.readlines()

print(f"Total turns: {len(lines)}")
# Let's inspect turn 205 and 206
for turn_idx in range(len(lines) - 4, len(lines)):
    data = json.loads(lines[turn_idx])
    turn = data.get("turn")
    print(f"--- Turn {turn} ---")
    if "board" in data:
        for s in data["board"]["snakes"]:
            print(f"  Snake {s['name']}: Head: ({s['head']['x']},{s['head']['y']}), Len: {s['length']}, Health: {s['health']}")
            print(f"    Body: {s['body']}")
    else:
        print("  Game ended metadata:", data)
