import json

# Let's read round 0, sim_128.jsonl turn 108, 109, 110, 111
file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

print(f"Total turns in sim_128: {len(lines)}")
for i in range(max(0, len(lines)-5), len(lines)):
    data = json.loads(lines[i])
    turn = data.get("turn")
    print(f"\n--- Turn {turn} ---")
    you = data.get("you", {})
    print("You head:", you.get("head"), "length:", len(you.get("body", [])), "health:", you.get("health"))
    print("You body:", [ (b['x'], b['y']) for b in you.get("body", []) ])
    for snake in data.get("board", {}).get("snakes", []):
        if snake["id"] != you["id"]:
            print("Opp head:", snake.get("head"), "length:", len(snake.get("body", [])), "health:", snake.get("health"))
            print("Opp body:", [ (b['x'], b['y']) for b in snake.get("body", []) ])
