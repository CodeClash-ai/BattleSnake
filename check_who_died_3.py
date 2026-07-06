import json

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

data = json.loads(lines[110])
print(f"--- Turn 110 ---")
for s in data["board"]["snakes"]:
    print(s["name"], "head:", s["head"], "body:", [(b['x'], b['y']) for b in s['body']])

data2 = json.loads(lines[111])
print(f"\n--- Turn 111 ---")
for s in data2["board"]["snakes"]:
    print(s["name"], "head:", s["head"], "body:", [(b['x'], b['y']) for b in s['body']])
