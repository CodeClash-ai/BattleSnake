import json
with open("/logs/rounds/1/sim_5.jsonl") as f:
    lines = [json.loads(line) for line in f if line.strip()]

for line in lines[-4:-1]:
    print(f"Turn {line.get('turn')}")
    for s in line["board"]["snakes"]:
        print(f"  {s['name']} (health: {s['health']}, head: {s['head']}, len: {s['length']})")
