import json

filepath = "/logs/rounds/4/sim_219.jsonl"
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if "turn" in data and data["turn"] >= 145:
                print(f"Turn {data['turn']}:")
                for s in data["board"]["snakes"]:
                    print(f"  {s['name']}: head {s['head']}, body {s['body']}")
                if "you" in data and data["you"]:
                    print(f"  You (server view): {data['you']['name']}, head {data['you']['head']}")
