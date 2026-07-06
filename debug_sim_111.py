import json

filepath = "/logs/rounds/2/sim_111.jsonl"
with open(filepath) as f:
    for line in f:
        if not line.strip():
            continue
        data = json.loads(line)
        if "turn" in data and data["turn"] in [15, 16, 17]:
            print(f"Turn {data['turn']}")
            print("Snakes:")
            for s in data["board"]["snakes"]:
                print(f"  {s['name']}: head {s['head']}, body {s['body']}")
