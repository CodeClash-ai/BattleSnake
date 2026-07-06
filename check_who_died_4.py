import json

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

data3 = json.loads(lines[112])
print(f"--- Turn 112 ---")
for s in data3["board"]["snakes"]:
    print(s["name"], "head:", s["head"], "body:", [(b['x'], b['y']) for b in s['body']])
