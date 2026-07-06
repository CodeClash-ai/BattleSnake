import json

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

for turn_idx in [109, 110, 111]:
    data = json.loads(lines[turn_idx])
    print(f"\n--- Turn {data['turn']} ---")
    for s in data["board"]["snakes"]:
        print(s["name"], "head:", s["head"], "body:", [(b['x'], b['y']) for b in s['body']])
