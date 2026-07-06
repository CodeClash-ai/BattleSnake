import json

filepath = "/logs/rounds/1/sim_244.jsonl"
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if data.get("turn") in [64, 65, 66]:
                print(f"\nTurn {data.get('turn')}:")
                for s in data["board"]["snakes"]:
                    print(f"  Snake: {s['name']}")
                    print(f"    Body: {[(seg['x'], seg['y']) for seg in s['body']]}")
                    print(f"    Health: {s['health']}")
