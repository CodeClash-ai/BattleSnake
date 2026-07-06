import json

with open("/logs/rounds/3/sim_0.jsonl") as f:
    for line in f:
        data = json.loads(line)
        if "turn" in data and data["turn"] is not None:
            # Let's see how many snakes and who died when
            snakes = data["board"]["snakes"]
            print(f"Turn {data['turn']}: {len(snakes)} snakes alive.")
            for s in snakes:
                print(f"  Snake: {s['name']}, Health: {s['health']}, Length: {s['length']}, Head: {s['head']}")
