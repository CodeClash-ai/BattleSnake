import os
import json

rounds_dir = "/logs/rounds"
with open(os.path.join(rounds_dir, "0", "sim_101.jsonl")) as f:
    lines = [json.loads(line) for line in f if line.strip()]

# Find when gemini-3-5-flash was present but then not present
for i in range(len(lines)):
    data = lines[i]
    if "board" in data:
        snakes = data["board"]["snakes"]
        names = [s["name"] for s in snakes]
        print(f"Turn {data['turn']}: {names}")
