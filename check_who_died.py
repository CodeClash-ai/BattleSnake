import json

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    data = json.loads(line)
    if "board" in data:
        snakes = data["board"]["snakes"]
        # print first few turns and last few turns
        if idx < 3 or idx >= len(lines) - 5:
            print(f"Turn {data['turn']}: {[s['name'] for s in snakes]}")
