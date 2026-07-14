import json
with open("/logs/rounds/1/sim_131.jsonl") as f:
    lines = f.readlines()
data = json.loads(lines[-3])
print("Spenca head:", data["board"]["snakes"][0]["head"])
print("Spenca body:", [ (p['x'], p['y']) for p in data["board"]["snakes"][0]['body'] ])
