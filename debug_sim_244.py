import json

filepath = "/logs/rounds/1/sim_244.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

for turn_data in turns:
    # Some lines might be moves/actions or results
    if "turn" in turn_data:
        turn = turn_data.get("turn")
        if turn >= 58:
            print(f"\n--- Turn {turn} ---")
            for s in turn_data["board"]["snakes"]:
                print(f"Snake: {s['name']}, Head: ({s['body'][0]['x']}, {s['body'][0]['y']}), Length: {len(s['body'])}")
