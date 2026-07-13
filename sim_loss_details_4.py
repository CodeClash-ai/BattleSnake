import json

with open("/logs/rounds/1/sim_146.jsonl") as f:
    lines = f.readlines()

for line in lines[-10:]:
    try:
        data = json.loads(line)
        if "turn" in data:
            print("Turn:", data["turn"])
            for s in data["board"]["snakes"]:
                print(f"  {s['name']}: Head: {s['head']}, Len: {s['length']}, Health: {s['health']}")
    except Exception as e:
        print("Meta:", line.strip())
